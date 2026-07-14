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

Only group-stage matchups have known teams at initial generation; knockout placeholders should show `Kalshi: not posted yet` or similar until markets exist. Once knockout teams resolve, the updater must map placeholder rows to real team matchups before matching Kalshi markets. For semifinals/final/third-place, prefer dynamic inference from completed semifinal result rows or ESPN scoreboard winner/loser data: final = semifinal winners, third-place = semifinal losers. Do not rely on hand-adding another override after each semifinal. Add a footer/source note that lines are a point-in-time snapshot, because static pages will stale unless regenerated.

## Timezone conversion

Use Python, not mental math:

```python
from datetime import datetime
from zoneinfo import ZoneInfo
pt = ZoneInfo('America/Los_Angeles')
dt_pt = datetime.fromisoformat(utc.replace('Z', '+00:00')).astimezone(pt)
```

For June/July events, the actual abbreviation is PDT. If the user asks for PST/Pacific, label the main UI as `PT` for readability and optionally note that summer dates are PDT.

If Gordon asks for “current user timezone” / viewer-local times, keep the embedded source data in a stable tournament/source timezone, but localize on the client with `Intl.DateTimeFormat().resolvedOptions().timeZone`. Add helpers such as `sourceEventDate(ev)`, `eventDateLabel(ev)`, `eventTimeParts(ev)`, and `localizeKickoffTimes()`; run localization before rendering mirrored top cards so copied HTML already shows local times. Today/Next-game logic should use the viewer-local event date label, not the embedded Pacific `date_label`. Verify with jsdom under a different `TZ` (e.g. `TZ=America/New_York`) that upcoming kickoff times and Next USA metadata show `EDT`, while in-progress cards still hide kickoff time.

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
- If the visible matchup/title disagrees with the live/final score rows or a screenshot correction from Gordon, treat the scoreboard team rows as the immediate truth for that event and patch every matchup surface together: link text, `data-search`, result-card `aria-label`, bracket/today-card resolved label, and any related itinerary/watch-note page that duplicated the matchup. Grep for the stale pair globally before committing so old labels do not survive in hidden JS arrays or trip notes.
- Put live-score markup inside the `.match` block when the top “today’s games” card copies schedule-card `innerHTML`; otherwise the copied card may show the live score in an awkward column or miss the status styling.
- When rewriting an existing live `.match` block, do **not** use a generic non-greedy regex like `<div class="match">.*?</div>` because the result card contains nested `<div>` rows; that can leave duplicate score rows behind. Replace from the top-level `<div class="match">` through the next top-level sibling (`place`, `tv`, or `kalshi`) or use an HTML parser.
- When mirroring canonical schedule cards into top cards, propagate both `completed` and `in-progress` status classes:
  ```js
  const statusClass = card.classList.contains('completed') ? ' completed' : (card.classList.contains('in-progress') ? ' in-progress' : '');
  ```
- Preserve expected total event count (`class="game-card"`) exactly.

If the page has started and should stay current, create a small updater script outside the repo (e.g. `/opt/data/scripts/update_wc_results.py`) that fetches the authoritative scoreboard, rewrites newly completed cards and currently in-progress cards, refreshes all Kalshi odds for still-scheduled games with currently open markets, commits/pushes/deploys only when content changes, and verifies the canonical URL. Gordon explicitly wants Kalshi odds refreshed whenever WC results are updated. For hourly sports updaters, schedule a few minutes after the hour (e.g. `5 * * * *`) so hourly-starting games become in-progress soon after kickoff without running every 15 minutes.

Client-side manual refresh on in-progress cards should update in place, not reload the page. Pattern: button click finds its own `.game-card`/`.today-schedule-game`, extracts `gameId`, fetches ESPN scoreboard for that event date with `fetch(..., { cache:'no-store' })`, updates the canonical schedule card’s `.match` block / result rows / live badge, then re-renders top mirrors (`renderTodayGames`, `renderNextUsaGame`) and standings. Do **not** set `window.location.href` for manual refresh; Gordon found page jumps to the top disorienting. Verify with jsdom that `location.href` is unchanged, the score/minute changes, buttons reset to `Refresh`, and kickoff time remains hidden on in-progress cards.

