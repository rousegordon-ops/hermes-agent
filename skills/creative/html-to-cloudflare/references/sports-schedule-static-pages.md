# Sports schedule static pages

Use this when Gordon asks for a public schedule page for a major sports event.

## Proven source pattern

For FIFA World Cup 2026, ESPN's public scoreboard API returned all 104 events with UTC kickoff timestamps, teams, venue, city/country, stage slug, broadcasts, and game IDs:

```text
https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260611-20260719&limit=200
```

Useful event fields:
- `event.date` — UTC ISO timestamp; convert with Python `zoneinfo`.
- `event.season.slug` — stage, e.g. `group-stage`, `round-of-32`, `final`.
- `event.competitions[0].venue.fullName` and `.address.city/.country` — stadium/location.
- `event.competitions[0].competitors[]` — teams; use `homeAway` for home/away ordering.
- `event.competitions[0].broadcasts[].names` — TV/streaming labels.
- `event.id` — build ESPN match link: `https://www.espn.com/soccer/match/_/gameId/<id>`.

Cross-check against the official FIFA schedule announcement/PDF before publishing, especially match count and opening/final details.

## Kalshi / betting line enrichment

For World Cup match winner markets, Kalshi's public unauthenticated API worked with:

```text
https://external-api.kalshi.com/trade-api/v2/markets?status=open&limit=100&series_ticker=KXWCGAME
```

The response is paginated with `cursor`; fetch all pages. Group rows by `event_ticker`; each group has three binary markets for team A, tie, team B. Useful fields:
- `title` — e.g. `Congo DR vs Uzbekistan Winner?`.
- `yes_sub_title` — outcome label (`Congo DR`, `Tie`, `Uzbekistan`).
- `yes_bid_dollars`, `yes_ask_dollars`, `last_price_dollars` — decimal dollar probabilities; display as cents/ranges (`30–31¢`).

Match names may differ between sources. Normalize before matching:
- `Korea Republic` ↔ `South Korea`
- `IR Iran` ↔ `Iran`
- `USA` / `US` ↔ `United States`
- `Bosnia and Herzegovina` ↔ `Bosnia-Herzegovina`
- `DR Congo` ↔ `Congo DR`
- remove accents for names such as `Curaçao`.

Only group-stage matchups have known teams; knockout placeholders should show `Kalshi: not posted yet` or similar until markets exist. Add a footer/source note that lines are a point-in-time snapshot, because static pages will stale unless regenerated.

## Timezone conversion

Use Python, not mental math:

```python
from datetime import datetime
from zoneinfo import ZoneInfo
pt = ZoneInfo('America/Los_Angeles')
dt_pt = datetime.fromisoformat(utc.replace('Z', '+00:00')).astimezone(pt)
```

For June/July events, the actual abbreviation is PDT. If the user asks for PST/Pacific, label the main UI as `PT` for readability and optionally note that summer dates are PDT.

## Group / pool enrichment

For tournament schedules with fixed groups/pools, add group data as a first-class facet rather than hiding it in generic stage text.

For FIFA World Cup 2026, Olympics.com listed the groups clearly:
- Group A — Mexico, South Africa, Czechia, South Korea
- Group B — Bosnia-Herzegovina, Canada, Qatar, Switzerland
- Group C — Brazil, Haiti, Morocco, Scotland
- Group D — Australia, Paraguay, Türkiye, United States
- Group E — Curaçao, Ecuador, Germany, Ivory Coast
- Group F — Japan, Netherlands, Sweden, Tunisia
- Group G — Belgium, Egypt, Iran, New Zealand
- Group H — Spain, Cape Verde, Saudi Arabia, Uruguay
- Group I — France, Senegal, Iraq, Norway
- Group J — Argentina, Algeria, Austria, Jordan
- Group K — Portugal, Congo DR, Uzbekistan, Colombia
- Group L — England, Croatia, Ghana, Panama

Implementation pattern:
- Create a `team_to_group` mapping from the group list and assign each group-stage match by splitting `match` on `vs`. Verify both teams resolve to the same group.
- Add `data-group="Group X"` to each group-stage `.game-card`; use `data-group=""` for knockout placeholders so JS filtering stays simple.
- Add a visible group pill next to `Group Stage`, e.g. `<span class="group-pill">Group A</span>Group Stage`.
- Add a `Groups` section with one clickable card per group, showing all teams.
- Add an `All groups` select in the sticky controls; group filtering must compose with team regex, venue regex, stage, and city filters.
- Add the group to the card/search haystack so a broad text search can also find it if applicable.
- Include the group source in the footer/source note.

