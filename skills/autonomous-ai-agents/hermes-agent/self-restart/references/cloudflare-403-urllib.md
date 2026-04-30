# Cloudflare 403 on Railway Backboard — urllib User-Agent Requirement

## Symptom
HTTP 403 Forbidden from `backboard.railway.app/graphql/v2` — blocked at Cloudflare's WAF
before the request reaches Railway's API. Works from Railway CLI, fails from Python `urllib`.

## Root Cause
Cloudflare's WAF blocks requests without a `User-Agent` header that looks like a real client.
Python's `urllib.request.Request` sends **no User-Agent by default**, so Cloudflare
returns 403 before Railway sees the request.

Railway CLI avoids this because it sends `User-Agent: railway-cli/<version>`.

## Fix
Always include a realistic User-Agent header:

```python
headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "User-Agent": "railway-cli/4.44.0",  # required by Cloudflare WAF
},
```

Tested confirmed working: `urllib` + `User-Agent: railway-cli/4.44.0` → `{"data": {"serviceInstanceRedeploy": true}}`

## Affected APIs
- `https://backboard.railway.app/graphql/v2` — Railway backboard API
- Likely any Cloudflare-proxied API accessed from Railway containers without a browser-like UA

## Other Requests Failing This Way
- `cost_report.py` → OpenRouter `/credits` API — same fix: add `User-Agent: hermes-agent/1.0`
- Any `urllib` call to external APIs from within Railway containers

## Verification
```python
# This works (with UA)
req = urllib.request.Request(url, headers={
    "Authorization": f"Bearer {token}",
    "User-Agent": "railway-cli/4.44.0",
})

# This gets 403 (no UA)
req = urllib.request.Request(url, headers={
    "Authorization": f"Bearer {token}",
})
```
