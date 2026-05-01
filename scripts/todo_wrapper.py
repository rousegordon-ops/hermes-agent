#!/usr/bin/env python3
"""Wrapper that reads Telegram tokens from /opt/data/.env.tokens and runs todo_manager.py.
The tokens file is written by the container entrypoint so we don't need env vars in cron sessions."""
import os

TOKEN_FILE = "/opt/data/.env.tokens"

def load_tokens() -> dict:
    tokens = {}
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    tokens[k.strip()] = v.strip()
    return tokens

env = load_tokens()
os.environ.update({
    "TELEGRAM_BOT_TOKEN": env.get("TELEGRAM_BOT_TOKEN", ""),
    "TELEGRAM_HOME_CHANNEL": env.get("TELEGRAM_HOME_CHANNEL", ""),
})

import subprocess
import sys

sys.exit(subprocess.run([sys.executable, "/opt/hermes/scripts/todo_manager.py"] + sys.argv[1:]).returncode)
