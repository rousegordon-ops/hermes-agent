# Railway Deployment Reference

## Container Layout

```
/opt/hermes/gateway  → symlink → /opt/data/repo/gateway
/opt/hermes/tools    → symlink → /opt/data/repo/tools
/opt/hermes/scripts  → symlink → /opt/data/repo/scripts
/opt/data/repo       = git checkout (source of truth)
/opt/data/skills     → symlink → /opt/data/repo/skills
```

Edits to either side of a symlink are the same write. The gateway and daemons run from `/opt/hermes/*` symlinks; `/opt/data/repo` is the git-accessible source.

## Branch Convention

- `main` — source of truth; watcher pushes here
- `release-pin` — what Railway watches for image rebuilds. Pushing here triggers a rebuild.

## Self-Deployment Skills

### self-restart (Bucket-2 changes)
Triggers `serviceInstanceRedeploy` GraphQL mutation → Railway redeploys the container on the same image. Fast (~$0, ~30s). Gateway process exits mid-reply.

### self-rebuild (Bucket-3 changes)
Pushes `main:release-pin` → triggers a full Railway image rebuild. Slow (~$0.11, ~10min). Service down during rebuild.

## Common Failure Modes

### RAILWAY_API_TOKEN returns HTTP 403 on backboard GraphQL

**Symptom:** `urllib.error.HTTPError: HTTP Error 403: Forbidden` on every GraphQL mutation.

**Cause:** The token lacks `backboard` scope, or it's a deploy-token rather than an account-level API token. Cloudflare returns "Access denied" (HTTP 403, code 1010) before Railway's API even sees the request.

**Fix:** Generate a new token at https://railway.app/account with `read` + `write` scopes. Update the `RAILWAY_API_TOKEN` env var in the Railway project settings.

**Verify:**
```python
# This also fails with 403 if token is bad:
query = '{"query":"{ project(id: \"c49b3e8b-a36d-4d24-a972-eab5e05b881d\") { name } }"}'
```

### git push to origin/main fails (self-rebuild Step 2)

**Symptom:** `fatal: could not read Username for 'https://github.com': No such device or address`

**Cause:** `~/.git-credentials` doesn't exist. Even though `GITHUB_TOKEN` is set in the environment, the entrypoint doesn't write `~/.git-credentials` for the `hermes` user. Also note: running as `hermes` means `~` = `/home/hermes` (which doesn't exist), so the file would need to be `/home/hermes/.git-credentials`.

**Fix options:**
1. Manually create credentials: `echo "https://github.com:$(GITHUB_TOKEN=your_token python3 -c 'import urllib.parse;print(urllib.parse.quote(input()))')@github.com" > ~/.git-credentials`
2. Use SSH git remote: `git remote set-url origin git@github.com:rousegordon-ops/hermes-agent.git` (requires SSH key in the container)
3. Do the push from your local machine

**Entry in skill should say:** "If ~/.git-credentials is missing, fall back to manual git push from /opt/data/repo, or use SSH URL."

### source_watcher.commit_now() does nothing

**Symptom:** `[source-watcher] commit_and_push called but tree is clean; skipping`

**Cause:** The watcher only commits if there are uncommitted changes. If the tree is clean (all changes already committed or no changes), it skips. This is fine — it means the change is already on origin/main.

## Environment Variables (from running container)

```
RAILWAY_API_TOKEN=472e2d2f-c197-44d2-8a3a-8e95f1a3758e
RAILWAY_PROJECT_ID=c49b3e8b-a36d-4d24-a972-eab5e05b881d
RAILWAY_ENVIRONMENT_ID=38eea0f3-0bd3-48f4-abaf-ec3de09174de
RAILWAY_SERVICE_ID=c32be0a9-9d43-49a8-bf43-764915360dfb
GITHUB_TOKEN=github_pat_11CAZSPJQ0Kg3IOVyM8Ece_...  # Fine-grained PAT
TELEGRAM_BOT_TOKEN=8767103984:AAHkVZp9c4jrOzhpz24vvoH0eSow9yu7WGk
TELEGRAM_HOME_CHANNEL=8746106424
OPENROUTER_API_KEY=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
```

## Railway GraphQL IDs (not secrets)

```
Project ID:        c49b3e8b-a36d-4d24-a972-eab5e05b881d  (pretty-amazement)
Environment ID:    38eea0f3-0bd3-48f4-abaf-ec3de09174de  (production)
Service ID:        c32be0a9-9d43-49a8-bf43-764915360dfb  (hermes-agent)
```

## Introspection Query (find mutation names)

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { mutationType { fields { name } } } }"}' \
  | python3 -c "import json,sys; [print(f['name']) for f in json.load(sys.stdin)['data']['__schema']['mutationType']['fields'] if 'redeploy' in f['name'].lower()]"
```
