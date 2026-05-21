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
export PATH=/opt/data/.bun/bin:$PATH GBRAIN_HOME=/opt/data
cd /opt/data/repos/gbrain
gbrain dream 2>&1
```

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
export PATH=/opt/data/.bun/bin:$PATH GBRAIN_HOME=/opt/data

# Confirm what dream will lint/sync.
gbrain config get sync.repo_path

# Lint the real content source, not native memory.
gbrain lint /opt/data/gbrain-content

# Add/fix YAML frontmatter on content pages and remove placeholder dates.
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

## Pitfalls

- Do not use `/opt/data/memories` as a durable gbrain content path; it collides with Hermes native memory and confuses future sessions.
- Do not do upstream gbrain merge/pull work in `/opt/data/gbrain`; it may be a root-owned legacy checkout. Prefer `/opt/data/repos/gbrain`.
- Do not assume `/opt/data/.gbrain` is writable; check ownership first.
- Original gbrain's “brain” is a DB/runtime concept, not merely a markdown folder named `gbrain`.
- Do not trust a clean `gbrain lint /opt/data/gbrain-content` alone; also verify `gbrain dream --phase lint --json` because dream may be reading a different `sync.repo_path`.
