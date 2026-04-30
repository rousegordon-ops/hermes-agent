---
name: self-restart
description: "Trigger a Railway redeploy of the hermes-agent service (container exit + restart on same image)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, railway, deployment, restart]
    homepage: https://github.com/NousResearch/hermes-agent
---

# self-restart

Trigger a Railway redeploy of the hermes-agent service. The container exits and a new container starts on the same image; the entrypoint refreshes `/opt/data/repo`, and daemons + gateway pick up the new code via symlinks.

## When to Invoke

- You just edited a **Bucket-2** file: `tools/**`, `gateway/**`, `scripts/source_watcher.py`, `scripts/cost_report_daemon.py`, top-level `*.py` (anything imported into the long-running gateway or long-running daemon scripts).
- AND you want the change live (not just persisted to git).
- AND it is **not** a rebuild-class change (not a Bucket-3 file: no Dockerfile, docker/**, pyproject.toml, package*.json, requirements*.txt, uv.lock).

**Bucket quick-ref:**
- Bucket 1 (no action): `skills/**`, `*.md`, `docs/**`, `scripts/cost_report.py`
- Bucket 2 (self-restart): `tools/**`, `gateway/**`, `scripts/source_watcher.py`, `scripts/cost_report_daemon.py`, top-level `*.py`
- Bucket 3 (self-rebuild): `Dockerfile`, `docker/**`, `pyproject.toml`, `package*.json`, `requirements*.txt`, `uv.lock`

## Action

POST the `serviceInstanceRedeploy` mutation to Railway's GraphQL API.

**Caution:** The gateway process exits when the container is told to redeploy — the current conversation will be cut short mid-reply. **Tell the user "Restarting now — your message will be answered by the new container in ~30s" before triggering.**

Pending uncommitted edits in `/opt/data/repo` survive the restart (entrypoint preserves them); the watcher commits them on next boot. You can trigger restart immediately after editing without waiting for the watcher.

No user confirmation required — restart is cheap and routine.

## Implementation

```python
import os, subprocess, urllib.request, json

RAILWAY_API_TOKEN = os.environ.get("RAILWAY_API_TOKEN")
PROJECT_ID = "c49b3e8b-a36d-4d24-a972-eab5e05b881d"
ENVIRONMENT_ID = "38eea0f3-0bd3-48f4-abaf-ec3de09174de"
SERVICE_ID = "c32be0a9-9d43-49a8-bf43-764915360dfb"

mutation = """
mutation serviceInstanceRedeploy($serviceId: String!, $environmentId: String!) {
  serviceInstanceRedeploy(serviceId: $serviceId, environmentId: $environmentId)
}
"""

variables = {
    "serviceId": SERVICE_ID,
    "environmentId": ENVIRONMENT_ID,
}

body = json.dumps({"query": mutation, "variables": variables}).encode()
req = urllib.request.Request(
    "https://backboard.railway.app/graphql/v2",
    data=body,
    headers={"Authorization": f"Bearer {RAILWAY_API_TOKEN}", "Content-Type": "application/json", "User-Agent": "railway-cli/4.44.0"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())

print(json.dumps(result, indent=2))
```

## Verification

Print the raw API response verbatim. Tell the user clearly: **"Restarting now — your message will be answered by the new container in ~30s."**

## If the mutation fails

Railway has renamed GraphQL mutations historically. Two distinct failure modes are known:

**Mode A — HTTP 403 from Cloudflare (code 1010 "Access denied"):**
The token lacks `backboard` scope, or is a deploy-token rather than an account-level API token. Cloudflare returns this before Railway's API sees the request.
- Verify: the introspection query also fails with 403
- Fix: generate a new token at https://railway.app/account with `read` + `write` scopes; update `RAILWAY_API_TOKEN` in Railway project settings
- **Also**: Cloudflare requires a `User-Agent` header that looks like a real browser/CLI client. Python's urllib sends no User-Agent by default and gets 403. Always include `User-Agent: railway-cli/4.44.0` (or similar) in the request headers.

**Mode B — "Cannot query field":**
The mutation name was renamed (e.g. `serviceInstanceRedeploy` → `deploymentRedeploy`).

### Diagnosing Which Failure Mode

1. **Try the redeploy mutation first** (the code above).
2. **If it fails with 403**, run the introspection probe:
```bash
python3 -c "
import os, urllib.request, json
token = os.environ.get('RAILWAY_API_TOKEN')
query = '{\"query\":\"{ __schema { mutationType { fields { name } } } }\"}'
body = query.encode()
req = urllib.request.Request(
    'https://backboard.railway.app/graphql/v2',
    data=body,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
for f in result.get('data', {}).get('__schema', {}).get('mutationType', {}).get('fields', []):
    if 'redeploy' in f['name'].lower():
        print(f['name'])
"
```

3. **Interpret the result:**
   - **Introspection also 403s** → **Mode A** (bad token). The introspection probe itself will 403, so you cannot use it to discover a renamed mutation. Generate a new account-level token.
   - **Introspection returns fields but redeploy fails with "Cannot query field"** → **Mode B** (mutation renamed). Use the name from introspection.
   - **Introspection returns 200 but no redeploy field** → Railway may have removed the redeploy mutation entirely; check Railway docs or use the Railway CLI from outside the container instead.

### Container tool limitations

This Railway container has **no `curl` or `wget`** — only Python stdlib `urllib`. The 403 cannot be bypassed with alternate HTTP clients. If stdlib urllib is blocked by Cloudflare and a token fix is not possible, fall back to:
- Railway CLI run from outside the container: `railway redeploy`
- Railway dashboard: manual redeploy button at railway.app
