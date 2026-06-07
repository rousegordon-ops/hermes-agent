# Travel itinerary page enrichment notes

Use this when Gordon asks to make hobby/travel itinerary wiki pages more interesting or engaging.

## Pattern that worked

- Keep the existing hand-authored HTML page and wiki auth guard; enrich in place rather than creating a separate app.
- Add locally saved public-domain/Commons-style images under a topic folder such as:
  - `/opt/data/hermes-pages/wiki/assets/uk-vacation-july-26/`
- Prefer local assets over hotlinks so pages remain stable and Cloudflare serves everything from the same deploy.
- Add visual structure beyond plain lists:
  - large hero image with readable gradient overlay
  - quick-facts cards
  - mood-board photo grid with captions
  - day-by-day cards/timeline
  - playful prompts/trip games
  - local illustrative SVG route map for road trips
- Preserve substantive itinerary details and booking info already present in the page; do not expose secrets/tokens or paste sensitive values into summaries.

## Wikimedia asset download quirks

- `Special:FilePath/<filename>?width=1200` works well for downloading resized Commons images.
- URL-encode filenames, including commas, spaces, parentheses, and apostrophes.
- Wikimedia may return transient `429 Too many requests`; retry with a normal browser-ish User-Agent and exponential/backoff sleeps. Do not abandon after the first 429.
- Verify downloaded assets by checking both `Content-Type` contains `image` and size is non-trivial (>10KB for photos).
- Some plausible filenames from search results 404; use web search to find exact Commons `File:` titles, then use `Special:FilePath`.

## Verification checklist

Before commit:
- Assert each page still contains `wiki_auth` and `/wiki/login?dst=`.
- Assert new section markers exist (`Trip mood board`, `Route at a glance`, etc.).
- Assert each local asset exists and has nonzero/non-trivial size.
- Run `git diff --check`.

Publish:
- Commit page and asset changes.
- Push to GitHub.
- Deploy with Wrangler Direct Upload:
  `npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages --commit-dirty=true`

Live verification:
- Fetch canonical page URLs and assert new section text and asset filenames are present.
- Fetch image/SVG asset URLs and assert HTTP 200 plus image/SVG content type and expected content length.
