"""Tests for cross-session "recent exchanges" injection.

Covers:
  * SessionEntry persists previous_session_ids round-trip
  * Auto-reset paths populate the lineage (get_or_create_session)
  * Manual reset path populates the lineage (reset_session)
  * SessionStore.list_transcripts_for_source walks current + history,
    skips missing files, respects limit
  * SessionStore.list_transcripts_for_source returns [] for unknown sources
    (no cross-source leakage)
  * gateway.recent_exchanges.collect_recent_exchanges pair-stitches
    transcripts, skips tool-only assistant turns, handles Anthropic
    content blocks, truncates oversized messages
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from gateway.config import GatewayConfig, Platform, SessionResetPolicy
from gateway.recent_exchanges import collect_recent_exchanges
from gateway.session import (
    SESSION_LINEAGE_MAX,
    SessionEntry,
    SessionSource,
    SessionStore,
)


# ---------- helpers ----------


def _make_store(tmp_path, idle_minutes: int = 1) -> SessionStore:
    config = GatewayConfig(
        default_reset_policy=SessionResetPolicy(
            mode="idle", idle_minutes=idle_minutes
        ),
    )
    with patch("gateway.session.SessionStore._ensure_loaded"):
        store = SessionStore(sessions_dir=tmp_path, config=config)
    store._db = None
    store._loaded = True
    return store


def _make_source(user_id: str = "u1", chat_id: str = "c1") -> SessionSource:
    return SessionSource(
        platform=Platform.TELEGRAM,
        chat_id=chat_id,
        user_id=user_id,
        chat_type="dm",
    )


def _write_transcript(path: Path, messages: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(m) for m in messages) + "\n")


# ---------- SessionEntry round-trip ----------


class TestSessionEntryLineageRoundTrip:
    def test_previous_session_ids_persist_through_to_from_dict(self):
        entry = SessionEntry(
            session_key="k",
            session_id="current",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            platform=Platform.TELEGRAM,
            chat_type="dm",
            previous_session_ids=["prev1", "prev2", "prev3"],
        )
        restored = SessionEntry.from_dict(entry.to_dict())
        assert restored.previous_session_ids == ["prev1", "prev2", "prev3"]

    def test_missing_previous_session_ids_field_defaults_to_empty(self):
        entry = SessionEntry(
            session_key="k",
            session_id="current",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            platform=Platform.TELEGRAM,
            chat_type="dm",
        )
        data = entry.to_dict()
        # Simulate loading an older sessions.json that predates this field
        data.pop("previous_session_ids", None)
        restored = SessionEntry.from_dict(data)
        assert restored.previous_session_ids == []


# ---------- lineage population on reset ----------


class TestLineagePopulation:
    def test_auto_reset_records_prior_session_id(self, tmp_path):
        store = _make_store(tmp_path, idle_minutes=1)
        source = _make_source()
        first = store.get_or_create_session(source)
        first_id = first.session_id
        # Age the entry past the idle threshold so the next call auto-resets
        store._entries[first.session_key].updated_at = (
            datetime.now() - timedelta(minutes=5)
        )
        second = store.get_or_create_session(source)
        assert second.session_id != first_id
        assert second.was_auto_reset is True
        assert second.previous_session_ids[:1] == [first_id]

    def test_manual_reset_records_prior_session_id(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        first = store.get_or_create_session(source)
        first_id = first.session_id
        reset = store.reset_session(first.session_key)
        assert reset is not None
        assert reset.session_id != first_id
        assert reset.previous_session_ids[:1] == [first_id]

    def test_lineage_carries_across_multiple_resets(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        entry = store.get_or_create_session(source)
        ids_in_order = [entry.session_id]
        for _ in range(3):
            entry = store.reset_session(entry.session_key)
            ids_in_order.append(entry.session_id)
        # Newest reset should see all prior IDs in reverse-chronological order
        assert entry.previous_session_ids[:3] == list(reversed(ids_in_order[:-1]))

    def test_lineage_capped_at_session_lineage_max(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        entry = store.get_or_create_session(source)
        for _ in range(SESSION_LINEAGE_MAX + 5):
            entry = store.reset_session(entry.session_key)
        assert len(entry.previous_session_ids) == SESSION_LINEAGE_MAX


# ---------- list_transcripts_for_source ----------


class TestListTranscriptsForSource:
    def test_returns_current_then_historical_paths(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        first = store.get_or_create_session(source)
        first_path = store.get_transcript_path(first.session_id)
        _write_transcript(first_path, [{"role": "user", "content": "hi"}])
        second = store.reset_session(first.session_key)
        second_path = store.get_transcript_path(second.session_id)
        _write_transcript(second_path, [{"role": "user", "content": "hello"}])

        paths = store.list_transcripts_for_source(source)

        assert paths == [second_path, first_path]

    def test_skips_paths_that_do_not_exist(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        first = store.get_or_create_session(source)
        # Don't write the first transcript — simulate deletion / never-written
        second = store.reset_session(first.session_key)
        second_path = store.get_transcript_path(second.session_id)
        _write_transcript(second_path, [{"role": "user", "content": "hi"}])

        paths = store.list_transcripts_for_source(source)

        assert paths == [second_path]

    def test_returns_empty_for_unknown_source(self, tmp_path):
        store = _make_store(tmp_path)
        known = _make_source(user_id="u1", chat_id="c1")
        unknown = _make_source(user_id="u2", chat_id="c2")
        store.get_or_create_session(known)
        # Write a transcript for the known source's session — the unknown
        # source must NOT pick it up.
        known_entry = store._entries[store._generate_session_key(known)]
        _write_transcript(
            store.get_transcript_path(known_entry.session_id),
            [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
        )

        assert store.list_transcripts_for_source(unknown) == []

    def test_respects_limit(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        entry = store.get_or_create_session(source)
        _write_transcript(
            store.get_transcript_path(entry.session_id),
            [{"role": "user", "content": "first"}],
        )
        for i in range(4):
            entry = store.reset_session(entry.session_key)
            _write_transcript(
                store.get_transcript_path(entry.session_id),
                [{"role": "user", "content": f"turn-{i}"}],
            )

        paths = store.list_transcripts_for_source(source, limit=2)

        assert len(paths) == 2
        # newest-first
        assert paths[0] == store.get_transcript_path(entry.session_id)


# ---------- collect_recent_exchanges ----------


class TestCollectRecentExchanges:
    def test_returns_none_when_no_transcripts(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        store.get_or_create_session(source)
        # session created but transcript never written
        assert collect_recent_exchanges(store, source, n=5) is None

    def test_returns_none_when_n_is_zero(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        entry = store.get_or_create_session(source)
        _write_transcript(
            store.get_transcript_path(entry.session_id),
            [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ],
        )
        assert collect_recent_exchanges(store, source, n=0) is None

    def test_pairs_user_and_assistant_in_chronological_order(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        entry = store.get_or_create_session(source)
        _write_transcript(
            store.get_transcript_path(entry.session_id),
            [
                {"role": "user", "content": "q1"},
                {"role": "assistant", "content": "a1"},
                {"role": "user", "content": "q2"},
                {"role": "assistant", "content": "a2"},
            ],
        )
        block = collect_recent_exchanges(store, source, n=5)
        assert block is not None
        assert block.index("q1") < block.index("a1") < block.index("q2") < block.index("a2")

    def test_skips_tool_call_only_assistant_turns(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        entry = store.get_or_create_session(source)
        _write_transcript(
            store.get_transcript_path(entry.session_id),
            [
                {"role": "user", "content": "fetch the weather"},
                {"role": "assistant", "content": "", "tool_calls": [{"id": "1"}]},
                {"role": "tool", "content": "sunny"},
                {"role": "assistant", "content": "It's sunny."},
            ],
        )
        block = collect_recent_exchanges(store, source, n=5)
        assert "It's sunny." in block
        assert "sunny" in block  # tool output appears via the assistant's reply
        # The tool message itself must not leak into the block
        assert "\"role\": \"tool\"" not in block

    def test_handles_anthropic_content_blocks(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        entry = store.get_or_create_session(source)
        _write_transcript(
            store.get_transcript_path(entry.session_id),
            [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "ask question"}],
                },
                {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "id": "t1", "name": "get_weather"},
                    ],
                },
                {"role": "tool", "content": "result"},
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "final answer"}],
                },
            ],
        )
        block = collect_recent_exchanges(store, source, n=5)
        assert "ask question" in block
        assert "final answer" in block

    def test_walks_back_through_lineage(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        entry = store.get_or_create_session(source)
        _write_transcript(
            store.get_transcript_path(entry.session_id),
            [
                {"role": "user", "content": "old-q"},
                {"role": "assistant", "content": "old-a"},
            ],
        )
        entry = store.reset_session(entry.session_key)
        _write_transcript(
            store.get_transcript_path(entry.session_id),
            [
                {"role": "user", "content": "new-q"},
                {"role": "assistant", "content": "new-a"},
            ],
        )
        block = collect_recent_exchanges(store, source, n=5)
        # Both pairs present, oldest first
        assert block.index("old-q") < block.index("new-q")

    def test_truncates_to_n_pairs(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        entry = store.get_or_create_session(source)
        messages = []
        for i in range(10):
            messages.append({"role": "user", "content": f"q{i}"})
            messages.append({"role": "assistant", "content": f"a{i}"})
        _write_transcript(store.get_transcript_path(entry.session_id), messages)
        block = collect_recent_exchanges(store, source, n=3)
        # Only the last 3 pairs should appear
        assert "a9" in block and "a8" in block and "a7" in block
        assert "a6" not in block

    def test_respects_max_chars_per_message(self, tmp_path):
        store = _make_store(tmp_path)
        source = _make_source()
        entry = store.get_or_create_session(source)
        long_text = "x" * 5000
        _write_transcript(
            store.get_transcript_path(entry.session_id),
            [
                {"role": "user", "content": long_text},
                {"role": "assistant", "content": long_text},
            ],
        )
        block = collect_recent_exchanges(
            store, source, n=5, max_chars_per_message=100
        )
        # Each truncated message should appear with capped length
        assert block.count("x" * 100) >= 2
        assert "x" * 200 not in block

    def test_does_not_leak_other_users_exchanges(self, tmp_path):
        store = _make_store(tmp_path)
        alice = _make_source(user_id="alice", chat_id="c-alice")
        bob = _make_source(user_id="bob", chat_id="c-bob")
        alice_entry = store.get_or_create_session(alice)
        bob_entry = store.get_or_create_session(bob)
        _write_transcript(
            store.get_transcript_path(alice_entry.session_id),
            [
                {"role": "user", "content": "alice-secret"},
                {"role": "assistant", "content": "alice-only"},
            ],
        )
        _write_transcript(
            store.get_transcript_path(bob_entry.session_id),
            [
                {"role": "user", "content": "bob-q"},
                {"role": "assistant", "content": "bob-a"},
            ],
        )
        bob_block = collect_recent_exchanges(store, bob, n=5)
        assert "alice-secret" not in bob_block
        assert "alice-only" not in bob_block
        assert "bob-q" in bob_block
