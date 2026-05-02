#!/usr/bin/env python3
"""Todo list manager for Gordon — stores list in /opt/data/todo-list.json.

Usage:
  todo_manager.py list              — print current list
  todo_manager.py add "<item>"      — add item
  todo_manager.py clear             — reset list
  todo_manager.py send_and_clear    — send to Telegram, then clear (for cron)
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
TODO_PATH = os.environ.get("TODO_PATH", "/opt/data/todo-list.json")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_HOME_CHANNEL = os.environ.get("TELEGRAM_HOME_CHANNEL", "")


def load() -> list[str]:
    try:
        with open(TODO_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save(items: list[str]) -> None:
    with open(TODO_PATH, "w") as f:
        json.dump(items, f, indent=2)


def send_telegram(text: str) -> None:
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_HOME_CHANNEL,
        "text": text,
        "parse_mode": "HTML",
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data=data,
        headers={"User-Agent": "hermes-agent/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        body = r.read().decode("utf-8")
    if '"ok":true' not in body:
        raise SystemExit(f"telegram send failed: {body}")


def format_list(items: list[str]) -> str:
    if not items:
        return "📋 <b>Todo List (AM)</b>\n\n<i>Nothing on the list today!</i>"
    lines = ["📋 <b>Todo List (AM)</b>", ""]
    for i, item in enumerate(items, 1):
        lines.append(f"  {i}. {item}")
    return "\n".join(lines)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    if cmd == "list":
        items = load()
        if items:
            for item in items:
                print(f"• {item}")
        else:
            print("List is empty.")
        return

    elif cmd == "add":
        item = sys.argv[2] if len(sys.argv) > 2 else ""
        if not item:
            print("Usage: todo add \"<item>\"", file=sys.stderr)
            sys.exit(1)
        items = load()
        items.append(item)
        save(items)
        print(f"Added: {item}")
        print(f"List now has {len(items)} item(s):")
        for i, it in enumerate(items, 1):
            print(f"  {i}. {it}")
        return

    elif cmd == "clear":
        save([])
        print("List cleared.")
        return

    elif cmd == "send_and_clear":
        items = load()
        text = format_list(items)
        send_telegram(text)
        save([])
        now = datetime.now(PT).strftime("%I:%M %p %Z")
        print(f"[todo] sent and cleared at {now} ({len(items)} items)")
        return

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
