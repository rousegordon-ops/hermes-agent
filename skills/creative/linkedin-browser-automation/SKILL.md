---
name: linkedin-browser-automation
description: "Using agent-browser with LinkedIn session cookies for authenticated profile access."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [linkedin, browser, scraping, agent-browser]
    category: creative
---

# linkedin-browser-automation

Using `agent-browser` with a LinkedIn session cookie to access authenticated profile data.

## Getting the Cookie

In Chrome on your machine:
1. Go to linkedin.com
2. Open DevTools (`Cmd+Option+I` on Mac, `F12` on Windows)
3. **Application** tab → **Cookies** → `https://www.linkedin.com`
4. Find row with name `li_at` and copy the **Value**

**Important:** Only the browser with an active session can see this cookie. LinkedIn authwalls block all non-browser access.

## Injecting the Cookie

```bash
# Close any existing browser session first
node /opt/hermes/node_modules/.bin/agent-browser close

# Create a state file with the cookie
cat > /tmp/li-state.json << 'EOF'
{
  "cookies": [{"name": "li_at", "value": "<TOKEN>", "domain": ".linkedin.com", "path": "/", "secure": true}],
  "origins": []
}
EOF

# Open LinkedIn with authenticated session
node /opt/hermes/node_modules/.bin/agent-browser open "https://www.linkedin.com/in/PROFILE/" --state /tmp/li-state.json
```

## Critical Gotcha: Cookie Invalidation

LinkedIn aggressively detects and **invalidates** `li_at` tokens when it detects non-browser API usage. Signs of detection:
- `set-cookie: li_at=delete me` in HTTP response headers
- Profile pages redirecting to authwall after initial success
- 403 responses from `/voyager/api/` endpoints

**Rules to keep the cookie alive:**
1. **Never make raw HTTP requests** (curl, Python urllib, etc.) with the cookie — LinkedIn detects the non-browser fingerprint and kills it instantly
2. **Only use browser navigation** — `agent-browser open` commands, not direct API calls
3. **Fresh cookies only** — if the token was ever used in a non-browser context, it's dead
4. If cookie dies, get a fresh one from the browser before trying again

## Getting Profile Data

Once authenticated:
```bash
node /opt/hermes/node_modules/.bin/agent-browser open "https://www.linkedin.com/in/PROFILE/"
node /opt/hermes/node_modules/.bin/agent-browser eval "(() => { const m = document.querySelector('main') || document.body; return m.innerText.substring(0, 10000); })();"
node /opt/hermes/node_modules/.bin/agent-browser snapshot
```

## Alternative: Manual Screenshot

If cookie setup is too cumbersome, just open LinkedIn in your own browser, go to the profile, take a screenshot, and share it. From the screenshot I can read everything needed for resumes, landing pages, etc. More reliable than fighting LinkedIn's automation detection.