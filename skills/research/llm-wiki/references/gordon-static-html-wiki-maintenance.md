# Gordon Static HTML Wiki Maintenance Notes

Use these notes when maintaining Gordon's Cloudflare Pages wiki at `/opt/data/hermes-pages/wiki/`.

## Canonical deployment

- Source of truth: `/opt/data/hermes-pages/wiki/` static HTML.
- Deploy mirror: `/opt/data/hermes-pages-files/wiki/`.
- Cloudflare Pages project name: `hermes-pages`.
- Public/custom Pages domain: `https://hermes-pages-d55.pages.dev/`.
- Do **not** pass `--project-name hermes-pages-d55`; that is the Pages domain suffix, not the project name. Wrangler returns `Project not found`.

Deploy command:

```bash
rm -rf /opt/data/hermes-pages-files/wiki \
  && cp -a /opt/data/hermes-pages/wiki /opt/data/hermes-pages-files/wiki \
  && export PATH=/opt/data/.nvm/bin:$PATH \
  && /opt/data/.npm-global/bin/wrangler pages deploy /opt/data/hermes-pages-files \
       --project-name hermes-pages --branch main --commit-dirty=true
```

## Static child-page workflow

When the user asks for a deep dive into a bucket item or subsection:

1. Read the parent hub page and index page.
2. Create a child directory/page under the semantic parent, e.g. `wiki/business-opportunities/acquire-local-service-business.html`.
3. Add a link from the parent card/section to the child page.
4. Add the child page to `wiki/index.html` only if it is important enough to browse directly.
5. Append a concise entry to `wiki/log.html`.
6. Copy to deploy mirror and deploy with project name `hermes-pages`.
7. Verify the live page with `curl -L -A 'Mozilla/5.0' -H 'Cookie: wiki_auth=GW2026' <url>`.

## Verification quirks

- `urllib.request` may receive `403 Forbidden` from Cloudflare even when the page is live. Prefer `curl` with a browser-like user agent.
- The auth gate is client-side JavaScript, so server-side curl should still receive HTML. Include the cookie for closer browser parity.

## Good deep-dive page structure

- Breadcrumb back to wiki and parent hub.
- Short thesis/summary box.
- Evidence-backed local demand signals.
- Acquisition/filter criteria.
- Target niche ranking.
- Playbook / operating improvements.
- Diligence questions.
- Search strategy.
- Sources.
- Created/updated note with confidence level.
