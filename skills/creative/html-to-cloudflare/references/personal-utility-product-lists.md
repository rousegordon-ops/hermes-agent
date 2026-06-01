# Personal utility product lists

Session-specific notes for maintaining Gordon's lightweight product-list pages on `hermes-pages`, especially `/bathroom-vanities`.

## Bathroom vanities command semantics

Treat these as equivalent:
- `store vanity <URL>`
- `add vanity <URL>`

Add the product to `/opt/data/hermes-pages/bathroom-vanities.html` and deploy to `https://hermes-pages-d55.pages.dev/bathroom-vanities`.

## Required output per item

- Keep the original user-supplied URL as the product link.
- Save a local image under `/opt/data/hermes-pages/assets/` with a descriptive stable filename.
- Add useful metadata when available: price, dimensions, finish, specs.
- Do not add wiki auth or redirect snippets to this root-level utility page.

## Fetching metadata/images

Preferred source order:
1. Product page JSON-LD / Open Graph metadata.
2. Shopify variant JSON-LD (`hasVariant`) when the URL has a `variant=` parameter.
3. Search/extract fallback using model/item number and product title.
4. Reseller mirror pages for specs/images when the original site blocks fetches.

Examples from session:
- Home Depot blocked direct Python fetch with `403`. `web_search` found a PrairieGrit mirror for model `21191` / item `316720475`, which provided a product image and specifications; keep the Home Depot URL as the actual card link.
- LightsLux Shopify page exposed JSON-LD and many images. The selected variant had price `$109.99`, size `60CM(23.6")`, color `Coffee`, warm white `3000K`. A variant image was cropped/poor; the Open Graph image was visually verified as a better product-card image.

## Image verification

Use vision analysis when available. If the first candidate is cropped, mostly blank, off-center, or not clearly the product, try another candidate before committing.

## Deploy verification

Cloudflare Pages auto-deploy has lagged repeatedly for this page. After push:
- Verify the canonical URL contains the new item text and local image filename.
- Verify the image URL returns 200 and an image content type.
- If stale after retries, deploy a clean committed clone:

```bash
rm -rf /tmp/hermes-pages-vanities-deploy
git clone --no-local /opt/data/hermes-pages /tmp/hermes-pages-vanities-deploy
npx -y -p node@22 -p wrangler wrangler pages deploy /tmp/hermes-pages-vanities-deploy --project-name hermes-pages --commit-dirty=true
```

This avoids deploying unrelated dirty files from `/opt/data/hermes-pages`.
