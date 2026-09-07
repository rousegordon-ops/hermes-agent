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

## Workflow

1. Check current news/rankings for time-sensitive advice.
2. Use roster/scoring context when available.
3. Decide whether a move is actually worth making.
4. Return the exact action first.
5. Add only brief rationale.
6. If no move is best, say `Do nothing`.

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

## Checklist

- [ ] Current info checked if needed.
- [ ] Exact action given first.
- [ ] Add/drop or start/sit names are explicit.
- [ ] “Do nothing” used when appropriate.
- [ ] Rationale is short.
