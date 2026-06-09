# OpenAI Codex OAuth re-auth and auxiliary 401s

Use this when Hermes logs errors like:

- `Auxiliary title generation failed: HTTP 401: Provided authentication token is expired`
- `Title generation failed: Error code: 401 ... token_expired`
- `Failed to generate context summary ... token_expired`

## What it means

Auxiliary tasks such as `title_generation` and `compression` can be configured to use the OpenAI Codex / ChatGPT OAuth backend. A stale or consumed OAuth access/refresh token can fail only those auxiliary paths even when the main conversation mostly continues.

## Gordon Railway path

On Gordon's Railway deployment the `hermes` executable may not be on PATH and system Python may not have dependencies. Use the repo entrypoint through `uv`:

```bash
cd /opt/data/repo
HERMES_HOME=/opt/data uv run /opt/data/repo/hermes auth list openai-codex
```

## Re-auth flow

Start the device-code login without opening a browser in the container:

```bash
cd /opt/data/repo
HERMES_HOME=/opt/data uv run /opt/data/repo/hermes auth add openai-codex --type oauth --no-browser --timeout 600
```

Send Gordon the displayed device URL and code. Do not expose any token values.

After he completes the device flow, verify:

```bash
cd /opt/data/repo
HERMES_HOME=/opt/data uv run /opt/data/repo/hermes auth list openai-codex
HERMES_HOME=/opt/data uv run /opt/data/repo/hermes auth status openai-codex
```

Expected status includes `openai-codex: logged in` and a new `openai-codex-oauth-N` credential.

## Functional checks

Main Codex call:

```bash
cd /opt/data/repo
HERMES_HOME=/opt/data uv run /opt/data/repo/hermes chat -q 'Reply with exactly: codex ok' --provider openai-codex -m gpt-5.5 -Q --source auth-check
```

Auxiliary title-generation path:

```bash
cd /opt/data/repo
HERMES_HOME=/opt/data uv run python - <<'PY'
from agent.auxiliary_client import call_llm
messages=[{'role':'user','content':'Return exactly: title ok'}]
r=call_llm(task='title_generation', messages=messages, max_tokens=20)
print(r.choices[0].message.content.strip())
PY
```

## Pitfalls

- `hermes login --provider openai-codex` is obsolete in this deployment; it prints that `hermes login` has been removed.
- Do not run `/opt/data/repo/hermes` directly with system Python if dependencies are missing (`ModuleNotFoundError: yaml`). Use `uv run`.
- Re-auth adds a new credential and may not automatically make it the displayed current `←` entry under fill-first selection; a functional check is more useful than only reading the marker.
- Never print, paste, or log OAuth token values from `/opt/data/auth.json`.
