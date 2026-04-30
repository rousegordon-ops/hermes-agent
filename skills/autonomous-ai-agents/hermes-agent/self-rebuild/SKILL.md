---
name: self-rebuild
description: "Trigger a full Railway image rebuild when Bucket-3 code or dependencies change."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, railway, deployment, rebuild]
    homepage: https://github.com/NousResearch/hermes-agent
---

# self-rebuild

Trigger a full Railway image rebuild. Required when image-baked code or dependencies change.

## When to Invoke

- You just edited a **Bucket-3** file: `Dockerfile`, `docker/**`, `pyproject.toml`, `package*.json`, `requirements*.txt`, `uv.lock`.
- AND the change can't wait for someone else to trigger.
- AND the user has given **explicit confirmation** (see below).

**Bucket quick-ref:**
- Bucket 1 (no action): `skills/**`, `*.md`, `docs/**`, `scripts/cost_report.py`
- Bucket 2 (self-restart): `tools/**`, `gateway/**`, `scripts/source_watcher.py`, `scripts/cost_report_daemon.py`, top-level `*.py`
- Bucket 3 (self-rebuild): `Dockerfile`, `docker/**`, `pyproject.toml`, `package*.json`, `requirements*.txt`, `uv.lock`

## User Confirmation (REQUIRED)

**Always ask before triggering.** Say:

> "Editing `{file}` requires a Railway rebuild — ~$0.11 in build minutes and ~10 min. OK to trigger?"

Wait for explicit `yes` / `y` / `go ahead` before proceeding. If the user says no, do not trigger.

## Action (two steps)

### Step 1 — Push pending edits to origin/main

Force an immediate commit + push without waiting for the 180s watcher debounce:

```python
import sys
sys.path.insert(0, "/opt/hermes/scripts")
from source_watcher import commit_now
commit_now()
```

### Step 1.5 — Verify the commit landed on origin/main

```bash
git -C /opt/data/repo log origin/main -1 --oneline
```

The HEAD line should be the auto-commit you just made (or the watcher's just-pushed commit). If it shows an older commit, your push to release-pin in the next step will deploy stale code — investigate before continuing.

### Step 2 — Push main to release-pin

```bash
git -C /opt/data/repo push origin main:release-pin
```

This triggers a Railway image rebuild because Railway watches the `release-pin` branch.

## Caveats

- Rebuilds cost ~$0.11 in build minutes and take ~10 minutes.
- The rebuild can fail (broken Dockerfile, bad deps) leaving the service in a broken state.
- After triggering, tell the user: **"Rebuild triggered — service will be down for ~10 min. Monitor at https://railway.app/project/pretty-amazement"**

## Required env / setup

This skill assumes:
- `$RAILWAY_API_TOKEN` is set (verify with `[ -n "$RAILWAY_API_TOKEN" ]`). Not used directly here, but its presence indicates the operator has configured the container for self-management.
- Git auth is configured (entrypoint writes `~/.git-credentials` from `$GITHUB_TOKEN`). Verify with `cat ~/.git-credentials | head -c 30` if there's any doubt.
- The watcher daemon is running (otherwise `commit_now()` does nothing — fall back to `manual git add -A && git commit -m '…' && git push origin main` from `/opt/data/repo`).

If any of these aren't set, stop and tell me — don't try to provision them yourself.

## Verification

Print the raw git push output and tell the user clearly what just happened and what to expect.
