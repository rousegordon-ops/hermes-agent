"""Cross-session recent-exchange injection for the gateway's system prompt.

When a session has just been created or auto-reset (e.g. after the inactivity
timeout), the agent's `messages` array is empty — the agent has no memory of
prior conversations even though those conversations are persisted on disk.

This module reads the N most recent user/assistant exchange pairs from the
gateway's transcript files and formats them as a system-prompt addendum. The
block is wrapped with explicit delimiters and an instruction that the model
should consult them only if relevant to the current message, so the prior
context behaves as reference material rather than the active conversation
thread.

The pair-stitching walks each transcript chronologically, pairing every
assistant turn with the most recent preceding user turn. Tool-call-only
assistant turns (no user-facing text) are skipped — they're internal
plumbing, not part of the conversation as the user experienced it.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def collect_recent_exchanges(
    sessions_dir: Path,
    n: int = 5,
    max_files_to_scan: int = 20,
    max_chars_per_message: int = 800,
) -> Optional[str]:
    """Return a system-prompt block of the most recent N user/assistant pairs
    found in `sessions_dir`'s transcript files, or None when no usable pairs
    exist.

    Args:
        sessions_dir: Directory containing per-session .jsonl transcripts.
        n: Number of (user, assistant) pairs to include.
        max_files_to_scan: Cap on files inspected (newest-mtime first), so
            disk I/O stays bounded as transcripts accumulate.
        max_chars_per_message: Per-message truncation to keep the block from
            ballooning the system prompt when individual messages are large.
    """
    if n <= 0:
        return None

    try:
        files = sorted(
            sessions_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError as e:
        logger.debug("recent_exchanges: failed to list %s: %s", sessions_dir, e)
        return None

    # Walk newest file first. Each file's pairs are appended in chronological
    # order; we prepend newer files so the combined list ends up chronologically
    # ordered (oldest first, newest last). Stop once we have enough.
    pairs: List[Tuple[str, str]] = []
    for fp in files[:max_files_to_scan]:
        if len(pairs) >= n * 2:
            break
        try:
            file_pairs = _extract_pairs_from_transcript(fp, max_chars_per_message)
        except Exception as e:
            logger.debug("recent_exchanges: failed to read %s: %s", fp, e)
            continue
        pairs = file_pairs + pairs

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
    """Read a JSONL transcript and yield (user_text, assistant_text) pairs in
    chronological order. Assistant turns without final user-facing text
    (pure tool-call turns) are skipped."""
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
            # tool / system messages: ignored
    return pairs


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
