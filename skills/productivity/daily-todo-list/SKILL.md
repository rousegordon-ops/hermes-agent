---
name: daily-todo-list
description: "Gordon's morning todo list — add items via chat, receive list at 6:05 AM PT, list resets after send."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [telegram, todo, cron, daily-routine]
    homepage: https://github.com/NousResearch/hermes-agent
---

# daily-todo-list

Gordon's daily todo list — sent to Telegram at 6:05 AM PT each morning, then cleared.

## Components

### `/opt/hermes/scripts/todo_manager.py`
Core script. Manages the list in `/opt/data/todo-list.json`.

```bash
python3 /opt/hermes/scripts/todo_manager.py list              # show current list
python3 /opt/hermes/scripts/todo_manager.py add "<item>"     # add item
python3 /opt/hermes/scripts/todo_manager.py clear            # reset list
python3 /opt/hermes/scripts/todo_manager.py send_and_clear   # send to Telegram, then clear
```

### `/opt/hermes/scripts/todo_wrapper.py`
Cron wrapper — reads Telegram tokens from `/opt/data/.env.tokens` and delegates to `todo_manager.py`.

**Why the wrapper?** Cron runs in a subprocess that doesn't inherit the container's env vars (including TELEGRAM_BOT_TOKEN and TELEGRAM_HOME_CHANNEL). The wrapper reads tokens from `/opt/data/.env.tokens` which is populated at container startup.

### `/opt/data/.env.tokens`
Token store. Write the bot token and channel ID here so the cron wrapper can find them:

```
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_HOME_CHANNEL=<chat_id>
```

### Cron job
Scheduled at `5 13 * * *` (6:05 AM PT = 13:05 UTC) to send and clear the list. Cron job ID: `f4e6ed55cf93`.

## Workflow

### Adding items
Gordon says: `todo add <item>` → agent runs the add command **and replies with the full updated list** (numbered, like a text snapshot — not HTML/Telegram formatted, just plain text).

### Listing items
Gordon says: `todo list` → agent runs the list command and replies with the full list (numbered).

## Pitfalls

### Cron schedule is UTC
Hermes cron uses UTC times. To fire at 6:05 AM PT (UTC-8 or UTC-7 PDT), the schedule must be `5 13 * * *` (13:05 UTC). A schedule of `5 6 * * *` fires at 6:05 UTC = 10:05 PM PT the prior day — completely wrong. Always verify the UTC equivalent when setting PT schedules.

### Telegram tokens not in cron subprocess env
The cron daemon runs without the container's env vars. Always use `todo_wrapper.py` in cron — not `todo_manager.py` directly. The wrapper reads tokens from `/opt/data/.env.tokens`.

### Tokens file not populated
The `/opt/data/.env.tokens` file must exist and contain valid credentials. If the container restarts and tokens aren't there, the cron job silently fails to send.

## Modifying the Schedule

```bash
hermes cron edit <job_id> --schedule "5 6 * * *"
```

To change the send time (e.g., 6:00 AM instead of 6:05), edit the cron job.
