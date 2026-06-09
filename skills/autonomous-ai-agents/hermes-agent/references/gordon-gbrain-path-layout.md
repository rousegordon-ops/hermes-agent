# Gordon GBrain Path Layout

Session learning: Gordon wants GBrain organized like upstream `garrytan/gbrain` to avoid merge confusion and repeated ambiguity between Hermes native memory, gbrain source code, runtime DB/config, and content sources.

## Upstream gbrain convention

Original gbrain separates three axes:

- **Source repo / app code**: cloned implementation repo, e.g. `~/gbrain`.
- **Runtime config + local DB**: `~/.gbrain/config.json` and `~/.gbrain/brain.pglite` by default. If `GBRAIN_HOME=/opt/data`, gbrain appends `.gbrain`, so runtime path is `/opt/data/.gbrain/brain.pglite`.
- **Content sources**: independent repos/folders registered inside the brain DB with `gbrain sources add <id> --path <path>`. A source is selected by `--source`, `GBRAIN_SOURCE`, `.gbrain-source`, or registered `local_path` matching.

## Gordon Railway layout after this session

- **Hermes native memory hot-cache**: `/opt/data/memories`
  - Keep this for Hermes built-in memory only: `MEMORY.md`, `USER.md`, lock files.
  - Do not call this gbrain content.
- **Durable gbrain-style markdown content source**: `/opt/data/gbrain-content`
  - Contains `SCHEMA.md`, `index.md`, `entities/`, `concepts/`, `projects/`, `queries/`, `raw/`, etc.
- **GBrain source repo copy**: `/opt/data/repos/gbrain`
  - Use this for upstream pulls/merge work, not `/opt/data/gbrain`.
- **GBrain runtime/config/DB convention**: `/opt/data/.gbrain`
  - Intended upstream-style runtime location; note it was root-owned in the observed Railway volume.
- **Legacy leftover**: `/opt/data/gbrain`
  - Root-owned gbrain source checkout still existed and could not be moved/deleted by the Hermes user. Avoid using it for future source work unless ownership is fixed.

## Migration/verification pattern

Before making changes:

```bash
printf 'HERMES_HOME=%s\n' "$HERMES_HOME"
for p in /opt/data/memories /opt/data/gbrain-content /opt/data/repos/gbrain /opt/data/gbrain /opt/data/.gbrain; do
  if [ -e "$p" ]; then stat -c '%A %U:%G %n' "$p"; else echo "$p missing"; fi
done
```

Safe split used in this session:

```bash
mkdir -p /opt/data/gbrain-content /opt/data/repos
# Leave /opt/data/memories/MEMORY.md and USER.md in place.
for item in SCHEMA.md index.md comparisons concepts entities hobbies log projects queries raw; do
  [ -e "/opt/data/memories/$item" ] && mv "/opt/data/memories/$item" /opt/data/gbrain-content/
done
# If /opt/data/gbrain is root-owned and cannot be moved, copy instead:
cp -a --no-preserve=ownership /opt/data/gbrain /opt/data/repos/gbrain
```

Verification:

```bash
git -C /opt/data/repos/gbrain status --short
find /opt/data/memories -maxdepth 1 -mindepth 1 -printf '%f\n' | sort
find /opt/data/gbrain-content -maxdepth 1 -mindepth 1 -printf '%f\n' | sort

# Runtime readiness is separate from source/content layout:
for c in gbrain bun node npm; do
  if command -v "$c" >/dev/null 2>&1; then
    echo "$c=$(command -v "$c")"
    "$c" --version 2>/dev/null | head -1 || true
  else
    echo "$c=missing"
  fi
done
```

Expected:

- `/opt/data/memories` has only native memory files plus locks/git metadata.
- `/opt/data/gbrain-content` has durable markdown content directories.
- `/opt/data/repos/gbrain` is a clean source checkout.
- `gbrain` on PATH means Hermes can invoke the CLI directly; a clean `/opt/data/repos/gbrain` checkout alone does **not** prove runtime CLI readiness. If `gbrain=missing` and `bun=missing`, the pull-in/layout is good but install/linking still remains before direct `gbrain` calls will work.