When manually editing a page that an updater cron may touch, check `git log --oneline -- <page>` and `git status --short -- <page>` immediately before committing. If an updater commit lands while you are editing, re-read the live file and verify your intended changes are still in the working tree before deploy. Deploy from an isolated clone of the committed state when unrelated files are dirty so unrelated site work is not published.

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
- Put a `Today’s games` card near the top, populated from existing embedded schedule data using the current Pacific/viewer-local date; keep it static-client-side and verify it does not break inline JS.
  - If Gordon asks for “today and tomorrow’s games,” keep the same top-card mirror pattern but build a two-date label set from `todayLabel()` and `todayLabel(new Date(Date.now() + 24 * 60 * 60 * 1000))`, filter schedule events whose viewer-local `eventDateLabel(ev)` is in that set, sort by `sourceEventDate`, and label the header `Today and tomorrow’s games`. For usability, group the mirrored cards under explicit day dividers such as `Today — Sat, Jul 4` and `Tomorrow — Sun, Jul 5`; do not also keep a redundant combined heading/date summary like `Sat, Jul 4 + Sun, Jul 5` if it makes the grouping less clear. Verify the live HTML contains the updated heading, the two-day filter logic, and rendered `.today-day-section` / `.today-day-label` groups.
  - If Gordon asks the knockout bracket to default to a later round, update both the initial active tab class in raw HTML and the JS state variable (e.g. `let activeBracketStage = 'Round Of 16';`). Verify both raw source snippets; changing only one can leave the tab highlight and rendered cards out of sync.
  - If Gordon asks for today’s games to include “the same info” as the schedule cards below, render today entries by locating the matching underlying `.game-card` (via ESPN/game ID link) and copying its content into a `.today-schedule-game` wrapper. Use a helper such as `cardContentHtml(card)` that clones the card and removes injected buttons/controls before copying; otherwise refresh buttons can duplicate or appear in mirrored top cards. This avoids drift and automatically includes kickoff, matchup, group/stage, stadium/location, TV, Kalshi lines, or final-result markup as the source card changes.
  - When copied top cards resolve a knockout placeholder matchup (e.g. `Round of 32 1 Winner vs Round of 32 3 Winner` → `Canada vs Morocco`), update *all visible matchup surfaces*, not just the link text. In `cardContentHtml(card, matchLabel)`, also rewrite `.result-card .result-team` rows from the split `matchLabel` and update the `.result-card` aria-label; otherwise mobile live-score boxes can still show placeholder winners even while the title is correct. Use `displayMatchForEvent(ev)` for every knockout stage (`ev.stage !== 'Group Stage'`), not only R32, so R16/QF/SF live refreshes resolve prior winners too.
  - If Gordon says some today games “don’t matter” or asks to highlight games that decide who advances/goes home, add a client-side stakes layer for the top card rather than hand-labeling one date. Pattern: compute current group stats from completed `.game-card.completed` result rows, enumerate outcome scenarios for each remaining group match, then for each today game compare each team’s possible statuses (`R32`, `3rd-place pool`, `Out`) under win/draw/loss plus all other remaining outcomes. Sort today’s games by stakes score before kickoff time, and add high-contrast `.stakes-high` / `.stakes-medium` styling plus a short `.stakes-note` such as “Team can advance or go out.” Keep labels factual and concise; avoid over-explaining group math in the card.
  - For stakes logic, reuse the same completed-result parser as standings (`collectGroupStats()` or equivalent) so standings and stakes do not diverge. If exact future goal-difference scenarios are unavailable, it is acceptable for the stakes note to express status possibilities rather than exact clinch math; reserve exact `Clinched R32` labels for the standings clinch algorithm.
  - For follow-on summary cards like `Next USA game`, reuse the same canonical-card-copy pattern instead of hand-authoring duplicate markup: find the first scheduleData event whose match contains the target team and whose source `.game-card` is not `.completed`, then copy that card’s cleaned content into the top card. Set the header metadata from a timezone-aware formatter (not hardcoded PT) and show a concise empty state if no upcoming team game exists.
  - Add CSS so `.today-schedule-game` mirrors the `.game-card` grid columns, make the mobile media query apply to both `.game-card` and `.today-schedule-game`, and add obvious high-contrast boundaries for any stakes badges/notes.
