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
- Amazon product pages may fail via `web_extract`, but a direct Python `urllib.request` fetch with browser-like `User-Agent` and `Accept-Language` can still return the full HTML. For ASIN `B0DC6D2VDK`, this exposed `#productTitle`, feature bullets, `displayPrice`, and image-block JSON fields such as `landingImage` / `colorImages` with `hiRes` image URLs. Extract title from `id="productTitle"`, price from `"displayPrice":"..."` or first `a-price` offscreen value, bullets from `id="feature-bullets"`, and product images from `"hiRes":"https://m.media-amazon.com/..."`. Download the chosen `m.media-amazon.com` image locally and visually verify it before adding the card. Note Amazon may localize currency based on fetch context. Gordon wants product-list prices in US dollars with no source/explanation text in the price field. Prefer a US retailer/search-result price; otherwise convert from the fetched currency using a current rate and publish only the estimated dollar amount (e.g. `$52.70`).

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

## Showerheads command semantics

Primary current command:
- `add showerhead <URL or product name>`

Canonical source and URL:
- Source: `/opt/data/hermes-pages/showerheads.html`
- URL: `https://hermes-pages-d55.pages.dev/showerheads`

This page is for showerheads being considered for the Ventura house. If Gordon provides a product name instead of a URL, search the web for the product, choose the most likely official/retailer URL, and keep that as the card link. For each new product, prioritize metadata that matters for showerheads:
- Flow rate / GPM
- Spray patterns and pressure feel
- Fixed, handheld, rain, dual, filtered, or combo type
- Finish and dimensions / face diameter
- Installation notes and compatibility with standard shower arms/valves
- Anti-clog / easy-clean nozzles, filter cartridges, pause controls, hose length where relevant
- Certifications such as WaterSense, ASME/CSA, CEC/California compliance when available

Add objects to `window.__SHOWERHEADS` with fields: `name`, `url`, `img`, `price`, `type`, `flow`, `spray`, `dimensions`, `finish`, `install`, `certifications`, `specs`, and `fitNote` when available. Save images locally under `/opt/data/hermes-pages/assets/`, visually verify clear product images when possible, commit, deploy, and verify the canonical URL contains the new product and image filename.

### Showerhead provider notes

Moen showerheads:
- If Gordon provides a Build/Ferguson `bci...` item ID with a model (example `bci4093471`, `6345EPBN`), the likely Ferguson/Build URL pattern is `https://www.fergusonhome.com/moen-6345ep/s1488769?uid=4093471`; direct Python fetch may return `403`, but the URL is still a useful original card link.
- Moen official Shopify-style pages can be readable via `web_extract`, e.g. `https://shop.moen.com/products/6345` or `/products/6345ep`, and expose Widen CDN product/lifestyle images plus Moen web/list prices. Watch variant/finish: `/products/6345ep` may default to matte black (`6345EPBL`) even when Gordon asked for brushed nickel (`6345EPBN`). Use finish-specific image filenames from Moen assets when available, e.g. `6345bn_set1.tif` / `6345bn_set2.tif` for brushed nickel lifestyle images.
- Moen product-spec PDFs are often at `https://assets.moen.com/shared/docs/product-specifications/<series>sp.pdf` and extract well. For 6345 series, the PDF gave: single-function rainfall showerhead, 8" diameter, nonmetallic spray face/shell, brass swivel ball, EP models after 2018 = 1.75 GPM / 6.7 LPM max, WaterSense, ASME A112.18.1 / CSA B125.1.
- Amazon pages for Moen may fetch with browser-like `urllib` even when `web_extract` fails. For ASIN `B07QPC1X4Z`, Amazon exposed a clean primary image `71E8NidfyIL._AC_SL1500_.jpg` that was better for the card than Moen lifestyle images with black bars. Amazon prices can localize to EUR in this environment; if using price snippets from search/eBay, label the source clearly.

## Multiple URLs in one command

If Gordon says `add light <URL> <URL>`, `add gimbal <URL> <URL>`, or `add showerhead <URL/name> <URL/name>` (or more items), do **not** spawn parallel agents against the shared HTML file. Fetch metadata/images for each item serially, then patch the appropriate JS data array once, commit once, deploy once, and verify every new item/image on the canonical page.

## Recessed gimbal provider notes

