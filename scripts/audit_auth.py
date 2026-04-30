#!/usr/bin/env python3
"""Print a redacted summary of /opt/data/auth.json — provider, token
fingerprint, last status. Diagnostic only."""
import json
import os
import sys

AUTH = os.environ.get("HERMES_AUTH_PATH", "/opt/data/auth.json")
try:
    with open(AUTH) as f:
        d = json.load(f)
except FileNotFoundError:
    print(f"missing: {AUTH}")
    sys.exit(1)

for prov, entries in d.get("credential_pool", {}).items():
    for e in entries:
        tok = e.get("access_token", "") or ""
        fp = f"{tok[:10]}...{tok[-6:]}" if len(tok) > 16 else "(short)"
        print(
            f"  provider={prov:<10} id={e.get('id','?'):<8} "
            f"source={e.get('source','?'):<28} "
            f"token={fp} "
            f"status={e.get('last_status') or 'OK'}"
        )

print(f"updated_at: {d.get('updated_at')}")
