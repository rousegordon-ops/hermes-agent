---
name: sidekick-studio
description: "Work on Gordon's Sidekick Studio / Concierge app: repo layout, Railway deployment, share-page debugging, and app-specific pitfalls."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [sidekick-studio, concierge, railway, google-maps, node]
---

# Sidekick Studio

Use this skill when modifying, debugging, or deploying Sidekick Studio / Concierge at `sidekickstudio.net`, including shared session rendering, Concierge tool behavior, Google Maps links, and Railway deployment.

## Repo and architecture

- Source repo: `/opt/data/sidekickstudio` (GitHub: `rousegordon-ops/SidekickStudio`).
- Main server: `server.js` — Express routes, Socket.io namespaces, app registration.
- App configs: `apps/*/config.js`; Concierge is `apps/concierge/config.js`.
- Shared public view: `public/share.html`; share messages endpoint is `/<app>/share/:token/messages` in `server.js`.
- Package: Node app (`npm start` runs `node server.js`). Use `node --check` for syntax validation.

## Concierge Google Maps address links

Root cause from 2026-06-11: Concierge generated Google Maps search URLs with `query_place_id`. Some links opened the wrong place or failed even when the text query was correct, because synthesized/stale/mismatched place IDs can override the query.

Rules:
1. `search_places` / `validate_business` should prefer the Places API-provided `googleMapsUri` when available.
2. If no canonical URI exists, generate a query-only URL:
   `https://www.google.com/maps/search/?api=1&query=<business name + address>`
3. Do **not** synthesize `query_place_id` into Google Maps URLs.
4. For existing shared messages, the `/share/:token/messages` cleaning layer should strip `query_place_id` from `https://www.google.com/maps/search/` links before returning content.
5. User-visible address links must keep the street address as link text, not “Google Maps.”

## Debug shared sessions

For a share URL like:

```text
https://sidekickstudio.net/concierge/share/<token>#msg-1
```

Fetch messages directly; ignore the fragment for HTTP:

```bash
python3 - <<'PY'
import json, urllib.request
url='https://sidekickstudio.net/concierge/share/<token>/messages'
data=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30))
for i,m in enumerate(data['messages'],1):
    print('---', i, m['role'])
    print(m['content'])
PY
```

Also check raw stored assistant content when needed:

```text
https://sidekickstudio.net/concierge/share/<token>/raw
```

## Railway deployment

This app is Railway project `tranquil-truth`, service `content-mercy`, public URL `https://sidekickstudio.net`.

Hermes' environment variables can mask the repo's Railway link. Always unset them for Sidekick Railway commands:

```bash
cd /opt/data/sidekickstudio
env -u RAILWAY_PROJECT_ID -u RAILWAY_SERVICE_ID -u RAILWAY_ENVIRONMENT_ID \
  npx --yes @railway/cli status
```

If not linked:

```bash
env -u RAILWAY_PROJECT_ID -u RAILWAY_SERVICE_ID -u RAILWAY_ENVIRONMENT_ID \
  npx --yes @railway/cli link \
  --project 8f675138-e1c6-43ea-9081-df0531e8e792 \
  --environment production \
  --service 4af308de-63a1-4978-8735-30dbc5dc5494
```

Deploy and verify:

```bash
cd /opt/data/sidekickstudio
node --check server.js
node --check apps/concierge/config.js
git diff --check
git add <files>
git commit -m "<message>"
GIT_TERMINAL_PROMPT=0 git push origin main
env -u RAILWAY_PROJECT_ID -u RAILWAY_SERVICE_ID -u RAILWAY_ENVIRONMENT_ID \
  npx --yes @railway/cli up --service content-mercy
env -u RAILWAY_PROJECT_ID -u RAILWAY_SERVICE_ID -u RAILWAY_ENVIRONMENT_ID \
  npx --yes @railway/cli deployment list --service content-mercy
```

Confirm the newest deployment is `SUCCESS`, then verify the live behavior with HTTP requests to `sidekickstudio.net`.

## Pitfalls

- `web_extract` may fail on Sidekick share pages, but direct `urllib.request` to `/messages` works.
- Do not deploy with Railway env vars still set; otherwise `railway status/up` points at Hermes (`pretty-amazement` / `hermes-agent`) instead of Sidekick.
- Build success is not enough; check `railway deployment list` and then verify the live URL.
