# OpenAI Codex OAuth re-auth on Gordon's Railway instance

Use this when Codex/ChatGPT-backed primary or auxiliary calls fail with `401 token_expired`, e.g. `Auxiliary title generation failed` or `Failed to generate context summary`.

## What happened in the June 2026 session

- Logs showed `auxiliary.title_generation.provider: codex` and `auxiliary.compression.provider: codex` using `gpt-5.5` at `https://chatgpt.com/backend-api/codex/`.
- `agent.title_generator` failed at 2026-06-09 04:02 UTC and 05:23 UTC with `Provided authentication token is expired` / `token_expired`.
- `/opt/data/auth.json` still contained OpenAI Codex OAuth credentials with refresh tokens and a recent `last_refresh`, but the access path returned 401 anyway.
- The CLI docs in the skill were stale: `hermes login --provider openai-codex` prints that `hermes login` was removed.

## Commands that worked

On Railway, `hermes` may not be on PATH and system Python may lack dependencies. Use the repo wrapper via `uv` and set Gordon's Hermes home explicitly:

```bash
cd /opt/data/repo
HERMES_HOME=/opt/data uv run /opt/data/repo/hermes auth list openai-codex
HERMES_HOME=/opt/data uv run /opt/data/repo/hermes auth add openai-codex --type oauth --no-browser --timeout 600
```

The second command prints:

```text
Open this URL: https://auth.openai.com/codex/device
Enter this code: XXXX-XXXX
Waiting for sign-in...
```

Send the URL and code to Gordon, then poll the process until it exits. Do not paste token values from `auth.json` or logs.

## Verification

After Gordon completes device login:

```bash
HERMES_HOME=/opt/data uv run /opt/data/repo/hermes auth list openai-codex
```

Then make a small Codex-backed call or watch logs for no new `token_expired` warnings. If the gateway process caches credentials, restart the gateway/Railway service after auth refresh.

## Pitfalls

- Do not use `hermes login`; it is removed in this fork/runtime.
- Do not assume re-auth failed just because a previous usage-limit issue was fixed. Plan upgrades and OAuth token refresh are separate failure modes.
- Never print values of `access_token`, `refresh_token`, API keys, or full env vars. It is safe to report credential labels, provider names, timestamps, and whether secret fields are present.
