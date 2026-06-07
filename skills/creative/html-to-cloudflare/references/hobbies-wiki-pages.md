# Hobbies wiki page creation notes

Use this when Gordon asks for a new page under `wiki/hobbies/`, especially a practical how-to page with images/illustrations.

## Proven workflow from lemon tree cuttings page

- Create hand-edited HTML directly under `/opt/data/hermes-pages/wiki/hobbies/<slug>.html`; do not use the retired markdown pipeline.
- **Default public:** new and updated hobby/travel pages should be publicly accessible unless Gordon specifically requests private/auth-gated access.
  - Do **not** add the wiki auth guard by default.
  - If an existing page has the `wiki_auth` script and Gordon asks to publish/share/make it public, remove that script and verify `wiki_auth` and `/wiki/login?dst=` are absent.
  - Only add or preserve the auth guard when Gordon explicitly asks for the page to stay private/protected.
- Add a link in `/opt/data/hermes-pages/wiki/index.html` under the existing **Hobbies** section. Use extensionless URLs, e.g. `/wiki/hobbies/lemon-tree-cuttings`.
- Use high-contrast dark styling consistent with existing wiki pages; avoid dim gray for substantive text.
- For practical/how-to pages, a richer page layout is OK: hero image, quick recipe/callout, step cards, supplies checklist, sources, and image credits.
- If exact method/product photos are hard to find, combine:
  - Wikimedia Commons or other permissively reusable images for concepts/products (e.g. lemon tree, roots, perlite).
  - A custom local SVG under `/wiki/assets/` for the actual method sequence.
- Download reusable images locally under `/opt/data/hermes-pages/wiki/assets/` rather than hotlinking. Record credits/licenses in the page.
- Visually verify downloaded images when possible; if an image is only conceptually useful, caption it clearly rather than overselling it.

## Verification checklist

Before commit:
- Assert page contains expected `<h1>`, local asset paths, and key user-provided content.
- Assert public/default pages do **not** contain `wiki_auth` or `/wiki/login?dst=`; if Gordon explicitly requested a private page, assert the auth guard is present instead.
- Assert the wiki index contains the new extensionless link.
- Assert each local asset exists and has nonzero size.
- Run `git diff --check`.

Publish:
- Commit page, index, and assets.
- Push to GitHub for source backup.
- Deploy with Wrangler because `hermes-pages` uses Direct Upload:
  `npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages --commit-dirty=true`

Live verification:
- Fetch `https://hermes-pages-d55.pages.dev/wiki/hobbies/<slug>` and check expected title/content and asset filenames.
- Fetch `/wiki/index.html` and check the new Hobbies link.
- Fetch local asset URLs and verify HTTP 200 plus expected content type/length.
