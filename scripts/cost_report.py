#!/usr/bin/env python3
"""Daily LLM cost report — sends OpenRouter balance + 24h spend to Telegram.

v1 ships balance and total spend (computed from snapshot delta). Per-model
breakdown (chat vs opencode), Tavily search count, and 5h peak request rate
are deferred to v2 — those need either OpenRouter analytics access or our
own ledger hooked into Hermes' API call cycle.

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
from datetime import datetime
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
STATE_PATH = os.environ.get("COST_STATE_PATH", "/opt/data/cost-state.json")


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


def format_report(balance: float, prev_balance: float | None) -> str:
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
    lines.append("<i>v1 — per-model breakdown, search count, and peak rate coming soon.</i>")
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

    text = format_report(balance, prev_balance)
    send_telegram(bot_token, chat_id, text)
    save_state({"balance": balance, "at": datetime.now(PT).isoformat()})
    spend_str = f"${prev_balance - balance:.4f}" if prev_balance is not None else "n/a (first run)"
    print(f"[cost-report] sent; balance=${balance:,.4f}, spend={spend_str}")


if __name__ == "__main__":
    main()
