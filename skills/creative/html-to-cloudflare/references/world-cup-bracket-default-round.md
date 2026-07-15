# World Cup bracket default round updates

Use when Gordon asks for shorthand like “Default to SF” on `/world-cup-2026`.

## Pattern

1. Interpret as the visible knockout bracket tab default, not timezone or location.
2. Patch both sources of default state in `/opt/data/hermes-pages/world-cup-2026.html`:
   - Mark the requested tab button as `class="bracket-tab active"` and remove `active` from the old tab.
   - Update the executable JS default: `let activeBracketStage = '<Stage>';`.
3. Stage labels used by the page:
   - `R32` → `Round Of 32`
   - `R16` → `Round Of 16`
   - `QF` → `Quarterfinals`
   - `SF` → `Semifinals`
   - `3rd` → `3Rd Place Match`
   - `Final` → `Final`
4. Before committing, assert the new active markup and JS default are present and the old JS default is absent.
5. If `/opt/data/hermes-pages` has unrelated dirty files, commit only `world-cup-2026.html`, then deploy from an isolated clean clone.
6. Deploy with Wrangler Direct Upload and verify the canonical URL, not only the preview URL.

## Verification snippet

```python
import urllib.request
url = 'https://hermes-pages-d55.pages.dev/world-cup-2026'
html = urllib.request.urlopen(
    urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0', 'Cache-Control':'no-cache'}),
    timeout=40,
).read().decode('utf-8','replace')
assert '<button class="bracket-tab active" data-stage="Semifinals" type="button">SF</button>' in html
assert "let activeBracketStage = 'Semifinals';" in html
```

## Pitfall

Changing only the visible `active` class makes the tab look right in static HTML but the page can still render the old bracket after JS initializes. Changing only `activeBracketStage` can render the right cards but leave the wrong tab highlighted before/around initialization. Always patch both.
