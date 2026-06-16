# World Cup schedule filter update verification (2026-06-16)

Context: Gordon asked to add a date/status filter to `/opt/data/hermes-pages/world-cup-2026.html` with exactly three options: `Schedule`, `Results`, `Results & schedule`, defaulting to `Schedule`.

Useful implementation pattern:
- Add a dedicated select in the filter controls:
  ```html
  <select id="dateFilter" aria-label="Date filter">
    <option value="schedule" selected>Schedule</option>
    <option value="results">Results</option>
    <option value="all">Results &amp; schedule</option>
  </select>
  ```
- In `apply()`, treat `.game-card.completed` as results and every other game card as schedule/upcoming/live:
  ```js
  const selectedDateFilter = dateFilter.value;
  const isResult = row.classList.contains('completed');
  const okDate = selectedDateFilter === 'all' ||
    (selectedDateFilter === 'results' ? isResult : !isResult);
  const show = okTeam && okGroup && okVenue && okDate;
  ```
- Add `dateFilter.addEventListener('change', apply);`.
- Call `apply()` after page initialization so the default `Schedule` filter actually hides completed results on first load.
- Reset should restore `dateFilter.value = 'schedule'`.
- If live refreshes can change a card to completed, call `apply()` after refresh/update so the default schedule view updates immediately.

Verification shortcuts when browser automation is unavailable:
1. Extract the executable inline script and run `node --check` against it.
2. Use Python/regex checks on the HTML to confirm the select/options/listeners/default reset are present and that expected row counts make sense.
3. Verify the live canonical source with Python `urllib.request` and a `User-Agent`; `web_extract` can omit form controls/options from its text view, so do not rely on it alone for this kind of UI verification.

Example verification snippet:
```bash
python3 - <<'PY'
import urllib.request
url='https://hermes-pages-d55.pages.dev/world-cup-2026'
req=urllib.request.Request(url, headers={'User-Agent':'hermes-agent/1.0'})
html=urllib.request.urlopen(req, timeout=20).read().decode('utf-8','replace')
for needle in [
    'id="dateFilter"',
    '<option value="schedule" selected>Schedule</option>',
    "dateFilter.addEventListener('change', apply);",
    "dateFilter.value='schedule'",
]:
    print(needle, needle in html)
PY
```

Repo/process note: `/opt/data/hermes-pages` may have a watcher/auto-committer that commits `world-cup-2026.html` very quickly with a generic `Auto-update World Cup results` message. If a manual `git commit` reports no staged changes, inspect `git log --oneline -1 -- world-cup-2026.html`, `git show --stat -1`, and live source before assuming your edit was lost.
