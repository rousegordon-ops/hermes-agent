#!/usr/bin/env python3
"""Daily LLM usage report — sends request metrics to Telegram.
Fires daily at 6 AM America/Los_Angeles. Reader for the request log;
gateway/run.py is the writer side.

Metrics:
  - Total API requests in the last 24h
  - User interactions (chat messages) in the last 24h
  - Max API requests in any rolling 5-hour window (24h)
  - Max API requests in any rolling 5-hour window (30d)

Modes:
  python3 cost_report.py            — compute metrics, send report
  python3 cost_report.py --baseline — no-op baseline (for first run)
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
STATE_PATH = os.environ.get("COST_STATE_PATH", "/opt/data/cost-state.json")
REQUEST_LOG_PATH = os.environ.get("REQUEST_LOG_PATH", "/opt/data/request-log.jsonl")


def load_state() -> dict:
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def send_telegram(token: str, chat_id: str, text: str) -> None:
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        headers={"User-Agent": "hermes-agent/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        body = r.read().decode("utf-8")
    if '"ok":true' not in body:
        raise SystemExit(f"telegram send failed: {body}")


def sliding_window_max(entries: list, window_seconds: float) -> int:
    """Return max sum of api_calls in any rolling window of window_seconds."""
    if not entries:
        return 0
    entries.sort(key=lambda x: x[0])
    max_sum = 0
    window_sum = 0
    left = 0
    for right in range(len(entries)):
        window_sum += entries[right][1]
        while entries[right][0] - entries[left][0] > window_seconds:
            window_sum -= entries[left][1]
            left += 1
        max_sum = max(max_sum, window_sum)
    return max_sum


def compute_request_metrics() -> dict:
    """Parse the request log (JSONL) to compute:
    - total_requests_24h: sum of api_calls in the last 24 hours
    - max_requests_5h: max sum of api_calls in any rolling 5-hour window (24h)
    - max_requests_5h_30d: max sum of api_calls in any rolling 5-hour window (30d)
    - interactions_24h: number of user interactions (lines) in the last 24h

    Returns dict with these keys (all 0 if no log data).
    """
    now = datetime.now(PT).timestamp()
    cutoff_24h = now - 86400
    cutoff_30d = now - (30 * 86400)

    entries_24h = []
    entries_30d = []

    try:
        with open(REQUEST_LOG_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    ts = rec.get("ts", 0)
                    api_calls = rec.get("api_calls", 0)
                    if ts >= cutoff_24h:
                        entries_24h.append((ts, api_calls))
                    if ts >= cutoff_30d:
                        entries_30d.append((ts, api_calls))
                except (json.JSONDecodeError, TypeError):
                    continue
    except FileNotFoundError:
        pass

    if not entries_24h:
        return {
            "total_requests_24h": 0,
            "max_requests_5h": 0,
            "max_requests_5h_30d": sliding_window_max(entries_30d, 5 * 3600),
            "interactions_24h": 0,
        }

    total_requests_24h = sum(calls for _, calls in entries_24h)
    interactions_24h = len(entries_24h)

    return {
        "total_requests_24h": total_requests_24h,
        "max_requests_5h": sliding_window_max(entries_24h, 5 * 3600),
        "max_requests_5h_30d": sliding_window_max(entries_30d, 5 * 3600),
        "interactions_24h": interactions_24h,
    }


def prune_old_entries(days_to_keep: int = 30) -> None:
    """Remove request log entries older than N days to prevent unbounded growth."""
    cutoff = datetime.now(PT).timestamp() - (days_to_keep * 86400)
    kept_lines = []
    try:
        with open(REQUEST_LOG_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("ts", 0) >= cutoff:
                        kept_lines.append(line)
                except (json.JSONDecodeError, TypeError):
                    continue
    except FileNotFoundError:
        return

    with open(REQUEST_LOG_PATH, "w") as f:
        for line in kept_lines:
            f.write(line + "\n")


def format_report(metrics: dict) -> str:
    now = datetime.now(PT).strftime("%Y-%m-%d %I:%M %p PT")
    lines = [
        "<b>📊 Usage Report (24H)</b>",
        f"  User Interactions: <b>{metrics['interactions_24h']}</b>",
        f"  API Requests: <b>{metrics['total_requests_24h']}</b>",
        "",
        "<b>📈 Max Req / 5H Window</b>",
        f"  24H: <b>{metrics['max_requests_5h']}</b>",
        f"  30D: <b>{metrics['max_requests_5h_30d']}</b>",
    ]

    if metrics["total_requests_24h"] == 0:
        lines.append("")
        lines.append("  <i>No request data yet — metrics populate after first full day.</i>")

    lines.append("")
    lines.append(f"<i>Snapshot: {now}</i>")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true",
                        help="No-op; save empty state and exit.")
    args = parser.parse_args()

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_HOME_CHANNEL", "").strip()

    if not args.baseline and (not bot_token or not chat_id):
        print("[cost-report] TELEGRAM_BOT_TOKEN or TELEGRAM_HOME_CHANNEL not set",
              file=sys.stderr)
        sys.exit(1)

    metrics = compute_request_metrics()
    state = load_state()
    prev_metrics = state.get("metrics")

    if args.baseline:
        save_state({"metrics": metrics, "at": datetime.now(PT).isoformat()})
        print(f"[cost-report] baseline saved: {metrics}")
        return

    text = format_report(metrics)
    send_telegram(bot_token, chat_id, text)
    save_state({"metrics": metrics, "at": datetime.now(PT).isoformat()})

    # Prune old log entries monthly (keep 30 days)
    prune_old_entries(days_to_keep=30)

    print(f"[cost-report] sent; reqs_24h={metrics['total_requests_24h']}, "
          f"interactions_24h={metrics['interactions_24h']}, "
          f"max_5h_24h={metrics['max_requests_5h']}, max_5h_30d={metrics['max_requests_5h_30d']}")


if __name__ == "__main__":
    main()