- Label the main listing `Schedule & Results` once games have started.
- Collapse large filter/reference sections (host locations, groups, stages) by default with native `<details><summary>…</summary>` arrows.
- For tournaments with groups/pools, show group data as a visible facet on every group-stage game and in standings. Avoid duplicate filter affordances: if there is a compact filter bar, do **not** also add host-location chips, group cards used as filters, and stage chips unless Gordon explicitly asks for those reference sections.
- For World Cup-style utility pages, keep filters as sparse as the current phase warrants. Earlier group-stage pages used Team/Group/Venue, but once the tournament moves toward knockout viewing Gordon may prefer removing redundant filters (e.g. Group, then Venue/Schedule) rather than preserving them for completeness. Do not treat `Group` as mandatory if the user says it is no longer useful.
- For knockout-phase World Cup pages on mobile, prefer a tabbed bracket view over the full schedule list:
  - Replace the bottom visible game list with `Knockout bracket` and round tabs (`R32`, `R16`, `QF`, `SF`, `3rd`, `Final`).
  - Render one round at a time as cards; each card should show round/match number, localized date/time, matchup, venue/location, and a concise progression label such as `Winner → R16 Match 1`.
  - Do not draw bracket connector lines on phone screens; text progression labels are more legible.
  - Keep the original schedule cards in a hidden source container (e.g. `.schedule-source#schedule { display:none; }`) if existing JS helpers depend on `.game-card`, `rowGameId`, standings, live refresh, or selected-team knockout relabeling. Avoid deleting the source markup unless you also rewrite all dependent helpers.
  - Keep Team focus if useful; when a team is selected, use the existing slot-resolution helpers to fill known direct slots and highlight matching bracket cards. Remove Venue/Schedule filters when they no longer make sense for bracket browsing.
  - **Pitfall: ambiguous third-place pool slots.** Substitute a selected team into a knockout slot only when that team has exactly one locked direct status (`1st in group` or `2nd in group`). Do **not** replace every compatible `Third Place Group A/B/...` placeholder with the selected team: third-place pool allocation depends on the cross-group allocation table and otherwise makes one team appear in multiple R32 games (e.g. Ecuador showing in four games). Leave ambiguous third-place placeholders generic until the exact allocation is known.
  - Verify raw HTML and rendered DOM: raw page has `#bracketTabs`, `#bracketGrid`, no obsolete select IDs, and no old list heading; jsdom should render 16 R32 cards by default, known direct labels like `South Africa vs Canada` should appear when locked, and a non-locked third-place-pool team should not be faked into multiple R32 placeholders.
- For tournament standings or other secondary reference sections, prefer native collapsed `<details class="section ... collapsible">` when the page is getting long. Gordon asked for World Cup group standings to be collapsed by default. Use `<summary>` as the visible title, omit the `open` attribute, reuse `.collapsible` arrow styling, and verify with jsdom that the section starts closed, contains all tables, and opens on summary click.
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
# If the page uses the simplified World Cup filter bar:
assert '<h2 id="filtersTitle">Filters</h2>' in html
assert 'id="team"' in html and 'id="group"' in html and 'id="venue"' in html
assert 'Team regex' not in html and 'id="stage"' not in html
assert all(x not in html for x in ['Host locations','id="cityChips"','id="stageChips"','id="groupChips"'])
# If grouped by day or enriched with lines:
assert html.count('class="day-group"') >= 1
assert html.count('class="kalshi"') in (0, <expected_match_count>)
```

If an important feature is client-rendered (for example the `Today’s games` card), verify the rendered DOM too, not just raw HTML. A simple pattern is to install/use `jsdom` in `/tmp`, execute the live page script, and count the expected rendered subfields (date/time, match, place, TV, Kalshi/result) inside `#todayGames`. If stakes/highlight logic was added, also assert the live raw HTML contains the helper/style hooks (`gameStakes`, `stakes-note`, `stakes-high`/`stakes-medium`) and, when the current date has meaningful matches, that the rendered `#todayGames` includes at least one `.stakes-note`. Avoid relying on browser automation if local Chrome is unavailable; raw fetch plus `jsdom` is sufficient for this class of static page.
