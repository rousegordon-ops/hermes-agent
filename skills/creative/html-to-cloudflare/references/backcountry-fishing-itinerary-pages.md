# Backcountry fishing itinerary wiki pages

Use when Gordon asks for a separate web/wiki page for a backcountry fishing destination candidate, especially Sierra trout trips.

## Content pattern

- Create a public-by-default page under `/opt/data/hermes-pages/wiki/hobbies/<destination-slug>.html` unless Gordon explicitly asks for privacy.
- Keep it practical and trip-planning oriented, not a generic destination article.
- Include:
  - concise fit statement against Gordon's benchmark: steep remote creek/plunge-pool canyon vs timberline/alpine/meadow variant;
  - quick facts box: trailhead, route, permit, fishing style, trip length, verdict;
  - proposed itinerary with nights/days separated;
  - planning cautions: permits, current road/snow, fire restrictions, bear canister/food storage, fishing regulations;
  - sources and image credits;
  - backlink to `/wiki/hobbies/backcountry-fishing`.
- If the destination already appears on Backcountry Fishing, update that list item to link to the new detailed page.
- Add the new page to the Hobbies section of `/opt/data/hermes-pages/wiki/index.html` using an extensionless URL.

## Research sources

Prefer authoritative sources for logistics and species claims:
- USDA Forest Service trailhead/trail/wilderness pages for trailheads, restrictions, water, quotas, campfire rules, road season, and bear storage.
- CDFW pages for fish species/native range/conservation facts.
- Recreation.gov only for permit links when agency pages point there.
- Use hiking blogs/trip reports only for qualitative route feel; avoid presenting user trip reports as authoritative regulations.

## Images and diagrams

- Download local copies under `/opt/data/hermes-pages/wiki/assets/<destination-slug>/`; do not hotlink.
- Wikimedia Commons API is useful for candidate images and metadata. Search `generator=search` in namespace 6, then fetch `imageinfo` with `iiprop=url|extmetadata` and a thumbnail width.
- Wikimedia downloads can return HTTP 429. Retry with backoff and a descriptive User-Agent; if one image fails, continue with the usable images rather than blocking the page.
- Visually verify images when possible. Use captions that do not overclaim; e.g. distinguish a lake/basin image from the actual creek if it is only representative.
- For route clarity, a local conceptual SVG is often better than a questionable map screenshot. Label it explicitly as a planning sketch / not a navigation map.

## Verification checklist

Before commit:
- Parse the HTML files with Python `html.parser`.
- Assert the new page contains the expected `<h1>`, itinerary heading, local asset paths, and no `wiki_auth` / `/wiki/login?dst=` unless explicitly private.
- Assert the Hobbies index contains the extensionless link.
- Assert the Backcountry Fishing page links to the new detail page when relevant.
- Assert each local asset exists and has nonzero size.
- Run `git diff --check`.

Publish and verify:
- Commit page, index, updated Backcountry Fishing page, and assets.
- Push with `GIT_TERMINAL_PROMPT=0`.
- Deploy with Wrangler Direct Upload: `npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages --commit-dirty=true`.
- Fetch canonical URLs with `Cache-Control: no-cache` and verify page text, index link, backlink, and asset URLs.
- If a HEAD/content-type check looks odd, fetch a byte sample; Cloudflare can still serve image bytes correctly even if an initial metadata read is misleading.