## Dream maintenance and health cleanup

When Gordon asks about the nightly “GBrain Dream” message or to fix dream warnings, inspect the latest cron session first (usually `/opt/data/sessions/session_cron_911ffb23e86b_*.json`) and then rerun explicitly:

```bash
export PATH=/opt/data/.bun/bin:$PATH HOME=/opt/data
cd /opt/data/repos/gbrain
gbrain dream 2>&1
```

Use `HOME=/opt/data` for Gordon's Railway runtime checks. In practice, `GBRAIN_HOME=/opt/data` alone can still leave the CLI looking under `/opt/data/home/.gbrain`, which makes `gbrain doctor`/`dream` report “No brain configured” even though `/opt/data/.gbrain/config.json` exists.

Important discovered behavior:

- `gbrain dream` resolves its filesystem brain directory from `sync.repo_path` unless `--dir` is passed.
- If `sync.repo_path` points at `/opt/data/memories`, the lint phase checks Hermes native `MEMORY.md`/`USER.md` and reports `no-frontmatter` issues. That is the wrong target for gbrain content cleanup.
- Gordon's current intended value is:
  ```bash
  gbrain config set sync.repo_path /opt/data/gbrain-content
  ```
- `/opt/data/gbrain-content` should be a git repo; otherwise dream/sync can fail with `Not a git repository: /opt/data/gbrain-content`.
- If `gbrain dream` reports Google embedding key errors in cron but embeddings work interactively, suspect cron environment propagation before editing content. Never print or paste the secret value; reference only `$GOOGLE_GENERATIVE_AI_API_KEY`.

### Fixing lint and orphan warnings

The successful cleanup pattern was:

```bash
export PATH=/opt/data/.bun/bin:$PATH HOME=/opt/data

# Confirm what dream will lint/sync.
gbrain config get sync.repo_path

# Lint the real content source, not native memory.
gbrain lint /opt/data/gbrain-content
```

# Then ensure the content source is a git repo.
git -C /opt/data/gbrain-content rev-parse --is-inside-work-tree || git -C /opt/data/gbrain-content init

# Import updated markdown and wire graph edges if root-slug wikilinks are not extracted.
gbrain import /opt/data/gbrain-content --no-embed
gbrain link log/log index --type references
gbrain link index memory --type references
gbrain link index user --type references
gbrain link index readme --type references
gbrain link index schema --type references

# Verify.
gbrain dream
gbrain dream --phase lint --json
gbrain orphans --json
```

Note: gbrain's markdown wikilink extractor is currently directory-prefix-whitelisted, so root-level `[[memory]]`, `[[user]]`, `[[readme]]`, `[[schema]]`, and `[[index]]` links may not create DB edges automatically. Manual `gbrain link ...` commands are a reliable fix for root-level core pages.

Expected healthy signals:

- `Brain is healthy` from `gbrain dream`.
- `gbrain dream --phase lint --json` shows `status: clean`, `brain_dir: /opt/data/gbrain-content`, and `0 remaining`.
- `gbrain orphans --json` shows `total_orphans: 0`.

## Upstream source pulls / fast-forwards

When Gordon asks to pull specific upstream gbrain commits, operate in `/opt/data/repos/gbrain` and verify whether the requested SHAs are already in the linear upstream path:

```bash
cd /opt/data/repos/gbrain
git fetch origin --tags --prune
for c in <sha1> <sha2>; do git show --stat --oneline --no-renames "$c" | sed -n '1,80p'; done
git log --oneline --ancestry-path HEAD..<target-sha>
git merge-base --is-ancestor HEAD <target-sha> && git merge --ff-only <target-sha>
```

If a fast-forward fails with permission errors under root-owned test fixtures (observed: `test/regressions/`), avoid fighting ownership from the Hermes user. Reset the partial checkout, then use sparse checkout to exclude the unwritable fixture directory and retry the fast-forward:

```bash
git reset --hard HEAD
git clean -fd
stat -c '%A %U:%G %n' test/regressions 2>/dev/null || true

