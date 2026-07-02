# World Cup knockout bracket mobile UI notes

Use this when replacing/augmenting a long World Cup schedule list with a phone-friendly knockout bracket.

## Mobile display pattern

- Do **not** render a full tree on phones. Use round tabs/segmented controls (`R32`, `R16`, `QF`, `SF`, `3rd`, `Final`) and show one round at a time.
- Use stacked cards per match: match number, localized kickoff, matchup, venue, optional Kalshi line, and a concise advancement label such as `Winner → R16 Match 6`.
- For completed knockout games, show a compact score block in the visible bracket card by reading the hidden schedule card’s `.result-card` rows; strike through the losing team name using the `.result-row.loser` class. Keep this derived from canonical schedule data so hourly result updates automatically flow into the bracket.
- If a top `Today's games` / `Next <team> game` card copies from hidden schedule cards, pass the resolved knockout label into the copy helper (e.g. `cardContentHtml(card, bracketMatchLabel(ev, ''))` for R32). Otherwise mobile top cards can still show `Group A 2nd Place` placeholders after the bracket itself is resolved.
- If live refresh rewrites the match/result block from the ESPN API, make that refresh path use the same resolved label helper for the `<a>` text, `aria-label`, and result-row teams. Otherwise tapping `Refresh` can reintroduce placeholder team names inside the live scoreboard even when the card title was previously resolved.
- Hide the old long schedule list with CSS (`.schedule-source { display:none; }`) rather than deleting it if existing client-side code still depends on `.game-card` rows for standings, result parsing, known-slot inference, Kalshi line storage, or refresh logic.
- If Kalshi prices are shown in bracket cards, keep the hidden schedule card as the canonical data holder and render the visible card by reading its `.kalshi` node (see `world-cup-kalshi-knockout-lines.md`). Do not maintain a second, divergent bracket-only Kalshi dataset.
- Keep team focus separate from schedule filters. For a bracket view, a single `Team` select + `Reset` is usually enough; venue/date/group filters become confusing once the main visible unit is a bracket.

## Known-slot replacement rules

- Direct slots can be filled when locked: `Group X Winner` or `Group X 2nd Place`.
- Do **not** substitute a selected team into every compatible third-place placeholder (e.g. `Third Place Group B/E/F/I/J`). The third-place allocation depends on FIFA's cross-group allocation table; naive compatibility makes one team appear in multiple games.
- Only replace a third-place placeholder when an authoritative bracket/source has assigned that exact match. Keep a `knownThirdPlaceSlots` map keyed by ESPN game ID or match number, e.g. `760494 -> Bosnia-Herzegovina` for USA's R32 match once the source says Match 81 is USA vs Bosnia-Herzegovina.
- For selected-team filtering/highlighting, only place the team into the bracket when its direct slot is locked (`statuses.size === 1` and status is `1st in group` or `2nd in group`). Third-place pool teams should not be highlighted into a match unless the exact slot is known.
- For post-R32 rounds, resolve placeholders such as `Round of 32 1 Winner` from the hidden canonical schedule cards once those source games are completed. Preferred pattern: `completedWinnerForEvent(ev)` reads `.game-card.completed .result-row.winner .result-team`, then `replaceKnownPriorWinners(label)` iterates `scheduleData`, uses `outgoingKnockoutRefs(sourceEv)`, and replaces matching winner refs in R16/QF/SF/Final labels. Do this in the visible bracket-label path (`bracketMatchLabel`) so top cards, team filtering, and live refreshes reuse the same resolved labels instead of maintaining a second dataset.
- Do **not** derive `Round of 32 N Winner` by chronological DOM order unless verified. ESPN/FIFA downstream R16 labels may use official bracket match numbers that differ from page/date order. Keep an explicit `officialRoundOf32Numbers` map keyed by ESPN game ID (e.g. 760486→1, 760489→2, 760488→3, 760487→4, 760492→5, 760490→6, 760491→7, 760495→8, 760494→9, 760493→10, 760497→11, 760496→12, 760498→13, 760499→14, 760500→15, 760501→16) so visible R16 labels align with Kalshi lines.

## Verification

- Run `node --check` on extracted inline JS.
- Use jsdom to render the page and assert the bracket card count for the active round (`R32` should be 16), tab labels exist, and the expected known match appears.
- If `npx -p jsdom node /tmp/test.js` cannot resolve `jsdom` because the script is outside the temporary package path, create a temp npm project, install jsdom there, copy the probe into that directory, and run it from there:
  ```bash
  rm -rf /tmp/wctest && mkdir -p /tmp/wctest
  cd /tmp/wctest && npm init -y >/dev/null && npm install jsdom@24 >/dev/null
  cp /tmp/test-wc-r16.js /tmp/wctest/test-wc-r16.js
  node /tmp/wctest/test-wc-r16.js
  ```
- Regression checks:
  - Selecting a third-place team whose exact slot is **not** known should not create multiple fake R32 appearances.
  - Selecting a locked direct-slot team (e.g. Canada as Group B 2nd) should still show one highlighted known match.
  - Selecting an explicitly mapped third-place team (e.g. Bosnia-Herzegovina after source assignment) should show one highlighted match.
  - Simulate a completed R32 source card and assert R16 resolves only known winners (e.g. `Canada vs Round of 32 3 Winner` while Match 3 is unknown; `Canada vs Germany` after Match 3 is completed). Do not require both sides to resolve unless both source games are completed.
- Verify the canonical Cloudflare URL after Wrangler deploy; Direct Upload means git push alone is not enough.
