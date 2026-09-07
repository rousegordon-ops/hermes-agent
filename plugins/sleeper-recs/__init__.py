"""Personal Sleeper fantasy-football recommendations for Hermes messages."""

from __future__ import annotations

from typing import Any


LEAGUE_ID = "1389388645986750464"
USERNAME = "GordonOnSleeper"
PHRASES = {
    "fantasy recommendations",
    "fantasy recommendation",
    "fantasy recs",
    "fantasy football recommendations",
    "fantasy football recs",
    "sleeper recommendations",
    "sleeper recommendation",
    "sleeper recs",
    "run my fantasy football recommendations",
    "run fantasy football recommendations",
    "run fantasy recommendations",
}

IMMEDIATE_PROMPT = f"""Run Gordon's Sleeper fantasy football recommendations now.

Sleeper details:
- Username: {USERNAME}
- League ID: {LEAGUE_ID}

Fetch current league, roster, matchup, transaction, and NFL state data from Sleeper's public API. Use these endpoints as needed:
- https://api.sleeper.app/v1/user/{USERNAME}
- https://api.sleeper.app/v1/league/{LEAGUE_ID}
- https://api.sleeper.app/v1/league/{LEAGUE_ID}/rosters
- https://api.sleeper.app/v1/league/{LEAGUE_ID}/users
- https://api.sleeper.app/v1/state/nfl
- https://api.sleeper.app/v1/league/{LEAGUE_ID}/matchups/{{current_week}}
- https://api.sleeper.app/v1/league/{LEAGUE_ID}/transactions/{{current_week}}
- https://api.sleeper.app/v1/players/nfl/trending/add?lookback_hours=24&limit=50
- https://api.sleeper.app/v1/players/nfl/trending/drop?lookback_hours=24&limit=25
- https://api.sleeper.app/v1/players/nfl only if needed to map player ids, injury status, teams, positions, and age.

Identify Gordon's team roster_id by resolving the Sleeper username to user_id and matching that user_id against the league roster owner_ids.

Give a concise actionable report:
- Top 3-5 actions first.
- Roster health and current matchup outlook.
- Waiver pickups only when they are likely unrostered in this league.
- Drops only when justified by Gordon's roster needs.
- Concrete trade ideas only when coherent for both sides.

If data is missing or the API is unavailable, say exactly what failed and give the best recommendations possible from available data.
"""


def _pre_gateway_dispatch(**kwargs: Any) -> dict[str, str] | None:
    event = kwargs.get("event")
    text = str(getattr(event, "text", "") or "").strip().lower()
    if text in PHRASES:
        return {"action": "rewrite", "text": IMMEDIATE_PROMPT}
    return None


def register(ctx) -> None:
    ctx.register_hook("pre_gateway_dispatch", _pre_gateway_dispatch)
