---
name: fantasy-football-advice
description: Use when Gordon asks for fantasy football recommendations, waivers, start/sit, trades, or says “fantasy recommendations”. Return concrete actions, not just analysis.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [fantasy-football, nfl, waivers, start-sit]
    related_skills: []
---

# Fantasy Football Advice

## Trigger

Use this when Gordon asks for fantasy football advice, including:

- “fantasy recommendations”
- waiver adds/drops
- start/sit
- trades
- FAAB / claims
- roster cleanup

If Gordon says “fantasy recommendations,” run cron job `b3cfac1234b9`. If unavailable, say so briefly and give live recommendations anyway.

## Core Rule

Fantasy recommendations must be **specific executable actions**, not labels or analysis alone.

Good outputs:

- `Add Y; drop X.`
- `Start A over B.`
- `Hold / do nothing.`
- `Claims: 1) Add Y/drop X; 2) Add B/drop A.`
- `Bid $N / N% FAAB.`

Bad output:

- `Your weakest player is X and the best waiver option is Y.`

Convert that into the move: `Add Y; drop X.`

## Data Sources

Gordon's Sleeper league can be queried via the public Sleeper API:

- Username: `GordonOnSleeper`
- League ID: `1389388645986750464`

Use these before asking Gordon for roster/waiver context:

- `https://api.sleeper.app/v1/user/GordonOnSleeper`
- `https://api.sleeper.app/v1/league/1389388645986750464`
- `https://api.sleeper.app/v1/league/1389388645986750464/rosters`
- `https://api.sleeper.app/v1/league/1389388645986750464/users`
- `https://api.sleeper.app/v1/state/nfl`
- `https://api.sleeper.app/v1/league/1389388645986750464/matchups/{current_week}`
- `https://api.sleeper.app/v1/league/1389388645986750464/transactions/{current_week}`
- `https://api.sleeper.app/v1/players/nfl/trending/add?lookback_hours=24&limit=50`
- `https://api.sleeper.app/v1/players/nfl/trending/drop?lookback_hours=24&limit=25`
- `https://api.sleeper.app/v1/players/nfl`

To identify Gordon's roster, resolve the Sleeper `user_id`, then match it to league rosters by `owner_id`. To identify likely waiver/free-agent targets, subtract all rostered player IDs from candidate/trending/player lists.

## Workflow

1. Pull Sleeper roster, league settings, users, matchups, transactions, and likely waiver options when advice is roster-specific.
2. Check current news/rankings for time-sensitive advice.
3. Use roster/scoring context when available.
4. Decide whether a move is actually worth making.
5. Return the exact action first.
6. Add only brief rationale.
7. If no move is best, say `Do nothing`.

## Response Shape

Use this structure:

1. **Action:** exact move, or `Do nothing`.
2. **Priority:** ranked exact transactions if more than one.
3. **Why:** 1-3 short bullets.
4. **Exception:** only if it changes the action.

## Pitfalls

- Do not stop at “weakest player” / “best available player.”
- Do not give generic waiver lists unless asked.
- Do not recommend marginal churn; `do nothing` is valid.
- Do not overvalue upside stashes without saying who to add/drop.
- Own prior bad advice briefly, then give the corrected action.
- Do not claim “I recommended X earlier” unless the visible conversation text actually says that. If a context-compaction summary and recent visible messages conflict, trust the visible user-facing message and acknowledge uncertainty instead of asserting continuity.
- Before giving waiver advice, separate confirmed Sleeper facts, public-news facts, and inference. If availability output was truncated or uncertain, re-query before recommending an add/drop.

## Checklist

- [ ] Current info checked if needed.
- [ ] Exact action given first.
- [ ] Add/drop or start/sit names are explicit.
- [ ] “Do nothing” used when appropriate.
- [ ] Rationale is short.
