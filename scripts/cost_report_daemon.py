#!/usr/bin/env python3
"""Sleeps until the next 6 AM America/Los_Angeles, runs cost_report.py, repeats.

On startup: if no cost-state.json exists yet, take a baseline snapshot
immediately so the very first scheduled run has a previous balance to
diff against. Without this, the first 6 AM report would show "first
snapshot — spend available tomorrow" instead of an actual delta.

Designed for a long-lived container — sleeps for the wait duration in
one syscall, no busy-loop. Errors during the report run are logged but
don't kill the daemon.
"""

import os
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
HOUR = int(os.environ.get("COST_REPORT_HOUR", "6"))
MINUTE = int(os.environ.get("COST_REPORT_MINUTE", "0"))
SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cost_report.py")
STATE_PATH = os.environ.get("COST_STATE_PATH", "/opt/data/cost-state.json")


def log(msg: str) -> None:
    print(f"[cost-report-daemon] {msg}", flush=True)


def seconds_until_next(hour: int, minute: int) -> float:
    now = datetime.now(PT)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def run_once(extra_args: list[str] | None = None) -> int:
    cmd = [sys.executable, SCRIPT] + (extra_args or [])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.stdout.strip():
            log(f"stdout: {result.stdout.strip()}")
        if result.stderr.strip():
            log(f"stderr: {result.stderr.strip()}")
        return result.returncode
    except Exception:
        log(f"crashed:\n{traceback.format_exc()}")
        return 1


def main() -> None:
    log(f"started; will fire daily at {HOUR:02d}:{MINUTE:02d} America/Los_Angeles")

    # Take a baseline snapshot if we have no previous state. This ensures
    # the first scheduled report has yesterday's balance to diff against.
    if not os.path.exists(STATE_PATH):
        log("no prior state — taking baseline snapshot now")
        run_once(["--baseline"])

    while True:
        wait = seconds_until_next(HOUR, MINUTE)
        target = datetime.now(PT) + timedelta(seconds=wait)
        log(f"sleeping {wait:.0f}s until {target.strftime('%Y-%m-%d %H:%M %Z')}")
        time.sleep(wait)

        run_once()

        # Sleep a minute past the trigger time to dodge double-fires from
        # any clock skew or sleep-overshoot edge cases.
        time.sleep(60)


if __name__ == "__main__":
    main()
