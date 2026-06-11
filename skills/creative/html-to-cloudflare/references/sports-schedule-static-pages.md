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

## Timezone conversion

Use Python, not mental math:

```python
from datetime import datetime
from zoneinfo import ZoneInfo
pt = ZoneInfo('America/Los_Angeles')
dt_pt = datetime.fromisoformat(utc.replace('Z', '+00:00')).astimezone(pt)
```

For June/July events, the actual abbreviation is PDT. If the user asks for PST/Pacific, label the main UI as `PT` for readability and optionally note that summer dates are PDT.

## Page pattern

Good structure for a standalone schedule page:
- Hero with event name and clear timezone statement.
- Stats: match count, host locations, opening date, final date.
- Search box across team/city/stadium/stage.
- For Gordon-facing utility schedules, prefer a live regex search with a dynamic suggestions dropdown, not just plain substring filtering:
  - Compile user input with `new RegExp(raw, 'i')`; show an inline invalid-regex error instead of throwing.
  - Build suggestions from unique teams, full matches, stadiums, locations, and stages from the embedded schedule JSON.
  - Dropdown should update while typing, highlight the matching text, and let clicks populate the escaped literal value.
  - Filtering should apply the regex to each row's normalized `data-search` text while still respecting city/stage filters.
- Filter chips for host locations and stages.
- Responsive table: date/time, match, location, TV/streaming.
- On mobile, turn rows into cards; avoid wide tables.
- High-contrast dark theme for readability.

## Verification checklist

Before commit/deploy:

```python
s = open('/opt/data/hermes-pages/<page>.html', encoding='utf-8').read()
assert '<expected opening match>' in s
assert '<expected PT kickoff>' in s
assert s.count('<tr data-stage=') == <expected_match_count>
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
assert html.count('<tr data-stage=') == <expected_match_count>
assert 'id="suggestions"' in html  # if regex dropdown was requested
```
