#!/usr/bin/env python3
"""
Source-of-truth watcher for the Hermes fork checkout at HERMES_SRC_DIR.

Polls the cloned repo every WATCHER_POLL_SEC. When `git status --porcelain`
shows uncommitted work, starts a debounce timer; each subsequent change
extends it up to a hard ceiling. When the timer expires, runs:

    git add -A
    git commit -m "auto: <ts> — <files>"
    git push origin main

Respects .gitignore via git status. Never resets or destroys local work.

Why this exists: Hermes can autonomously create new skills and edit
existing ones (skill-authoring tools, agent-driven self-improvement).
Without a watcher, those changes live only on the persistent volume and
get out of sync with the GitHub fork — so the next image rebuild has no
record of them, and a volume reset wipes them entirely. The watcher
captures every disk change to source within a few minutes.

Heartbeat: writes a timestamp to HEARTBEAT_PATH every poll so a
separate health check can detect a stuck/crashed watcher.

Required env: nothing. Pushes use the credential helper configured by
the entrypoint (writes ~/.git-credentials from $GITHUB_TOKEN).

Ported from GordonClaw's source_watcher.py with path adjustments.
"""

import os
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone

SRC_DIR = os.environ.get("HERMES_SRC_DIR", "/opt/data/repo")
HEARTBEAT_PATH = os.environ.get(
    "SOURCE_WATCHER_HEARTBEAT", "/opt/data/source-watcher-heartbeat"
)

WATCHER_POLL_SEC = int(os.environ.get("SOURCE_WATCHER_POLL_SEC", "10"))
WATCHER_DEBOUNCE_SEC = int(os.environ.get("SOURCE_WATCHER_DEBOUNCE_SEC", "180"))
WATCHER_CEILING_SEC = int(os.environ.get("SOURCE_WATCHER_CEILING_SEC", "600"))
WATCHER_PUSH_RETRIES = int(os.environ.get("SOURCE_WATCHER_PUSH_RETRIES", "3"))

COMMIT_SUBJECT_FILE_LIMIT = 6


def log(msg: str) -> None:
    print(f"[source-watcher] {msg}", flush=True)


def heartbeat() -> None:
    try:
        with open(HEARTBEAT_PATH, "w") as f:
            f.write(datetime.now(tz=timezone.utc).isoformat())
    except OSError as err:
        log(f"heartbeat write failed: {err}")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", SRC_DIR, *args],
        capture_output=True,
        text=True,
        check=check,
    )


def porcelain_status() -> list[str]:
    try:
        result = git("status", "--porcelain")
    except subprocess.CalledProcessError as err:
        log(f"git status failed: {err.stderr.strip()}")
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def changed_files(porcelain_lines: list[str]) -> list[str]:
    out = []
    for line in porcelain_lines:
        body = line[3:] if len(line) > 3 else line
        if " -> " in body:
            body = body.split(" -> ", 1)[1]
        out.append(body)
    return out


def make_commit_message(files: list[str]) -> str:
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    if len(files) <= COMMIT_SUBJECT_FILE_LIMIT:
        subject = f"auto: {ts} — {' '.join(files)}"
    else:
        head = " ".join(files[:COMMIT_SUBJECT_FILE_LIMIT])
        more = len(files) - COMMIT_SUBJECT_FILE_LIMIT
        subject = f"auto: {ts} — {head} (+{more} more)"
    body = "\n".join(files)
    return f"{subject}\n\nFiles:\n{body}\n"


def commit_and_push() -> bool:
    files = changed_files(porcelain_status())
    if not files:
        log("commit_and_push called but tree is clean; skipping")
        return True

    try:
        git("add", "-A")
    except subprocess.CalledProcessError as err:
        log(f"git add failed: {err.stderr.strip()}")
        return False

    msg = make_commit_message(files)
    try:
        git("commit", "--no-verify", "-m", msg)
    except subprocess.CalledProcessError as err:
        log(f"git commit failed: {err.stderr.strip()}")
        return False

    for attempt in range(1, WATCHER_PUSH_RETRIES + 1):
        try:
            git("push", "origin", "main")
            log(f"committed + pushed {len(files)} file(s)")
            return True
        except subprocess.CalledProcessError as err:
            stderr = (err.stderr or "").strip()
            log(
                f"git push attempt {attempt}/{WATCHER_PUSH_RETRIES} failed: {stderr}"
            )
            if "non-fast-forward" in stderr or "rejected" in stderr:
                log("non-fast-forward; attempting pull --rebase origin main")
                try:
                    git("fetch", "origin", "main")
                    git("rebase", "origin/main")
                    log("rebase succeeded; retrying push")
                    continue
                except subprocess.CalledProcessError as rebase_err:
                    log(
                        f"rebase failed ({rebase_err.stderr.strip()}); "
                        f"aborting and bailing"
                    )
                    try:
                        git("rebase", "--abort", check=False)
                    except Exception:
                        pass
                    return False
            if attempt < WATCHER_PUSH_RETRIES:
                time.sleep(5 * attempt)
    log("git push gave up; commit is local, will push next time tree is dirty")
    return False


def commit_now() -> bool:
    return commit_and_push()


def main() -> None:
    if not os.path.isdir(os.path.join(SRC_DIR, ".git")):
        log(f"FATAL: {SRC_DIR} is not a git repo; exiting")
        sys.exit(1)

    log(
        f"started; src={SRC_DIR} poll={WATCHER_POLL_SEC}s "
        f"debounce={WATCHER_DEBOUNCE_SEC}s ceiling={WATCHER_CEILING_SEC}s"
    )

    first_dirty_at: float | None = None
    last_change_at: float | None = None
    last_porcelain: list[str] = []

    while True:
        try:
            heartbeat()
            porcelain = porcelain_status()
            now = time.monotonic()

            if not porcelain:
                if first_dirty_at is not None:
                    log("tree clean again; clearing debounce")
                first_dirty_at = None
                last_change_at = None
                last_porcelain = []
            else:
                if first_dirty_at is None:
                    first_dirty_at = now
                    last_change_at = now
                    last_porcelain = porcelain
                    log(f"detected {len(porcelain)} change(s); debounce started")
                elif porcelain != last_porcelain:
                    last_change_at = now
                    last_porcelain = porcelain
                    log(f"changes still in flux ({len(porcelain)} files); debounce extended")

                quiet_for = now - (last_change_at or now)
                age = now - first_dirty_at
                if quiet_for >= WATCHER_DEBOUNCE_SEC or age >= WATCHER_CEILING_SEC:
                    if age >= WATCHER_CEILING_SEC and quiet_for < WATCHER_DEBOUNCE_SEC:
                        log(
                            f"hit {WATCHER_CEILING_SEC}s ceiling with edits "
                            f"still arriving; committing anyway"
                        )
                    commit_and_push()
                    first_dirty_at = None
                    last_change_at = None
                    last_porcelain = []

            time.sleep(WATCHER_POLL_SEC)
        except Exception:
            log(f"watcher loop error:\n{traceback.format_exc()}")
            time.sleep(WATCHER_POLL_SEC)


if __name__ == "__main__":
    main()