Verification additions:
```python
assert s.count('class="group-card"') == 12
assert s.count('class="group-pill"') == 72  # World Cup group-stage matches
assert '<select id="group">' in s and 'okGroup' in s
assert 'Mexico · South Africa · Czechia · South Korea' in s
```

## Updating completed and in-progress games / scores

For static sports schedule pages that already list future fixtures, do not guess scores from snippets. Query the page's authoritative/public schedule source when possible. For ESPN-backed soccer pages, the public scoreboard endpoint works well:

```python
import json, urllib.request
url = 'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260611'
data = json.loads(urllib.request.urlopen(
    urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=20
).read())
for ev in data.get('events', []):
    comp = ev['competitions'][0]
    status = comp['status']['type']
    if status.get('completed'):
        print(ev['id'], ev['name'], status.get('description'))
        for c in comp['competitors']:
            print(c.get('homeAway'), c['team']['displayName'], c.get('score'), c.get('winner'))
```

Patch completed and in-progress events from the authoritative status data:
- For completed games, add `class="game-card completed"` and use structured final-result markup rather than a plain text blob.
- Completed-game cards should be compact: visible matchup, group/stage, and the final result only. Remove/hide kickoff time, venue/location, broadcaster, and betting/market lines unless Gordon explicitly asks to keep them.
- Prefer `.result-card` rows with a highlighted `.winner` and dimmed `.loser`; do **not** strike through the losing team.
- For in-progress games, add an `in-progress` class, a high-contrast live badge such as `LIVE · 16'`, and a `.result-card` with current scores for both teams. Keep the scheduled kickoff/location/TV/line fields unless the user asks to simplify live cards.
- Put live-score markup inside the `.match` block when the top “today’s games” card copies schedule-card `innerHTML`; otherwise the copied card may show the live score in an awkward column or miss the status styling.
- When rewriting an existing live `.match` block, do **not** use a generic non-greedy regex like `<div class="match">.*?</div>` because the result card contains nested `<div>` rows; that can leave duplicate score rows behind. Replace from the top-level `<div class="match">` through the next top-level sibling (`place`, `tv`, or `kalshi`) or use an HTML parser.
- When mirroring canonical schedule cards into top cards, propagate both `completed` and `in-progress` status classes:
  ```js
  const statusClass = card.classList.contains('completed') ? ' completed' : (card.classList.contains('in-progress') ? ' in-progress' : '');
  ```
- Preserve expected total event count (`class="game-card"`) exactly.

If the page has started and should stay current, create a small updater script outside the repo (e.g. `/opt/data/scripts/update_wc_results.py`) that fetches the authoritative scoreboard, rewrites newly completed cards and currently in-progress cards, refreshes all Kalshi odds for still-scheduled games with currently open markets, commits/pushes/deploys only when content changes, and verifies the canonical URL. Schedule it through the tournament window (e.g. every 30 minutes) rather than relying on client-side API calls from a static page. Gordon explicitly wants Kalshi odds refreshed whenever WC results are updated.

After editing, verify:
- Score labels/result rows expected are present exactly once.
- `class="game-card"` count is unchanged.
- Completed cards no longer expose stale logistics/market lines.
- In-progress cards expose a live badge, both team names, and both current scores.
- If the page has a top “today’s games” card that copies schedule-card HTML, run a rendered-DOM check (jsdom is fine when Chrome is unavailable) and assert the today card contains the live badge/minute and score text.
- Live canonical URL contains the scores after Wrangler deploy.

## Page pattern

