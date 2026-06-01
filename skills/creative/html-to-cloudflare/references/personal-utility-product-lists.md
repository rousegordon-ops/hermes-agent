# Personal utility product lists

Session-specific notes for maintaining Gordon's lightweight product-list pages on `hermes-pages`, especially the bathroom vanity lights list.

## Bathroom vanity lights command semantics

Primary current command:
- `add light <URL>`

Legacy commands may appear in older chat/context, but the public page instruction should say `add light <URL>`, not `add vanity <URL>`. The page title should be **Bathroom Vanity Lights**.

Canonical source and URL:
- Source: `/opt/data/hermes-pages/bathroom-vanity-lights.html`
- URL: `https://hermes-pages-d55.pages.dev/bathroom-vanity-lights`

Older names/paths like `/bathroom-vanities` and “Bathroom Vanities” are stale for this list unless Gordon explicitly asks for a redirect/backcompat fix.

## Required output per item

- Keep the original user-supplied URL as the product link.
- Save a local image under `/opt/data/hermes-pages/assets/` with a descriptive stable filename.
- Add useful metadata when available: price, dimensions, finish, specs.
- Do not add wiki auth or redirect snippets to this root-level utility page.
- Before commit, grep/read the actual HTML on disk and assert the new item text and image filename are present.

## Fetching metadata/images

Preferred source order:
1. Product page JSON-LD / Open Graph metadata.
2. Shopify product endpoint (`/products/<handle>.js`) or variant JSON-LD (`hasVariant`) when available.
3. Search/extract fallback using model/item number and product title.
4. Reseller mirror pages for specs/images when the original site blocks fetches.

Examples from sessions:
- Home Depot blocked direct Python fetch with `403`. `web_search` found a PrairieGrit mirror for model `21191` / item `316720475`, which provided a product image and specifications; keep the Home Depot URL as the actual card link.
- Home Depot ORGANNICE item `334843856` / model `R-B12191MB-LED` also blocked direct fetch. Search found an equivalent/similar Toolkiss Shopify product (`square-framed-bathroom-wall-mirrors-aluminum-frame-horizontal-vertical-copy-1`) with `/products/...js` metadata. The variant `B12191MB-LED` exposed price `$468`, dimensions `48'' x 36''`, and image `B12191MB-LED.jpg`; however vision check said that specific image was a cropped/detail shot with logo overlays. A lifestyle image (`11_2fc08f57...jpg`) was less product-isolated but clearer for the card. Keep the original Home Depot URL as the link and label any mirror-derived price as from the similar listing.
- LightsLux Shopify page exposed JSON-LD and many images. The selected variant had price `$109.99`, size `60CM(23.6")`, color `Coffee`, warm white `3000K`. A variant image was cropped/poor; the Open Graph image was visually verified as a better product-card image.
- Lamps Plus blocked direct Python fetch with `403`, but `web_extract` could read the page enough for title/description and `web_search` found specs. An ET2/Lighting New York mirror (`et2lightinglights.com`) for `E23423-PC` exposed JSON-LD, full specs, and downloadable product images. Use the mirror for metadata/images but keep Gordon's original Lamps Plus URL as the card link.
- LBC Lighting Shopify product pages can be fetched directly. For `kuz-vl62224`, JSON-LD exposed rich HTML specs and variant pricing; variant snippets in the page exposed Black/Chrome SKUs (`VL62224-BK`, `VL62224-CH`) and prices. Product images from Shopify CDN may be small but visually usable; verify before saving.
- Lumens may block direct fetch (`403` / empty `web_extract`). For Modern Forms Vogue, use search results plus reseller/manufacturer pages. 2Modern exposes a Shopify JSON endpoint at `https://www.2modern.com/products/vogue-bathroom-vanity-wall-light.js`, including variants, prices (`$317–$477`), finish/size/CCT options, and Shopify CDN images. Download the selected image locally and visually verify it.

## User interruption / stop signal

If Gordon says `stop` while a page-update workflow is in progress, stop immediately and do not continue executing or narrating planned page changes. Treat it as a hard interruption, not as a cue to keep working from prior context.

## Recessed gimbal lights command semantics

Primary current command:
- `add gimbal <URL>`

Canonical source and URL:
- Source: `/opt/data/hermes-pages/recessed-gimbal-lights.html`
- URL: `https://hermes-pages-d55.pages.dev/recessed-gimbal-lights`

This page is for recessed gimbal lights to illuminate art on walls. For each new product, prioritize metadata that matters for art lighting:
- CRI / color quality (high CRI is important)
- Tilt/rotation adjustability angle
- Beam spread / beam angle
- Whether beam spread is fixed or controllable
- Whether it uses a swappable MR16/GU10-style lamp (beam can be changed by bulb choice) or an integrated LED module
- Cost, aperture/trim size, finish, dimming, CCT, and installation notes

Add objects to `window.__GIMBALS` with fields: `name`, `url`, `img`, `price`, `dimensions`, `finish`, `cri`, `adjustability`, `beam`, `lamp`, `specs`, and `artFit` when available. Save images locally under `/opt/data/hermes-pages/assets/`, visually verify clear product images when possible, commit, deploy, and verify the canonical URL contains the new product and image filename.

## Multiple URLs in one command

If Gordon says `add light <URL> <URL>` or `add gimbal <URL> <URL>` (or more URLs), do **not** spawn parallel agents against the shared HTML file. Fetch metadata/images for each URL serially, then patch the appropriate JS data array once, commit once, deploy once, and verify every new item/image on the canonical page.

## Page UI/legibility

Gordon reported that on phone the association between product pictures and descriptions was not clear. Maintain strong card separation on mobile and desktop: high-contrast borders around each product card, generous vertical spacing between cards, and a clear border between the image and the description when stacked. Avoid subtle low-contrast separators for substantive product grouping.

## Image verification

Use vision analysis when available. If the first candidate is cropped, mostly blank, off-center, or not clearly the product, try another candidate before committing.

## Deploy verification

Cloudflare Pages auto-deploy has lagged repeatedly for this page. After push, verify the canonical URL contains the new item text and local image filename. If the live page is stale after 60+ seconds of retries, a forced deploy is needed.

**If Node 22+ is available** (wrangler requires it — system node may be older):
```bash
npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages --commit-dirty=true
```
If the worktree has unrelated dirty files, deploy from an isolated clean clone:
```bash
rm -rf /tmp/hermes-pages-vanity-lights-deploy
git clone --no-local /opt/data/hermes-pages /tmp/hermes-pages-vanity-lights-deploy
npx -y -p node@22 -p wrangler wrangler pages deploy /tmp/hermes-pages-vanity-lights-deploy --project-name hermes-pages --commit-dirty=true
```

**If only Node 20 is available** (current wrangler may not run): there is no CLI recovery. The content is committed to GitHub and will go live when CF eventually picks up the push. Tell Gordon the content is committed and deployment is pending.

**Verification pattern** — always check the committed state, not just the live URL:
```python
import subprocess, urllib.request
# 1. Confirm commit
r = subprocess.run(['git', 'log', '--oneline', '-1'], cwd='/opt/data/hermes-pages', capture_output=True, text=True)
print('commit:', r.stdout.strip())
# 2. Check live
url = 'https://hermes-pages-d55.pages.dev/bathroom-vanity-lights'
html = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'}), timeout=20).read().decode('utf-8', 'replace')
print('new item in live:', 'EXPECTED PRODUCT NAME' in html)
```
If the commit is there but the live page is stale, CF missed the webhook — force a deploy or wait.
