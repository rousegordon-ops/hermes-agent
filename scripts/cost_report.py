#!/usr/bin/env python3
"""Daily LLM cost report — sends OpenRouter balance + 24h spend + request
metrics to Telegram. Fires daily at 6 AM America/Los_Angeles. Reader for
the request log; gateway/run.py is the writer side. (workflow test 3)

Metrics:
  - OpenRouter balance and 24h spend (from balance snapshot delta)
  - Total API requests in the last 24h
  - Max API requests in any rolling 5-hour window (last 24h)

Modes:
  python3 cost_report.py            — fetch balance, send report, save state
  python3 cost_report.py --baseline — fetch balance, save state, no send
                                       (used at deploy time to seed the
                                       previous-balance snapshot)
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


def get_openrouter_balance(api_key: str) -> float:
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        body = json.loads(r.read().decode("utf-8"))
    d = body.get("data") or body
    if "total_credits" in d and "total_usage" in d:
        return float(d["total_credits"]) - float(d["total_usage"])
    if "balance" in d:
        return float(d["balance"])
    raise SystemExit(f"unexpected /credits response: {body}")


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
        f"https://api.telegram.org/bot{token}/sendMessage", data=data
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


def format_report(balance: float, prev_balance: float | None, metrics: dict) -> str:
    now = datetime.now(PT).strftime("%Y-%m-%d %I:%M %p PT")
    lines = [
        "<b>💰 Financials (24H)</b>",
        f"  OpenRouter Balance: <b>${balance:,.2f}</b>",
    ]
    if prev_balance is None:
        lines.append("  <i>First snapshot — spend available tomorrow.</i>")
    else:
        delta = prev_balance - balance
        if delta < 0:
            # Balance went up — credit was added.
            lines.append(f"  <i>Balance increased by ${-delta:,.2f} since last snapshot (credit added). Spend hidden.</i>")
        else:
            lines.append(f"  <b>TOTAL ESTIMATED SPEND: ${delta:,.4f}</b>")

    lines.append("")
    lines.append("<b>📊 Request Metrics (24H)</b>")
    lines.append(f"  API Requests (24h): <b>{metrics['total_requests_24h']}</b>")
    lines.append(f"  User Interactions (24h): <b>{metrics['interactions_24h']}</b>")
    lines.append(f"  Max Requests in 5h Window: <b>{metrics['max_requests_5h']}</b>")

    if metrics["total_requests_24h"] == 0:
        lines.append("  <i>No request data yet — metrics populate after first full day.</i>")

    lines.append("")
    lines.append(f"<i>Snapshot: {now}</i>")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true",
                        help="Save snapshot without sending Telegram message.")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_HOME_CHANNEL", "").strip()

    if not api_key:
        print("[cost-report] OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not args.baseline and (not bot_token or not chat_id):
        print("[cost-report] TELEGRAM_BOT_TOKEN or TELEGRAM_HOME_CHANNEL not set",
              file=sys.stderr)
        sys.exit(1)

    balance = get_openrouter_balance(api_key)
    state = load_state()
    prev_balance = state.get("balance")

    if args.baseline:
        save_state({"balance": balance, "at": datetime.now(PT).isoformat()})
        print(f"[cost-report] baseline snapshot saved: ${balance:,.4f}")
        return

    metrics = compute_request_metrics()
    text = format_report(balance, prev_balance, metrics)
    send_telegram(bot_token, chat_id, text)
    save_state({"balance": balance, "at": datetime.now(PT).isoformat()})

    # Prune old log entries weekly (keep 7 days)
    prune_old_entries(days_to_keep=7)

    spend_str = f"${prev_balance - balance:.4f}" if prev_balance is not None else "n/a (first run)"
    print(f"[cost-report] sent; balance=${balance:,.4f}, spend={spend_str}, "
          f"reqs_24h={metrics['total_requests_24h']}, max_5h={metrics['max_requests_5h']}")


if __name__ == "__main__":
    main()
