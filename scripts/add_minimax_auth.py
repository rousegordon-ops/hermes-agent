#!/usr/bin/env python3
"""One-shot fixer: add a MiniMax credential to /opt/data/auth.json.

Hermes' env-scan-on-first-boot logic doesn't pick up MINIMAX_API_KEY
automatically — only OPENROUTER_API_KEY. This script reads
MINIMAX_API_KEY from env and adds an entry to credential_pool that
mirrors how OpenRouter is registered, so Hermes routes MiniMax model
calls through the direct API instead of falling back to OpenRouter.

Usage (inside container):
    python3 /opt/hermes/scripts/add_minimax_auth.py
"""

import json
import os
import secrets
import sys
from datetime import datetime, timezone

AUTH_PATH = "/opt/data/auth.json"


def main() -> None:
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not key:
        print("ERROR: MINIMAX_API_KEY not set in env", file=sys.stderr)
        sys.exit(1)

    try:
        with open(AUTH_PATH) as f:
            auth = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {AUTH_PATH} doesn't exist — restart container first", file=sys.stderr)
        sys.exit(1)

    pool = auth.setdefault("credential_pool", {})
    minimax_entries = pool.setdefault("minimax", [])

    # Idempotent: if an env-sourced minimax entry exists, just refresh
    # its access_token and updated_at. Otherwise append a new one.
    new_id = secrets.token_hex(3)
    entry = {
        "id": new_id,
        "label": "MINIMAX_API_KEY",
        "auth_type": "api_key",
        "priority": 0,
        "source": "env:MINIMAX_API_KEY",
        "access_token": key,
        "last_status": None,
        "last_status_at": None,
        "last_error_code": None,
        "last_error_reason": None,
        "last_error_message": None,
        "last_error_reset_at": None,
        "base_url": "https://api.minimax.io/anthropic",
        "request_count": 0,
    }

    existing_idx = next(
        (i for i, e in enumerate(minimax_entries) if e.get("source") == "env:MINIMAX_API_KEY"),
        None,
    )
    if existing_idx is not None:
        # Preserve id + counters, refresh token + base_url
        old = minimax_entries[existing_idx]
        old["access_token"] = key
        old["base_url"] = "https://api.minimax.io/anthropic"
        action = f"refreshed (id {old['id']})"
    else:
        minimax_entries.append(entry)
        action = f"added (id {new_id})"

    auth["updated_at"] = datetime.now(tz=timezone.utc).isoformat()

    with open(AUTH_PATH, "w") as f:
        json.dump(auth, f, indent=2)

    print(f"minimax credential {action} in {AUTH_PATH}")


if __name__ == "__main__":
    main()
