#!/usr/bin/env python3
"""Set the top-level active_provider in /opt/data/auth.json.

When auth.json has multiple credential-pool entries but no explicit
active_provider, Hermes defaults to whatever's first — which gives
the wrong routing if a newer provider was added after the original
seed. This script sets active_provider explicitly.

Usage:
    python3 set_active_provider.py minimax
"""
import json
import os
import sys

AUTH = os.environ.get("HERMES_AUTH_PATH", "/opt/data/auth.json")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <provider_id>", file=sys.stderr)
        sys.exit(1)
    provider = sys.argv[1].strip().lower()

    with open(AUTH) as f:
        auth = json.load(f)

    pool = auth.get("credential_pool", {})
    if provider not in pool:
        print(f"ERROR: '{provider}' not in credential_pool. Available: {list(pool)}",
              file=sys.stderr)
        sys.exit(1)

    old = auth.get("active_provider")
    auth["active_provider"] = provider

    with open(AUTH, "w") as f:
        json.dump(auth, f, indent=2)

    print(f"active_provider: {old!r} -> {provider!r}")


if __name__ == "__main__":
    main()
