"""Continuity is scoped to a conversation and frozen across cache rebuilds."""
import json

import pytest

from gateway.config import GatewayConfig, Platform
from gateway.session import SessionSource, SessionStore


def _pair(store, entry, text):
    for role in ('user', 'assistant'):
        store.append_to_transcript(entry.session_id, {'role': role, 'content': f'{role}: {text}'})


@pytest.mark.parametrize('reset', ['explicit', 'forced', 'suspended'])
def test_snapshot_same_conversation_and_stable_after_restart(tmp_path, reset):
    config = GatewayConfig()
    store = SessionStore(tmp_path / 'sessions', config)
    a = SessionSource(platform=Platform.TELEGRAM, chat_id='1', thread_id='10')
    b = SessionSource(platform=Platform.TELEGRAM, chat_id='1', thread_id='20')
    old = store.get_or_create_session(a)
    _pair(store, old, 'remember my itinerary')
    other = store.get_or_create_session(b)
    _pair(store, other, 'private unrelated conversation')
    if reset == 'explicit':
        new = store.reset_session(old.session_key)
    elif reset == 'forced':
        new = store.get_or_create_session(a, force_new=True)
    else:
        store.suspend_session(old.session_key)
        new = store.get_or_create_session(a)
    snapshot = store.get_continuity_context(new, 5)
    assert 'remember my itinerary' in snapshot
    assert 'private unrelated' not in snapshot
    _pair(store, new, 'new turn must not alter the prompt')
    _pair(store, old, 'late write must not alter the snapshot')
    assert store.get_continuity_context(new, 1) == snapshot
    restored = SessionStore(store.sessions_dir, config)
    resumed = restored.get_or_create_session(a)
    assert restored.get_continuity_context(resumed, 20) == snapshot
    if store._db:
        store._db.close()
    if restored._db:
        restored._db.close()


def test_empty_or_disabled_snapshot_does_not_later_pick_up_history(tmp_path):
    store = SessionStore(tmp_path / 'sessions', GatewayConfig())
    source = SessionSource(platform=Platform.TELEGRAM, chat_id='1')
    first = store.get_or_create_session(source)
    assert store.get_continuity_context(first, 5) == ''
    _pair(store, first, 'old message')
    new = store.reset_session(first.session_key)
    assert store.get_continuity_context(new, 0) == ''
    assert store.get_continuity_context(new, 5) == ''
    if store._db:
        store._db.close()


def test_legacy_entry_does_not_scan_unrelated_transcripts(tmp_path):
    from gateway.session import SessionEntry
    from datetime import datetime
    entry = SessionEntry('key', 'old', datetime.now(), datetime.now())
    data = entry.to_dict()
    data.pop('previous_session_id')
    data.pop('continuity_context')
    (tmp_path / 'unrelated.jsonl').write_text(json.dumps({'role': 'user', 'content': 'private'}))
    store = SessionStore(tmp_path, GatewayConfig())
    assert store.get_continuity_context(SessionEntry.from_dict(data), 5) == ''
    if store._db:
        store._db.close()
