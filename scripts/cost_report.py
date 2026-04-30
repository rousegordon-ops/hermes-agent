#!/usr/bin/env python3
"""Daily LLM usage report — sends request metrics to Telegram.
Fires daily at 6 AM America/Los_Angeles. Reader for the request log;
gateway/run.py is the writer side.

Metrics:
  - Total API requests in the last 24h
  - User interactions (chat messages) in the last 24h
  - Max API requests in any rolling 5-hour window (last 24h)

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


def compute_request_metrics() -> dict:
    """Parse the request log (JSONL) to compute:
    - total_requests_24h: sum of api_calls in the last 24 hours
    - max_requests_5h: max sum of api_calls in any rolling 5-hour window
    - interactions_24h: number of user interactions (lines) in the last 24h

    Returns dict with these keys (all 0 if no log data).
    """
    now = datetime.now(PT).timestamp()
    cutoff_24h = now - 86400  # 24 hours ago

    entries = []  # list of (timestamp, api_calls)
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
                        entries.append((ts, api_calls))
                except (json.JSONDecodeError, TypeError):
                    continue
    except FileNotFoundError:
        pass

    if not entries:
        return {
            "total_requests_24h": 0,
            "max_requests_5h": 0,
            "interactions_24h": 0,
        }

    # Sort by timestamp
    entries.sort(key=lambda x: x[0])

    total_requests_24h = sum(calls for _, calls in entries)
    interactions_24h = len(entries)

    # Sliding 5-hour window for max requests
    window_seconds = 5 * 3600
    max_requests_5h = 0

    # Two-pointer sliding window
    window_sum = 0
    left = 0
    for right in range(len(entries)):
        window_sum += entries[right][1]
        # Shrink window from left if it exceeds 5 hours
        while entries[right][0] - entries[left][0] > window_seconds:
            window_sum -= entries[left][1]
            left += 1
        max_requests_5h = max(max_requests_5h, window_sum)

    return {
        "total_requests_24h": total_requests_24h,
        "max_requests_5h": max_requests_5h,
        "interactions_24h": interactions_24h,
    }


def prune_old_entries(days_to_keep: int = 7) -> None:
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


def format_report(metrics: dict, prev_metrics: dict | None) -> str:
    now = datetime.now(PT).strftime("%Y-%m-%d %I:%M %p PT")
    lines = [
        "<b>📊 Request Metrics (24H)</b>",
        f"  API Requests: <b>{metrics['total_requests_24h']}</b>",
        f"  User Interactions: <b>{metrics['interactions_24h']}</b>",
        f"  Max Requests / 5h Window: <b>{metrics['max_requests_5h']}</b>",
    ]

    if prev_metrics:
        delta_interactions = metrics['interactions_24h'] - prev_metrics.get('interactions_24h', 0)
        delta_sign = "+" if delta_interactions >= 0 else ""
        lines.append(f"  vs Prior Day: <b>{delta_sign}{delta_interactions}</b> interactions")

    if metrics["total_requests_24h"] == 0:
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

    text = format_report(metrics, prev_metrics)
    send_telegram(bot_token, chat_id, text)
    save_state({"metrics": metrics, "at": datetime.now(PT).isoformat()})

    # Prune old log entries weekly (keep 7 days)
    prune_old_entries(days_to_keep=7)

    print(f"[cost-report] sent; reqs_24h={metrics['total_requests_24h']}, "
          f"interactions_24h={metrics['interactions_24h']}, max_5h={metrics['max_requests_5h']}")


if __name__ == "__main__":
    main()
