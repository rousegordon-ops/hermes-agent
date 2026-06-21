# World Cup standings: Round of 32 clinch badges

Session pattern from `/opt/data/hermes-pages/world-cup-2026.html`.

## Goal

For each group standings card, show whether a team has clinched a Round of 32 berth, and show final group position once the group is complete.

## Implementation pattern

1. Reuse the page's existing standings calculation from completed group-stage result cards.
2. Build remaining group matches from `scheduleData`, treating cards not marked `.completed` as remaining.
3. For clinch logic, enumerate all remaining match outcome scenarios (`home win`, `draw`, `away win`) rather than using a naive independent max-points check. The independent max-points method can overstate clinches because two trailing teams may still play each other and cannot both maximize points.
4. A top-two berth is clinched only if, in every possible remaining-points scenario, no more than one other team can finish with points greater than or equal to the candidate team's points. Use `>=` to avoid claiming clinch when unresolved tie-breakers could still matter.
5. First place is clinched only if, in every scenario, zero other teams can finish with points greater than or equal to the candidate team's points.
6. Once all teams in the group have 3 played matches, render final labels:
   - `R32 · 1st`
   - `R32 · 2nd`
   - `3rd-place pool`
   - `Out`

## UI pattern

- Put the badge inside the Team cell rather than adding another standings column. This preserves compact table width on mobile.
- Use a high-contrast green pill for active clinches (`Clinched R32`, `Clinched 1st`).
- Hide empty/no-status cells rather than showing a dash; dashes add clutter in every row.
- Add one short note above the standings grid explaining that green badges mark clinched Round of 32 berths.

## Verification

- Extract the inline script after `</script><script>` into `/tmp/world-cup-inline.js` and run `node --check /tmp/world-cup-inline.js`.
- If browser automation is unavailable, fetch the live canonical URL with Python `urllib.request` and assert the deployed HTML contains:
  - the explanatory note
  - `.clinch-badge`
  - `function possiblePointTables`
  - `function clinchedRoundOf32Label`
  - `team-cell`
- Manually sanity-check current labels against possible outcomes. Example: two teams on 4 points with one match left each are not necessarily clinched if both could lose and a 3-point team could pass/tie them.
