# Railway reliability backports — 2026-09-09

Manual adaptations for this fork; no upstream merge or dependency change in the application manifest. Existing Railway startup, routing, and personal workflows are preserved.

## Changes and upstream sources

- Telegram: bound polling pool shutdown/reinitialization and updater stop at 15 seconds; bound polling startup at 30 seconds. Failed conflict restarts now schedule another attempt instead of waiting for callbacks from a stopped poller. Sources: [drain deadline](https://github.com/NousResearch/hermes-agent/commit/3391e639f6), [stop deadline](https://github.com/NousResearch/hermes-agent/commit/8645b34303), [polling startup](https://github.com/NousResearch/hermes-agent/commit/4aaaa206aa), [all startup sites](https://github.com/NousResearch/hermes-agent/commit/aaeba213d9).
- Telegram delivery: wrapped HTTPX connection/pool timeouts retry through the existing backoff loop and remain retryable on exhaustion. Read/write/ambiguous timeouts remain non-retryable to avoid duplicate delivery. Sources: [connection timeouts](https://github.com/NousResearch/hermes-agent/commit/af381ef12c), [pool timeouts](https://github.com/NousResearch/hermes-agent/commit/dc4de14377).
- Codex OAuth: hold the existing cross-process auth-store lock across token re-sync, refresh, and write-back. Adopt a newer usable token without refreshing it again, including forced recovery. Source: [refresh serialization](https://github.com/NousResearch/hermes-agent/commit/da6d5fcd13).
- Prompt caching: normalize the configured model using the same provider-aware normalizer as AIAgent before deciding whether fallback requires cache eviction. Real fallbacks and intentional model switches retain their prior behavior. Source: [gateway cache normalization](https://github.com/NousResearch/hermes-agent/commit/d6c53dcdcb). Its Discord message-ID change is outside this Telegram-focused batch.

## Fork-specific completion

`agent.gateway_agent_cache_max_size` defaults to 128 and clamps to a minimum of 1. Zero cannot safely evict a newly constructed agent before the turn starts. `agent.gateway_agent_cache_idle_ttl` defaults to 3600 seconds; zero disables time-based eviction. Invalid/nonfinite values fall back to defaults. Environment overrides remain supported. Active turns remain protected from eviction.

Continuity now reads only the preceding session associated with the same gateway conversation key, including that key's topic/user scoping. The text is captured once and saved in session metadata. Later turns, agent eviction, and gateway restart reuse the snapshot. An empty or disabled snapshot is also frozen. Existing sessions with no recorded predecessor do not scan other transcripts. Changing the continuity window takes effect on a new session. Extraction retains at most the requested number of exchange pairs; the gateway caps the window at 20.

The unfinished watchdog is preserved locally in the Git-ignored directory `tmp/deferred-memory-watchdog-2026-09-09/`, including its original script and Docker startup patch. It is excluded from this change and is not enabled.

## Validation

Result: **236 tests passed** with the canonical four-worker runner. The focused Ruff error checks and `git diff --check` also passed.

Run the targeted suite with:

```sh
scripts/run_tests.sh tests/gateway/test_agent_cache.py tests/gateway/test_continuity_snapshot.py tests/gateway/test_telegram_network_reconnect.py tests/gateway/test_telegram_thread_fallback.py tests/agent/test_credential_pool.py tests/gateway/test_restart_resume_pending.py tests/gateway/test_session_race_guard.py tests/gateway/test_session_store_prune.py --tb=short -q
```

Coverage includes two concurrent processes consuming one Codex refresh token, actual YAML startup configuration, environment precedence, cache limits and active-turn protection, safe versus ambiguous Telegram retries, stalled cleanup/startup, conversation isolation, and continuity persistence across restarts.

The older `tests/gateway/test_session.py` cannot collect because it imports `normalize_whatsapp_identifier`, which is absent from this fork's `gateway/session.py` at the original HEAD as well. This unrelated baseline mismatch has not been changed. The focused continuity and existing restart/race/prune suites exercise the session paths touched here.

No live Telegram messages, Railway restart, push, or deployment were performed. Local test dependencies were installed in `.venv` after checking publication dates; an older regex version was selected to honor the 24-hour embargo.

## Deployment preparation

The Codex pool and config modules are image-baked, so this batch requires an image rebuild, not only a restart. Docker now uses `npm ci` for lockfile-faithful Node installs and `uv pip install --exclude-newer "7 days"` to explicitly preserve the project’s existing stricter cutoff during Python resolution. See [uv resolution documentation](https://docs.astral.sh/uv/concepts/resolution/#excluding-newer-packages).
