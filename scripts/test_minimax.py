#!/usr/bin/env python3
"""One-shot diagnostic: send a tiny chat request to MiniMax's
Anthropic-compatible endpoint using whatever API key is in the
container env. Prints the result or the HTTP error body.

Usage (inside container):
    python3 /opt/hermes/scripts/test_minimax.py [--cn]

--cn switches to the China endpoint and uses MINIMAX_CN_API_KEY.
"""
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> None:
    use_cn = "--cn" in sys.argv
    if use_cn:
        base = "https://api.minimaxi.com/anthropic"
        key_var = "MINIMAX_CN_API_KEY"
    else:
        base = "https://api.minimax.io/anthropic"
        key_var = "MINIMAX_API_KEY"

    key = os.environ.get(key_var, "").strip()
    if not key:
        print(f"ERROR: {key_var} not set in env")
        sys.exit(1)

    print(f"Endpoint: {base}/v1/messages")
    print(f"Auth env: {key_var} (len={len(key)}, prefix={key[:6]}...)")
    print()

    body = json.dumps({
        "model": "MiniMax-M2.7",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "say hi"}],
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base}/v1/messages",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print("HTTP", r.status)
            print(r.read().decode("utf-8")[:800])
    except urllib.error.HTTPError as e:
        print("HTTP", e.code)
        try:
            print(e.read().decode("utf-8")[:800])
        except Exception:
            print("<no body>")
    except Exception as e:
        print(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
