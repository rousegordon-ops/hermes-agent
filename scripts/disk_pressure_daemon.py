#!/usr/bin/env python3
"""Disk-pressure alerter for the /opt/data Railway volume.

Every hour, checks the percent-used on the volume.  Once the volume
crosses a configurable threshold (default 80%), sends a single Telegram
ping to TELEGRAM_HOME_CHANNEL with the top space consumers and the
current free space.  Won't re-alert until the volume drops back below
the threshold and crosses it again — avoids spamming on a slow leak.

Quiet skip if TELEGRAM_BOT_TOKEN or TELEGRAM_HOME_CHANNEL is missing.
"""
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

LOG = logging.getLogger("disk_pressure")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

VOLUME = os.environ.get("HERMES_HOME", "/opt/data")
THRESHOLD_PCT = float(os.environ.get("HERMES_DISK_ALERT_PCT", "80"))
CHECK_INTERVAL_SEC = int(os.environ.get("HERMES_DISK_ALERT_INTERVAL_SEC", "3600"))
STATE_FILE = Path(VOLUME) / ".disk_pressure_state.json"


def percent_used(path: str) -> float:
    usage = shutil.disk_usage(path)
    if usage.total == 0:
        return 0.0
    return 100.0 * (usage.total - usage.free) / usage.total


def top_consumers(path: str, limit: int = 8) -> str:
    try:
        out = subprocess.run(
            ["du", "-sh", *sorted(str(p) for p in Path(path).iterdir())],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return f"(du failed: {exc})"
    rows: list[tuple[str, str]] = []
    for line in out.stdout.splitlines():
        size, _, name = line.partition("\t")
        if size and name:
            rows.append((size.strip(), name.strip()))

    def _sort_key(row: tuple[str, str]) -> float:
        s = row[0]
        mult = {"K": 1, "M": 1024, "G": 1024 * 1024, "T": 1024 * 1024 * 1024}
        try:
            return float(s[:-1]) * mult.get(s[-1], 0)
        except ValueError:
            return 0.0

    rows.sort(key=_sort_key, reverse=True)
    return "\n".join(f"  {size}\t{name}" for size, name in rows[:limit])


def send_telegram(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    channel = os.environ.get("TELEGRAM_HOME_CHANNEL")
    if not token or not channel:
        return False
    data = urllib.parse.urlencode({"chat_id": channel, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
        return True
    except Exception as exc:
        LOG.warning("Telegram send failed: %s", exc)
        return False


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"alerted": False}
    try:
        return json.loads(STATE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {"alerted": False}


def save_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state))
    except OSError as exc:
        LOG.warning("Could not write state: %s", exc)


def main() -> int:
    LOG.info(
        "disk_pressure_daemon starting (volume=%s, threshold=%.1f%%, interval=%ds)",
        VOLUME,
        THRESHOLD_PCT,
        CHECK_INTERVAL_SEC,
    )
    while True:
        try:
            pct = percent_used(VOLUME)
        except OSError as exc:
            LOG.warning("disk_usage failed: %s", exc)
            time.sleep(CHECK_INTERVAL_SEC)
            continue

        state = load_state()
        already_alerted = bool(state.get("alerted"))

        if pct >= THRESHOLD_PCT and not already_alerted:
            consumers = top_consumers(VOLUME)
            msg = (
                f"⚠️ Disk pressure on {VOLUME}: {pct:.1f}% used "
                f"(threshold {THRESHOLD_PCT:.0f}%).\n\n"
                f"Top consumers:\n{consumers}"
            )
            LOG.warning("Disk %.1f%% used; alerting", pct)
            if send_telegram(msg):
                state["alerted"] = True
                save_state(state)
        elif pct < THRESHOLD_PCT and already_alerted:
            # Recovered — clear flag so the next crossing fires again.
            state["alerted"] = False
            save_state(state)
            LOG.info("Disk recovered to %.1f%%; clearing alert flag", pct)
        else:
            LOG.info("Disk %.1f%% used (threshold %.0f%%)", pct, THRESHOLD_PCT)

        time.sleep(CHECK_INTERVAL_SEC)


if __name__ == "__main__":
    sys.exit(main())
