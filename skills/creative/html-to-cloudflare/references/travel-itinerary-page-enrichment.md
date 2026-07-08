# Travel itinerary page enrichment notes

Use this when Gordon asks to make hobby/travel itinerary wiki pages more interesting or engaging.

## Pattern that worked

- Keep the existing hand-authored HTML page and enrich in place rather than creating a separate app.
- **Default public:** travel itinerary pages should be public unless Gordon specifically requests private/auth-gated access.
  - Do not add a wiki auth guard to new itinerary pages by default.
  - If enriching an existing itinerary page that has `wiki_auth`, remove the auth guard unless Gordon explicitly says to keep it private.
  - Because the page is public by default, remove/redact booking confirmation numbers, reservation IDs, tokens, or other sensitive references from public text while preserving useful logistics.
- Add locally saved public-domain/Commons-style images under a topic folder such as:
  - `/opt/data/hermes-pages/wiki/assets/uk-vacation-july-26/`
- Prefer local assets over hotlinks so pages remain stable and Cloudflare serves everything from the same deploy.
- Add visual structure beyond plain lists when the page is meant to be inspirational or exploratory:
  - large hero image with readable gradient overlay
  - quick-facts cards
  - mood-board photo grid with captions
  - day-by-day cards/timeline
  - playful prompts/trip games
  - local illustrative SVG route map for road trips
- When Gordon is actively using an itinerary as an on-trip utility, bias toward a lean top section: title → `Today's itinerary` → itinerary details. If he removes top cards, mood boards, or promotional/lede copy, keep tightening rather than replacing it with new decorative content. Put practical logistics directly into the relevant day, with clear labels like `Train to Paddington`, and keep exact times only when known; use duration estimates only when they are sourced/previously verified.
- When he gives live-trip corrections or additions (e.g. “we need to check in first,” “George Square is closed,” “the drive is 3 hours, not 1.5,” or friend recommendations), patch **both** the visible day card/timeline and any `Today's itinerary` JS data object. Grep for stale place names/times across the whole file before committing; hidden JS data can keep wrong guidance alive even after visible HTML is fixed.
- If he says a recommendation is from a named friend/family member, label it explicitly in the page (e.g. `Grace rec`) and preserve that provenance in section headings/cards. Keep the user-facing itinerary terse and useful; put large recommendation banks in a separate clearly labeled section below the active day plan.
- If the itinerary includes World Cup or other sports watch windows, replace placeholder knockout labels with known team names whenever available. For `/world-cup-2026`, a reliable extraction pattern is to load the page with `jsdom`, run the bracket renderer for `Round Of 16`, and copy the resolved labels (e.g. `Brazil vs Norway`) into the travel page’s day bullets, tags, watch-notes cards, and `Today's itinerary` JS data. Remove stale placeholder wording like `R32 Match X winner` and vague `watch window` text once team names are known.
- Preserve substantive itinerary details already present in the page.
- For public pages, remove/redact sensitive booking IDs, reservation references, confirmation numbers, payment references, tokens, and credentials from user-visible HTML. Keep only non-sensitive logistics such as flight numbers, lodging names, addresses, check-in/check-out times, and whether a booking/payment is confirmed.

## Wikimedia asset download quirks

- `Special:FilePath/<filename>?width=1200` works well for downloading resized Commons images.
- URL-encode filenames, including commas, spaces, parentheses, and apostrophes.
- Wikimedia may return transient `429 Too many requests`; retry with a normal browser-ish User-Agent and exponential/backoff sleeps. Do not abandon after the first 429.
- Verify downloaded assets by checking both `Content-Type` contains `image` and size is non-trivial (>10KB for photos).
- Some plausible filenames from search results 404; use web search to find exact Commons `File:` titles, then use `Special:FilePath`.

## Updating from uploaded itinerary PDFs

When Gordon uploads a travel itinerary PDF and asks to update an existing travel page, proceed without asking what to do if the requested target page is clear from the conversation. Extract the PDF locally, merge the durable itinerary details into the hand-authored HTML, and keep the page public by default unless he explicitly requests privacy.

Recommended extraction fallback when system Python lacks `pip`/PyMuPDF:

```bash
uv run --with pymupdf python - <<'PY'
import fitz, pathlib
p = pathlib.Path('/opt/data/cache/documents/<uploaded-file>.pdf')
doc = fitz.open(p)
for i, page in enumerate(doc, 1):
    print(f'\n--- PAGE {i} ---')
    print(page.get_text('text'))
PY
```

Merge style:
- Preserve the existing page structure and visual design; patch specific day cards / planning links rather than regenerating the whole page.
- Add useful logistics, reservations, meal plans, activity options, and watch notes from the PDF.
- Redact booking/reference/confirmation identifiers from public pages. Do not include strings like `Reservation ID`, `Booking #`, `Ref #`, train/car/hotel confirmation numbers, or flight booking references; keep non-sensitive details like flight numbers, times, lodging names/addresses, reservation status, payment status, and cancellation windows.
- Verify the actual HTML file and the live page do not contain those sensitive identifiers before replying.

## Verification checklist

Before commit:
- Assert public/default pages do **not** contain `wiki_auth` or `/wiki/login?dst=`; if Gordon explicitly requested a private page, assert the auth guard is present instead.
- Assert public/default pages do not expose booking/reservation confirmation references or other sensitive identifiers. For PDF-derived itinerary updates, explicitly grep for known IDs from the PDF plus generic labels like `Reservation ID`, `Booking #`, and `Ref #`.
- Assert new section markers or inserted itinerary details exist (`Trip mood board`, `Route at a glance`, new restaurant/activity names, etc.).
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
