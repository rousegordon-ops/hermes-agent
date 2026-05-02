#!/usr/bin/env python3
"""Wrapper that reads Telegram tokens from /opt/data/.env.tokens and execs cost_report_daemon.py.
Uses os.execve so the daemon directly inherits this process's environment."""
import os

TOKEN_FILE = "/opt/data/.env.tokens"

with open(TOKEN_FILE) as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

os.execve(
    "/usr/bin/python3",
    ["/usr/bin/python3", "/opt/hermes/scripts/cost_report_daemon.py"],
    os.environ,
)
