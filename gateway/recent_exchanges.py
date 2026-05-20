"""Cross-session "recent exchanges" context for the gateway's system prompt.

When a session is reset (idle/daily, /reset) or the gateway restarts
beyond an inactive window, the agent's `messages` list comes up empty —
the user often experiences this as the assistant having no idea what
they were just talking about. This module reads the N most recent
user/assistant exchange pairs from this source's session lineage and
returns them as a system-prompt block, wrapped with an instruction so
the model treats them as reference material rather than the active
conversation thread.

Source isolation is delegated to ``SessionStore.list_transcripts_for_source``,
which only returns transcripts attached to this source's session_key
lineage. Transcripts from other users/chats are never read.

The pair-stitcher walks each transcript chronologically, pairing every
assistant turn with the most recent preceding user turn. Assistant
turns whose final user-facing text is empty (pure tool-call /
tool_use turns) are skipped — they're internal plumbing rather than
something the user perceived as a reply.

Tool/system messages are ignored entirely so the block contains only
what the user saw and said.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from gateway.session import SessionSource, SessionStore

logger = logging.getLogger(__name__)


def collect_recent_exchanges(
    session_store: "SessionStore",
    source: "SessionSource",
    n: int = 5,
    max_files_to_scan: int = 10,
    max_chars_per_message: int = 800,
) -> Optional[str]:
    """Return a system-prompt block of the most recent N user/assistant
    pairs in this source's session lineage, or ``None`` when no usable
    pairs exist.

    Args:
        session_store: Gateway session store used to resolve the source's
            transcript lineage (current + historical session_ids for the
            same session_key). The store handles source isolation.
        source: Identifies which user/chat to fetch exchanges for.
        n: Number of (user, assistant) pairs to include.
        max_files_to_scan: Cap on transcripts inspected (newest first) so
            disk I/O stays bounded as the lineage accumulates.
        max_chars_per_message: Per-message truncation to keep the block
            from ballooning the system prompt on long messages.
    """
    if n <= 0:
        return None

    try:
        paths = session_store.list_transcripts_for_source(
            source, limit=max_files_to_scan
        )
    except Exception as e:
        logger.debug("recent_exchanges: could not list transcripts: %s", e)
        return None

    if not paths:
        return None

    # paths come back newest-first. Walk them oldest-to-newest while collecting
    # pairs in chronological order; truncate to the last N afterwards.
    pairs: List[Tuple[str, str]] = []
    for fp in reversed(paths):
        try:
            file_pairs = _extract_pairs_from_transcript(fp, max_chars_per_message)
        except Exception as e:
            logger.debug("recent_exchanges: failed to read %s: %s", fp, e)
            continue
        pairs.extend(file_pairs)

    if not pairs:
        return None

    pairs = pairs[-n:]

    lines = [
        "--- Recent prior exchanges (consider only if relevant to the current message) ---",
    ]
    for user_text, assistant_text in pairs:
        lines.append(f"[user]: {user_text}")
        lines.append(f"[assistant]: {assistant_text}")
        lines.append("")
    lines.append("--- End recent exchanges ---")
    return "\n".join(lines)


def _extract_pairs_from_transcript(
    path: Path, max_chars: int
) -> List[Tuple[str, str]]:
    """Read a JSONL transcript and return (user_text, assistant_text) pairs
    in chronological order. Assistant turns without final user-facing text
    (pure tool-call / tool_use turns) collapse so a multi-step tool chain
    pairs once with the assistant's eventual reply."""
    pairs: List[Tuple[str, str]] = []
    pending_user: Optional[str] = None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = msg.get("role")
            if role == "user":
                text = _extract_text(msg)
                if text:
                    pending_user = text[:max_chars]
            elif role == "assistant":
                if pending_user is None:
                    continue
                text = _extract_assistant_text(msg)
                if text:
                    pairs.append((pending_user, text[:max_chars]))
                    pending_user = None
            # tool / system / anything else: ignored
    return pairs


def _extract_text(msg: dict) -> str:
    """Return plain text from a message's content. Handles both the
    OpenAI string form and the Anthropic-style content-blocks list."""
    content = msg.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: List[str] = []
        for part in content:
            if isinstance(part, dict):
                ptype = part.get("type")
                if ptype == "text":
                    parts.append(str(part.get("text", "")))
                elif ptype == "input_text" or ptype == "output_text":
                    # Newer Responses-API shapes
                    parts.append(str(part.get("text", "")))
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(p for p in parts if p).strip()
    return ""


def _extract_assistant_text(msg: dict) -> str:
    """Return the final user-facing text from an assistant message.

    A turn that only emits tool calls (no text) returns ''. The caller
    skips empty results, so multi-turn tool sequences naturally collapse
    to the assistant's eventual user-facing reply.
    """
    text = _extract_text(msg)
    if text:
        return text
    # OpenAI / Codex tool_calls field (no text alongside)
    if msg.get("tool_calls"):
        return ""
    # Anthropic-style: content list with tool_use blocks
    content = msg.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "tool_use":
                return ""
    return ""
