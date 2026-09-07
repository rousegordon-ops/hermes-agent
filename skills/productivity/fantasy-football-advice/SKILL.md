---
name: fantasy-football-advice
description: Use when Gordon asks for fantasy football recommendations, waiver adds/drops, start/sit, trade advice, or says “fantasy recommendations”. Prioritizes roster context, current news, and explicit confidence to avoid oversteering.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [fantasy-football, nfl, sports, waivers, start-sit]
    related_skills: []
---

# Fantasy Football Advice

## Overview

Use this skill for Gordon's fantasy football decisions: waiver adds/drops, start/sit, trade evaluations, stash rankings, injury pivots, and weekly lineup recommendations.

Gordon wants direct, specific actions — not generic setup instructions, not merely identifying “your weakest player is X” and “best waiver player is Y.” A fantasy recommendation should translate analysis into concrete moves: add/drop, start/sit, hold, claim priority, FAAB amount, or “do nothing.”

## Trigger Phrase

If Gordon says exactly or approximately:

- “fantasy recommendations”

then treat it as a request to run/trigger the fantasy recommendations workflow. Gordon stated this maps to cron job `b3cfac1234b9`. If that job is unavailable, say so briefly and fall back to giving live recommendations using current information.

## Required Approach

1. **Use current information first.** Search current fantasy/news sources before giving time-sensitive advice.
2. **Output actions, not labels.** Do not stop at “weakest roster player = X” and “best waiver option = Y.” Convert that into an executable recommendation:
   - `Add X, drop Y`
   - `Start X over Y`
   - `Hold; make no move`
   - `Claim priority: 1) X for Y, 2) A for B`
   - `Bid $N / N% FAAB`
3. **Be clear when no move is best.** “Nothing” / “do nothing” is an acceptable recommendation if no move improves the team enough.
4. **Separate floor from upside only as supporting rationale.** The main output must still be the action.
5. **Tie advice to Gordon's need.** If his roster need is unknown, use the safest default:
   - prefer near-term usable depth over fragile deep stashes
   - do not recommend using a waiver move unless the upgrade is clear
6. **Do not overcorrect with another panic move.** If a bad/uncertain move already happened, recommend waiting unless there is a clearly superior available option.

## Player-Specific Guardrails

Player-specific mistakes can be captured here, but they must not dominate the skill. The general rule is more important: **specific actions over vague comparisons**.

### Chris Rodriguez vs. Roschon Johnson

Do **not** casually recommend dropping Chris Rodriguez Jr. for Roschon Johnson.

Default ordering unless current news strongly changes it:

1. **Chris Rodriguez Jr. > Roschon Johnson** for near-term RB depth / Week 1 or early-season usability.
2. **Roschon Johnson > Chris Rodriguez Jr.** only if the stated goal is a deep, low-probability upside stash and Gordon does not need an emergency playable RB.

If comparing them, the recommendation must be explicit, e.g.:

> “Add Chris Rodriguez; drop Roschon.”

or:

> “Hold Roschon; do not spend another move unless Chris clears.”

## Waiver / Drop Decision Template

When asked “what should I do?” respond in this structure:

1. **Recommended action:** exact move, or `Do nothing`.
2. **Priority list:** if multiple moves are plausible, rank exact transactions.
3. **Why:** 1-3 bullets, focused on role/value delta.
4. **Exception / trigger to change:** only if important.

Good examples:

- `Do nothing. Keep your roster as-is; none of these waiver options are enough of an upgrade to spend the move.`
- `Add Malik Washington; drop your backup TE. Do not drop an RB for him.`
- `Start Jaylen Warren over Player X in flex. Sit Player Y.`
- `Waiver claims: 1) Chris Rodriguez for Roschon; 2) Tank Bigsby for backup DST. If both fail, no move.`

Bad example:

- `Your weakest player is Roschon and the best waiver option is Chris Rodriguez.`

That is analysis, not a recommendation. Convert it into: `Add Chris Rodriguez; drop Roschon.`

## Current-News Checks

For NFL/fantasy advice, prefer fresh sources such as:

- team injury reports / depth charts
- Sleeper roster data if available
- FantasyPros / RotoBaller / Yahoo / ESPN / DraftSharks / The Athletic snippets
- beat reporter reports when surfaced in search results

Check for:

- injury designation and practice participation
- depth-chart role
- projected touches/routes/snaps
- matchup only after role is established
- PPR vs half-PPR vs standard scoring

## Common Pitfalls

1. **Returning analysis instead of an action.** “Weakest player is X / best waiver player is Y” is not enough. Say `add Y, drop X`, `hold`, `start Y over X`, or `do nothing`.
2. **Overweighting upside stash language.** Do not recommend a long-shot stash over a boring usable player unless Gordon explicitly wants long-term upside.
3. **Ignoring availability locks.** If Gordon says he must wait 2 days, schedule the reminder and tell him not to chase the mistake with another marginal move.
4. **Giving generic recommendations after a trigger phrase.** If he says “fantasy recommendations,” run the mapped workflow/job first if possible; if not possible, provide concrete actions anyway.
5. **Contradicting prior advice without owning it.** If previous advice was wrong, acknowledge it briefly, then give the corrected action.
6. **Treating injury-questionable players as normal stashes.** Injured/questionable bench players need a clearer upside case to beat a healthy, usable role player.

## Verification Checklist

Before final answer:

- [ ] Did I use current information for time-sensitive claims?
- [ ] Did I give an executable action: add/drop, start/sit, hold, bid, claim order, or `do nothing`?
- [ ] Did I avoid stopping at “weakest player” / “best waiver player” labels?
- [ ] Did I distinguish immediate role from upside stash only as rationale, not as the answer?
- [ ] If discussing Chris Rodriguez vs Roschon Johnson, did I default to Chris for near-term usability unless upside-stash goal is explicit?
- [ ] Did I avoid recommending another marginal move just to undo discomfort?