ELCO product pages (`elcolighting.com`) extract text and image URLs well via `web_extract`, but direct image download from the official CDN may return `403` even with browser-like headers. Use reseller mirrors when needed:
- BuyRite product handles expose Shopify JSON at `/products/<handle>.js` with title, price, and image URLs.
- Example ELCO images/prices recovered from BuyRite/Shopify endpoints:
  - `EL2620W` slot aperture trim: ~$25.13, image `EL2620W.jpg`.
  - `EL2622W/B` wall-wash reflector: ~$23.73–$53.40, image `EL2622B.jpg`/`EL2622W` mirrors.
  - `EL2688W` pull-down trim: ~$27.93–$33.15, image `EL2688W.jpg`.
  - `EL2695W` scoop/baffle wall wash: ~$19.99–$22.65, image `EL2695W.jpg`.
- ELCO 3" Alpine trims are often *trim + housing + lamp* systems, not complete integrated LED fixtures. For artwork, state explicitly that CRI/CCT/beam spread depend on the selected MR16/GU10/PSA37 lamp. This is not a downside if Gordon wants beam-spread control by swapping bulbs.
- ELCO integrated pull-down inserts (example: `3-round-integrated-led-adjustable-pull-down-insert`, SKUs `EL39730W`/`EL39727BZ`) are different from the MR16/GU10 trims: integrated 10.8W LED, 800 lm, 93+ CRI, 36° fixed beam, 65° tilt, 356° rotation, Triac/ELV dimming, damp rated, Energy Star/Title 24. For art lighting, call out the tradeoff: strong CRI and aiming range, but beam spread is fixed and not bulb-swappable. Direct ELCO image downloads may 403; `web_extract` can read specs/PDF text, and reseller mirrors like Cans & Fans / Sonic Electric / USA Light can provide usable product images and prices (`$97.35–$126` seen). Example local image filename: `gimbal-elco-el39730w-integrated-led-pull-down-insert.jpg`.
- ELCO EL2677 fully retractable pull-down trim (`3-die-cast-fully-retractable-pull-down-trim-0`) is the 3" MR16 option with 60°+ aiming: 80° adjustability, 358° rotation, replaceable GU5.3 bi-pin MR16 lamp, 4 5/16" O.D., compatible with 3" low-voltage housings. Finish options found: black, clear/chrome, gold — no white. BuyRite mirror has usable product page/image (`EL2677C.jpg`); direct ELCO image may 403. Example local filename: `gimbal-elco-el2677c-fully-retractable-mr16-pull-down-trim.jpg`. Gordon disliked its appearance.
- Better ELCO alternatives found after EL2677 aesthetic complaint: EL2396W (`3-square-adjustable-pull-down-trim`) is a 3" all-white square pull-down MR16/PSA37 trim with 87° tilt/358° rotation, looks cleaner but square. EL1497W (`4-adjustable-pull-down-trim`) is a 4" all-white round pull-down MR16/PSA37 trim with 0–90° tilt/359° rotation and visually closest to EL39730W, but not 3".
- Useful fields from ELCO/resellers: outside diameter typically `4 5/16"` for Alpine trims; EL397 integrated insert outside diameter `4 3/8"`, max height `6 1/8"`; EL2622 wall-wash reflector has `45° adjustability, 359° rotation`; EL2688 pull-down has `30° adjustability, 358° rotation`; EL2677 fully retractable pull-down has `80° adjustability, 358° rotation`; EL2396W square pull-down has `87° tilt, 358° rotation`; EL1497W 4" round pull-down has `0–90° tilt, 359° rotation`; EL2620 slot aperture has `45° adjustability`.

## Page UI/legibility

Gordon reported that on phone the association between product pictures and descriptions was not clear. Maintain strong card separation on mobile and desktop: high-contrast borders around each product card, generous vertical gaps between cards, and a clear border between the image and the description when stacked. Avoid subtle low-contrast separators for substantive product grouping.

## Image verification and multi-image cards

Use vision analysis when available. If the first candidate is cropped, mostly blank, off-center, or not clearly the product, try another candidate before committing.

When Gordon asks to **add a picture** to an existing card, preserve the existing product image unless he explicitly says replace. Add a multi-image field/render path (e.g. `images: [existing, new]`) and verify both image paths render/live. This correction came up on the FRIHULT card: replacing the product photo with an inspiration photo was wrong; the desired outcome was two pictures.

For wide/lifestyle/inspiration images inside product cards, avoid cropping important context. Use `object-fit: contain` and `object-position: center center` for the added/lifestyle image if `cover` cuts off the side of the image. Keep card boundaries and image/detail separators high contrast.

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