git sparse-checkout init --no-cone
printf '/*\n!test/regressions/\n' > .git/info/sparse-checkout
git read-tree -mu HEAD || true
git merge --ff-only <target-sha>
```

After the pull:

```bash
export PATH=/opt/data/.bun/bin:$PATH HOME=/opt/data
bun install
bun run build
gbrain version
gbrain apply-migrations --yes --non-interactive
git diff --check -- .
git grep -n -E '^(<<<<<<<|=======|>>>>>>>)($| )' -- ':!llms-full.txt' ':!CHANGELOG.md' ':!CLAUDE.md' || true
bun run test
gbrain doctor --fast
gbrain dream
git status --short
```

If `bun run test` gets killed in Railway due to memory/parallel-shard pressure, do not treat the raw shard output as a code failure by default. Inspect `.context/test-failures.log`, rerun any explicit `(fail)` tests/files directly with `bun test <file>`, and report the distinction between environment kill (`rc=137`/`Killed`) and a reproducible test failure. Avoid bare `bun test` as the full-suite command here; it bypasses the repo’s `scripts/run-unit-parallel.sh` wrapper and is more likely to flood the container.

`llms-full.txt`, `CHANGELOG.md`, and some generated/docs files may legitimately contain conflict-marker strings as quoted historical content; prefer anchored `git grep` with exclusions instead of a naive whole-tree text scan.

## GBrain content quality / redundancy policy

Gordon does not want gbrain to be a redundant dump of Hermes native memory or raw conversation/session logs. Redundancy is bad. Treat gbrain as durable curated knowledge, not another transcript store.

Current corrective policy:

- Do not mirror native memory hot-cache pages (`memory`, `user`) into gbrain content.
- Do not keep `memory-writes/*` audit logs in active gbrain content.
- Do not append raw completed Telegram turns into active gbrain pages by default.
- Raw captures, if temporarily needed for debugging, belong outside the synced content source (e.g. `/opt/data/gbrain-archive/`) until synthesized.
- `hermes-memories.html` should be a mirror of current `gbrain export`: visible content must come from exported gbrain pages only. Presentation CSS/section wrappers are OK; do not add separate auth, hero/stats, generated timestamp, or explanatory page chrome. Broken wikilinks to absent pages (`memory`, `user`, etc.) should render as plain text, not dead anchors.

The local `/opt/data/plugins/gbrain` provider was changed to default `capture_raw_turns=false` and `capture_memory_writes=false`; code changes require a Railway restart to affect the long-running gateway.

## Pitfalls

- Do not use `/opt/data/memories` as a durable gbrain content path; it collides with Hermes native memory and confuses future sessions.
- Do not do upstream gbrain merge/pull work in `/opt/data/gbrain`; it may be a root-owned legacy checkout. Prefer `/opt/data/repos/gbrain`.
- Do not assume `/opt/data/.gbrain` is writable; check ownership first.
- Do not assume `GBRAIN_HOME=/opt/data` selects `/opt/data/.gbrain` in this Railway environment; for runtime verification, set `HOME=/opt/data` as well.
- For upstream source pulls, build after install (`bun run build`) so `/opt/data/.bun/bin/gbrain` reports the newly pulled version before migration/doctor checks.
- Treat `rc=137` or `Killed` during full parallel tests as possible container memory pressure; rerun named failures directly before calling it a regression.
- Original gbrain's “brain” is a DB/runtime concept, not merely a markdown folder named `gbrain`.
- Do not trust a clean `gbrain lint /opt/data/gbrain-content` alone; also verify `gbrain dream --phase lint --json` because dream may be reading a different `sync.repo_path`.
- If sparse checkout is enabled to work around root-owned fixtures, mention it in the final status; future full test-suite runs may need ownership fixed or the sparse exclusion removed.
