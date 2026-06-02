# Bathroom vanities utility page notes

Session-derived details for maintaining Gordon's lightweight bathroom vanity list on hermes-pages.

## Canonical page

- Source: `/opt/data/hermes-pages/bathroom-vanities.html`
- Live URL: `https://hermes-pages-d55.pages.dev/bathroom-vanities`
- Accepted commands: `store vanity <URL>` and `add vanity <URL>`
- Keep the page root-level/public unless Gordon explicitly asks for a proper root-scoped auth flow.

## Expected add workflow

1. Fetch product metadata from the supplied URL: title, price, dimensions, finish, specs, image candidates.
2. Prefer Open Graph/product JSON-LD image. If blocked, use web search/extract for the product ID/model and reputable mirror pages.
3. Save a product photo locally under `/opt/data/hermes-pages/assets/` with a stable name like `vanity-<brand>-<model>.jpg`.
4. If available, visually verify the image is actually the product photo before committing.
5. Append a new object to `window.__VANITIES` in `bathroom-vanities.html`; do not add wiki login/auth snippets.
6. Commit only the vanity page and new asset(s), push, deploy if needed, and verify the canonical URL includes both the new item text and image URL.

## Known quirks

- **Auto-deploy can silently fail** — GitHub push succeeds, git log confirms the commit, but the live page stays stale. This happened with WAC Lighting WS-63724 entry. Root cause: Cloudflare Pages missed the GitHub webhook trigger. Recovery:
  - If Node 22+ is available: `npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages --commit-dirty=true`
  - If only Node 20: no CLI recovery — tell Gordon the content is on GitHub and will go live when CF processes it.
  - Always verify the git commit state before assuming a deploy problem is the issue.
- Home Depot product pages may return HTTP 403 to direct Python fetches and `web_extract`; use search results and mirror/reseller pages for metadata/image, but preserve the original Home Depot URL in the card.
- Do not rely on HTTP 200 alone when Gordon says a link is broken; check auth redirects, login snippets, hub/index links, and the full click path.