Good structure for a standalone schedule/results page:
- If Gordon wants a minimal utility page, avoid a bulky hero/stat block; a simple top-level title such as `<h1 class="page-title">2026 World Cup</h1>` plus a Today’s games card is enough.
- Put a `Today’s games` card near the top, populated from existing embedded schedule data using the current Pacific date; keep it static-client-side and verify it does not break inline JS.
  - If Gordon asks for today’s games to include “the same info” as the schedule cards below, render today entries by locating the matching underlying `.game-card` (via ESPN/game ID link) and copying its `innerHTML` into a `.today-schedule-game` wrapper. This avoids drift and automatically includes kickoff, matchup, group/stage, stadium/location, TV, Kalshi lines, or final-result markup as the source card changes.
  - For follow-on summary cards like `Next USA game`, reuse the same canonical-card-copy pattern instead of hand-authoring duplicate markup: find the first scheduleData event whose match contains the target team and whose source `.game-card` is not `.completed`, then copy that card’s `innerHTML` into the top card. Set the header metadata from `date_label` and `time_label` (e.g. `Thu, Jun 18 · 12:00 PM PT`) and show a concise empty state if no upcoming team game exists.
  - Add CSS so `.today-schedule-game` mirrors the `.game-card` grid columns, and make the mobile media query apply to both `.game-card` and `.today-schedule-game`.
- Label the main listing `Schedule & Results` once games have started.
- Collapse large filter/reference sections (host locations, groups, stages) by default with native `<details><summary>…</summary>` arrows.
- For tournaments with groups/pools, show a dedicated groups section, a group dropdown, clickable group cards, and visible group labels on each group-stage game.
- Prefer separate regex search fields when the data has natural facets, especially sports schedules:
  - `Team regex…` filters only team/match text and has a team/match suggestion dropdown.
  - `Venue regex…` filters only stadium/location text and has a stadium/location suggestion dropdown.
  - Compile each input with `new RegExp(raw, 'i')`; show an inline invalid-regex error instead of throwing.
  - Dropdowns should update while typing, highlight the matching text, and let clicks populate the escaped literal value.
  - Filters must compose with each other and with city/stage chips.
- Filter chips for host locations and stages.
- For long event lists, group games by day using separate visible day boxes, not a single table with ambiguous separator rows. Each day should be its own bordered section (`.day-group`) containing that day’s `.game-card` entries; the date header applies to the games inside the box. Do not add directional arrows once boxed.
- Responsive cards: date/time, match, location, TV/streaming, and optional market/line data. Avoid wide tables for user-facing mobile schedules.
- High-contrast dark theme for readability.

## Verification checklist

Before commit/deploy:

```python
s = open('/opt/data/hermes-pages/<page>.html', encoding='utf-8').read()
assert '<expected opening match>' in s
assert '<expected PT kickoff>' in s
# Use whichever structure the page uses:
assert s.count('<tr data-stage=') == <expected_match_count> or s.count('class="game-card"') == <expected_match_count>
# If grouped by day:
assert 'class="day-group"' in s
# If enriched with market lines:
assert s.count('class="kalshi"') in (0, <expected_match_count>)
```

If the page includes inline JavaScript, extract the functional script and run a syntax check before commit:

```bash
python3 - <<'PY'
from html.parser import HTMLParser
from pathlib import Path
class P(HTMLParser):
    def __init__(self): super().__init__(); self.in_script=False; self.buf=[]; self.scripts=[]
    def handle_starttag(self, tag, attrs):
        if tag == 'script': self.in_script=True; self.buf=[]
    def handle_endtag(self, tag):
        if tag == 'script' and self.in_script:
            self.scripts.append(''.join(self.buf)); self.in_script=False
    def handle_data(self, data):
        if self.in_script: self.buf.append(data)
p = P(); p.feed(Path('/opt/data/hermes-pages/<page>.html').read_text())
Path('/tmp/<page>-script.js').write_text(p.scripts[-1])
PY
node --check /tmp/<page>-script.js
```

After Wrangler deploy, verify canonical URL, not just preview URL:

```python
import urllib.request
url = 'https://hermes-pages-d55.pages.dev/<page>'
html = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=40).read().decode('utf-8','replace')
assert '<expected opening match>' in html
assert html.count('<tr data-stage=') == <expected_match_count> or html.count('class="game-card"') == <expected_match_count>
# If the page uses separate regex fields:
assert 'id="teamQ"' in html and 'id="venueQ"' in html
# If grouped by day or enriched with lines:
assert html.count('class="day-group"') >= 1
assert html.count('class="kalshi"') in (0, <expected_match_count>)
```

If an important feature is client-rendered (for example the `Today’s games` card), verify the rendered DOM too, not just raw HTML. A simple pattern is to install/use `jsdom` in `/tmp`, execute the live page script, and count the expected rendered subfields (date/time, match, place, TV, Kalshi/result) inside `#todayGames`. Avoid relying on browser automation if local Chrome is unavailable; raw fetch plus `jsdom` is sufficient for this class of static page.
