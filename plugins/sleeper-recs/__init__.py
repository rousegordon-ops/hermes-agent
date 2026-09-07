"""Personal Sleeper fantasy-football trigger for Hermes gateway messages."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


JOB_ID = "b3cfac1234b9"
JOB_NAME = "Fantasy Football Daily Watch"
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

PROMPT = f"""You are Hermes running as a daily fantasy football watch job for Gordon.

Sleeper details:
- Username: {USERNAME}
- League ID: {LEAGUE_ID}

Today's task:
1. Fetch current league, roster, matchup, transaction, and NFL state data from Sleeper's public API. Use these endpoints as needed:
   - https://api.sleeper.app/v1/user/{USERNAME}
   - https://api.sleeper.app/v1/league/{LEAGUE_ID}
   - https://api.sleeper.app/v1/league/{LEAGUE_ID}/rosters
   - https://api.sleeper.app/v1/league/{LEAGUE_ID}/users
   - https://api.sleeper.app/v1/state/nfl
   - https://api.sleeper.app/v1/league/{LEAGUE_ID}/matchups/{{current_week}}
   - https://api.sleeper.app/v1/league/{LEAGUE_ID}/transactions/{{current_week}}
   - https://api.sleeper.app/v1/players/nfl/trending/add?lookback_hours=24&limit=50
   - https://api.sleeper.app/v1/players/nfl/trending/drop?lookback_hours=24&limit=25
   - https://api.sleeper.app/v1/players/nfl (large file; fetch only if needed to map player ids, injury status, teams, positions, and age)
2. Identify Gordon's team roster_id by resolving the Sleeper username to user_id and matching that user_id against the league roster owner_ids.
3. Review his roster, starters, bench, taxi or reserve slots, injury statuses, byes or schedule risks, and the current week's matchup.
4. Recommend waiver pickups only when they are likely unrostered in this league. Compare trending players and current needs against all rostered player ids.
5. Recommend trade targets and trade aways based on Gordon's roster depth, league rosters, standings/record if available, and positional needs. Only suggest concrete trades that are coherent for both sides.
6. Be concise and actionable. Lead with the top 3-5 actions, then give optional context: roster health, week outlook, pickups, drops, trade ideas, and monitoring notes.
7. If data is missing or the API is unavailable, say exactly what failed and give the best recommendations possible from available data.

<cron_status_prefix>If nothing has changed materially since the last run, start your response with "NO_NEW_FINDINGS:" and then give a one-paragraph status update.</cron_status_prefix>
"""


def _hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))


def _trigger_job() -> tuple[bool, str]:
    jobs_path = _hermes_home() / "cron" / "jobs.json"
    if jobs_path.exists():
        try:
            data = json.loads(jobs_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return False, f"Could not read cron jobs: {exc}"
    else:
        data = {"jobs": []}

    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        return False, f"Invalid cron jobs file: {jobs_path}"

    now = datetime.now().astimezone().isoformat()
    job_found = False
    for job in jobs:
        if job.get("id") == JOB_ID or job.get("name") == JOB_NAME:
            job_found = True
            job["enabled"] = True
            job["state"] = "scheduled"
            job["paused_at"] = None
            job["paused_reason"] = None
            job["next_run_at"] = now
            data["updated_at"] = now
            break

    if not job_found:
        jobs.append(
            {
                "id": JOB_ID,
                "created_at": now,
                "repeat": {"times": None, "completed": 0},
                "last_run_at": None,
                "last_status": None,
                "last_error": None,
                "last_delivery_error": None,
                "origin": None,
                "name": JOB_NAME,
                "prompt": PROMPT,
                "skills": [],
                "skill": None,
                "model": None,
                "provider": None,
                "base_url": None,
                "script": None,
                "context_from": None,
                "schedule": {
                    "kind": "interval",
                    "minutes": 1440,
                    "display": "every 1440m",
                },
                "schedule_display": "every 1440m",
                "enabled": True,
                "state": "scheduled",
                "paused_at": None,
                "paused_reason": None,
                "next_run_at": now,
                "deliver": "origin",
                "enabled_toolsets": ["web", "terminal"],
                "workdir": str(Path.cwd()),
            }
        )
        data["updated_at"] = now

    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(jobs_path.parent),
        suffix=".tmp",
        prefix=".jobs_",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, jobs_path)
        os.chmod(jobs_path, 0o600)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return True, f"Triggered {JOB_NAME}. It will run on the next scheduler tick."


def _sleeper_recs_command(raw_args: str = "") -> str:
    del raw_args
    ok, message = _trigger_job()
    if ok:
        return message
    return f"Could not trigger Sleeper recommendations: {message}"


def _pre_gateway_dispatch(**kwargs: Any) -> dict[str, str] | None:
    event = kwargs.get("event")
    text = str(getattr(event, "text", "") or "").strip().lower()
    if text in PHRASES:
        return {"action": "rewrite", "text": "/sleeper-recs"}
    return None


def register(ctx) -> None:
    ctx.register_command(
        "sleeper-recs",
        _sleeper_recs_command,
        description="Trigger Gordon's Sleeper fantasy football recommendations.",
    )
    ctx.register_hook("pre_gateway_dispatch", _pre_gateway_dispatch)
