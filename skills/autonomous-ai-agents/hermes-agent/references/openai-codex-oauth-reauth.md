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

Then make a small Codex-backed title-generation call:

```bash
HERMES_HOME=/opt/data uv run python3 - <<'PY'
from agent.title_generator import generate_title
print(generate_title('Please test title generation', 'I verified the auxiliary title generation path works.', timeout=60))
PY
```

If the gateway process caches credentials, restart the gateway/Railway service after auth refresh.

## Credential-pool refresh without device login

On Gordon's Railway instance, `auth add openai-codex --type oauth --no-browser` can time out even if the user says they completed the browser flow. Before repeating device codes, try refreshing the existing pooled OAuth refresh tokens directly. Do not print token values.

```bash
HERMES_HOME=/opt/data uv run python3 - <<'PY'
import json
from pathlib import Path
from datetime import datetime, timezone
from hermes_cli.auth import refresh_codex_oauth_pure

p = Path('/opt/data/auth.json')
data = json.loads(p.read_text())
creds = data.get('credential_pool', {}).get('openai-codex', [])
for i, c in enumerate(creds, 1):
    try:
        updated = refresh_codex_oauth_pure(c.get('access_token', ''), c.get('refresh_token', ''), timeout_seconds=20)
        c['access_token'] = updated['access_token']
        c['refresh_token'] = updated.get('refresh_token', c.get('refresh_token', ''))
        c['last_refresh'] = updated.get('last_refresh', datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
        c['last_status'] = 'ok'
        c['last_error_code'] = None
        c['last_error_message'] = None
        print(f'credential #{i}: refresh ok')
    except Exception as e:
        print(f'credential #{i}: refresh failed {type(e).__name__}: {str(e).splitlines()[0]} code={getattr(e, "code", None)} relogin={getattr(e, "relogin_required", None)}')
data['updated_at'] = datetime.now(timezone.utc).isoformat()
p.write_text(json.dumps(data, indent=2))
PY
```

Then run the title-generation verification above. This refreshes `/opt/data/auth.json` `credential_pool.openai-codex[*]`; the older `_read_codex_tokens()` helper may report missing credentials because it reads the legacy `providers` shape, not the credential-pool shape.

## Pitfalls

- Do not use `hermes login`; it is removed in this fork/runtime.
- Do not assume re-auth failed just because a previous usage-limit issue was fixed. Plan upgrades and OAuth token refresh are separate failure modes.
- Never print values of `access_token`, `refresh_token`, API keys, or full env vars. It is safe to report credential labels, provider names, timestamps, and whether secret fields are present.
