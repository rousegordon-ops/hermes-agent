"""Conversation-scoped continuity snapshots for gateway session resets.

The session store supplies the predecessor ID for the same conversation and
persists the resulting text once. Other transcripts are never searched, and
later turns or cache eviction do not change the snapshot.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def collect_recent_exchanges(
    sessions_dir: Path,
    *,
    session_id: str,
    n: int = 5,
    max_chars_per_message: int = 800,
) -> Optional[str]:
    """Read only the explicitly linked predecessor, never other conversations."""
    if n <= 0 or not session_id or Path(session_id).name != session_id:
        return None
    try:
        pairs = _extract_pairs_from_transcript(
            sessions_dir / f"{session_id}.jsonl", max_chars_per_message, n
        )
    except (OSError, ValueError) as exc:
        logger.debug("recent_exchanges: predecessor unavailable: %s", exc)
        return None
    if not pairs:
        return None

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
    path: Path, max_chars: int, limit: int = 5
) -> List[Tuple[str, str]]:
    """Read a JSONL transcript and yield (user_text, assistant_text) pairs in
    chronological order. Assistant turns without final user-facing text
    (pure tool-call turns) are skipped."""
    from collections import deque

    pairs = deque(maxlen=limit)
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
            if not isinstance(msg, dict):
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
            # tool / system messages: ignored
    return list(pairs)


def _extract_text(msg: dict) -> str:
    """Return plain text from a message's content (str or content-parts list)."""
    content = msg.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: List[str] = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text":
                    parts.append(str(part.get("text", "")))
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(parts).strip()
    return ""


def _extract_assistant_text(msg: dict) -> str:
    """Return the final user-facing text from an assistant message. A turn that
    only emits tool_calls (no text) is treated as an intermediate step and
    returns ''. The caller skips empty results, so multi-turn tool sequences
    naturally collapse to the assistant's final text."""
    text = _extract_text(msg)
    if msg.get("tool_calls") and not text:
        return ""
    return text
