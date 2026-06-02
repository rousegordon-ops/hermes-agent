# gbrain as source for hermes-pages content

Use this when regenerating or building a `hermes-pages` HTML page from a **gbrain** markdown source rather than the hand-edited HTML wiki at `/opt/data/hermes-pages/wiki/`.

## Two parallel content sources for hermes-pages

`hermes-pages` is fed by two independent content stores, and pages can come from either:

| Source | Location | Format | Current example |
|--------|----------|--------|-----------------|
| Static HTML wiki | `/opt/data/hermes-pages/wiki/` | hand-edited `.html` (auth-gated) | 16 pages, behind `wiki_auth=GW2026` cookie |
| gbrain content repo | `/opt/data/gbrain-content/` (git) | `.md` with frontmatter + `[[wikilinks]]` | 4 .md files in root, subdirs empty as of 2026-06-02 |
| gbrain runtime DB | `/opt/data/.gbrain/brain.pglite` (PGLite) | rows keyed by slug, queryable via `gbrain` CLI | 7 stub rows: index, log/log, readme, schema, user, memory |

**Generated pages** like `hermes-memories.html` (single-page wiki compendium) have a "Generated from <source>" eyebrow that names which store fed it. The current `hermes-memories.html` says **"Generated from /opt/data/hermes-pages/wiki"** — i.e. the static HTML wiki, NOT gbrain.

When Gordon asks to regenerate a generated page from gbrain, expect a **content regression** unless the gbrain store has been kept in sync with the static wiki. As of 2026-06-02 it has not — gbrain is mostly stubs.

## Verifying which source actually produced a page

Before claiming any page is "from gbrain" or "from the wiki":

1. `grep -i "generated from" /opt/data/hermes-pages/<page>.html` — most generated pages include an explicit provenance string in an eyebrow/div.
2. `grep -l "<page-specific-content>" /opt/data/hermes-content/ /opt/data/hermes-pages/wiki/ 2>/dev/null` — the source dir that contains the page's distinctive content is the one that produced it.
3. The script that generated the file (look in the surrounding session log: `gbrain export`, `md2html.py`, or direct write) is the source of truth.

Never pattern-match the page name to a source ("oh, `hermes-memories` must come from gbrain"). The naming is historical, not semantic.

## gbrain content sync workflow

To bring gbrain in sync with the static HTML wiki (or any markdown source) before regenerating a generated page:

```bash
# 1. Ensure gbrain CLI is on PATH and HOME is /opt/data (so the brain DB lives at /opt/data/.gbrain)
export PATH=/opt/data/.bun/bin:$PATH
export HOME=/opt/data

# 2. Inspect current state
gbrain list -n 200

# 3a. Pull a markdown directory into the brain (idempotent)
gbrain import /opt/data/hermes-pages/gordons-llm-wiki --no-embed

# 3b. Or sync the gbrain-content git repo into the brain (preserves git history)
gbrain sync --repo /opt/data/gbrain-content

# 4. Verify
gbrain list -n 200
gbrain get <slug>
```

The `gbrain sync` command is incremental — it only ingests new/changed files. Use `--watch` for a continuous loop or `--install-cron` for a persistent daemon.

## Rendering gbrain → hermes-pages HTML

There is no canonical `gbrain → hermes-pages` script in the repo as of 2026-06-02. To build a new one or update an existing one:

1. `gbrain export --dir /tmp/gbrain-export/` to dump all pages as markdown (uses frontmatter, slug-based filenames).
2. Run the existing `scripts/md2html.py` (lives at `/opt/data/hermes-pages/scripts/md2html.py` and `/opt/data/skills/creative/html-to-cloudflare/scripts/md2html.py`) over the export dir. It already understands Karpathy's LLM Wiki format: `[[wikilinks]]`, `## Facts` fences, etc.
3. Inline the generated pages into a single HTML compendium (the current `hermes-memories.html` pattern) using the same Python style as the 2026-05-16 generator — see the active session log if the script has been removed and needs to be rebuilt.
4. Deploy via wrangler: `npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages --commit-dirty=true`. **Git push alone is not enough — the project is Direct Upload.**

## Pitfalls

- **Don't trust "16 wiki pages" stats in the page itself.** The current `hermes-memories.html` says "16 wiki pages" because that was the wiki size when it was generated (2026-05-16). If the wiki has shrunk or grown since, the stat is stale. Always regenerate the page from the current source before showing it to Gordon.
- **Don't conflate `gordons-llm-wiki/` (under `hermes-pages/`) with `gbrain-content/`.** The former is the markdown source for the static HTML wiki (now retired — wiki is hand-edited HTML). The latter is gbrain's source-of-truth git repo. Different content, different pipelines, different cadences.
- **The `gbrain` CLI silently uses `/opt/data/.gbrain` only when `HOME=/opt/data`.** If you forget to set HOME, the brain DB ends up in `~/.gbrain` (e.g. `/root/.gbrain`) and the import appears to "succeed" but lands in the wrong place. Always check the result of `gbrain list` after import.
- **`/opt/data/hermes-pages-repo` does not exist** — that's a deprecated path from older sessions. Use `/opt/data/hermes-pages` directly.
- **Cloudflare deploy is required after every content change** — the project is Direct Upload, not Git Integration. `git push` only updates the GitHub mirror. See the "Critical Deployment Failures" section in the SKILL.md for recovery options when live pages don't update.
