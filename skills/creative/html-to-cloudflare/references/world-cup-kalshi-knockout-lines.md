# World Cup Kalshi knockout-line updates

Use this when adding Kalshi prices to World Cup knockout games whose visible bracket labels still contain placeholders.

## Why the ordinary updater can miss them

`/opt/data/scripts/update_wc_results.py` refreshes Kalshi lines by parsing the visible schedule-card matchup and matching it to Kalshi market titles. That works for concrete matchups such as `Croatia vs Ghana`, but not for knockout cards whose HTML still says `Group A 2nd Place vs Group B 2nd Place` while Kalshi has already posted `South Africa vs Canada Winner?`.

## Recommended pattern

1. Fetch open Kalshi FIFA game markets:
   ```python
   url = 'https://external-api.kalshi.com/trade-api/v2/markets?status=open&limit=100&series_ticker=KXWCGAME'
   ```
2. Group by `event_ticker`; each event usually has three markets: Team A, Tie, Team B. Gordon prefers the Kalshi outcome label rendered as `Tie`, matching Kalshi's wording, even for knockout games.
3. Parse `title` with `(.+?)\s+vs\s+(.+?)\s+Winner\?` to identify the concrete matchup.
4. Normalize Kalshi `yes_sub_title` before display/matching:
   - Strip leading `Reg Time: ` when present.
   - Normalize `USA` ↔ `United States`.
   - Normalize `Bosnia and Herzegovina` ↔ `Bosnia-Herzegovina`.
   - Preserve user-facing short labels (`USA`, `Bosnia-Herzegovina`) in the rendered line.
5. Use ESPN game IDs as the durable join key for the page. Maintain an explicit `gameId -> concrete matchup` map for knockout cards that are posted on Kalshi but still placeholder-labeled in schedule data. This applies beyond R32: when R16 markets post before the source page labels resolve, add those R16 game IDs to `/opt/data/scripts/update_wc_results.py`'s knockout override map as well, then run the updater so future hourly refreshes do not revert to `not posted yet`.
6. Write the line onto the hidden canonical schedule card as:
   ```html
   <div class="kalshi">Kalshi: Team A 57–58¢ · Tie 26–27¢ · Team B 17–18¢</div>
   ```
7. Render bracket-card lines by reading from the schedule card, not by maintaining a second Kalshi dataset:
   ```js
   function bracketKalshiHtml(ev) {
     const card = scheduleCardFor(ev.id);
     const kalshi = card?.querySelector(':scope > .kalshi');
     return kalshi ? `<div class="bracket-kalshi">${kalshi.innerHTML}</div>` : '';
   }
   ```
   Then include `${bracketKalshiHtml(ev)}` in `renderBracket()` after `.bracket-place`.

## Third-place placeholders

If Kalshi is posted for a concrete R32 matchup that resolves a third-place placeholder, update `knownThirdPlaceSlots` only for exact authoritative/market-resolved assignments keyed by ESPN game ID. Do not infer all compatible third-place slots. Example from the 2026 page:

```js
const knownThirdPlaceSlots = {
  '760489': 'Paraguay',
  '760492': 'Sweden',
  '760494': 'Bosnia-Herzegovina'
};
```

This keeps bracket labels aligned with the posted Kalshi market while avoiding the old bug where one third-place team appeared in multiple possible slots.

## Verification

- Extract inline JS and run `node --check`.
- Verify the local HTML contains all expected updated game IDs and `function bracketKalshiHtml(ev)`.
- Deploy with Wrangler Direct Upload; git push alone is not enough for `hermes-pages`.
- Verify the canonical live URL source contains at least one newly added Kalshi line and the `bracket-kalshi` hook.
- Browser automation may be unavailable on this host; if Chrome is missing, source + JS verification is acceptable but mention that visual browser verification was not run only if relevant.
