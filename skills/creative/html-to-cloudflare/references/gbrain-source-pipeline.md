# gbrain as source for hermes-pages content

Use this when regenerating or building a `hermes-pages` HTML page from a **gbrain** markdown source rather than the hand-edited HTML wiki at `/opt/data/hermes-pages/wiki/`.

## Which source feeds which page

`hermes-pages` is fed by two independent content stores, and pages can come from either:

| Source | Location | Format | Examples |
|--------|----------|--------|----------|
| Static HTML wiki | `/opt/data/hermes-pages/wiki/` | hand-edited `.html` (auth-gated, `wiki_auth=GW2026` cookie) | `/wiki/entities/gordon-rouse`, `/wiki/hobbies/hiking`, all 16 wiki pages |
| gbrain content repo | `/opt/data/gbrain-content/` (git) | `.md` with frontmatter + `[[wikilinks]]` | source-of-truth for the brain content |
| gbrain runtime DB | `/opt/data/.gbrain/brain.pglite` (PGLite) | rows keyed by slug, queryable via `gbrain` CLI | what `gbrain export` reads from |

**`hermes-memories.html` is the canonical example of a gbrain-sourced page.** Its eyebrow div says "Generated from gbrain (runtime DB at /opt/data/.gbrain)" — that is the truth. The page name contains "memories" but it is NOT generated from the static HTML wiki. The naming is historical, not semantic. When Gordon asks "is hermes-memories from gbrain?" the answer is yes — always check the eyebrow rather than pattern-matching the name.

The static HTML wiki at `/opt/data/hermes-pages/wiki/` and the gbrain knowledge base are **independent content stores** with different content, different update cadences, and different deployment pipelines. They are not kept in sync automatically.

## Verifying which source actually produced a page

Before claiming any page is "from gbrain" or "from the wiki":

1. `grep -i "generated from" /opt/data/hermes-pages/<page>.html` — most generated pages include an explicit provenance string in an eyebrow/div.
2. `grep -l "<page-specific-content>" /opt/data/gbrain-content/ /opt/data/hermes-pages/wiki/ 2>/dev/null` — the source dir that contains the page's distinctive content is the one that produced it.
3. The script that generated the file (look in the surrounding session log: `gbrain export`, `md2html.py`, or direct write) is the source of truth.

Never pattern-match the page name to a source ("oh, `hermes-memories` must come from gbrain because the name sounds like memory"). Always read the provenance marker or grep the source.

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

## Diagnosing whether Hermes Memories or gbrain is wrong

When Gordon says `hermes-memories.html` looks repetitive/gibberish or asks whether Hermes Memories is working, do not detour into the static wiki unless he explicitly asks about it. Answer the binary first:

1. Export gbrain with the correct environment:
   ```bash
   export PATH=/opt/data/.bun/bin:$PATH
   export HOME=/opt/data
   TMP=$(mktemp -d)
   gbrain export --dir "$TMP"
   ```
2. Count exported markdown files and compare with rendered sections in `/opt/data/hermes-pages/hermes-memories.html` (`<section class="page" ...>`, not `<article>` or `.page-section`).
3. If counts and previews match, Hermes Memories is rendering accurately and the problem is gbrain content quality/population.
4. If counts/previews differ, fix the generator before blaming gbrain.
5. Check organic capture wiring:
   - `memory.provider` should be `gbrain` in `/opt/data/config.yaml`.
   - `/opt/data/plugins/gbrain/` should exist.
   - `gbrain sources list` and `gbrain list -n 50` should include `sessions/YYYY-MM` after a completed turn or provider smoke test.

Avoid saying “the wiki pages are separate” as the first response when Gordon’s intent is inspecting gbrain. That framing confused the issue; lead with “Hermes Memories is/is not an accurate render of current gbrain export.”

## Organic Hermes → gbrain capture

Gordon's Railway instance has a user-installed Hermes memory provider at:

```
/opt/data/plugins/gbrain/
```

It is enabled with:

```yaml
memory:
  provider: gbrain
```

The provider passively appends completed primary-agent turns to markdown under `/opt/data/gbrain-content/sessions/`, commits the changed markdown locally, then runs:

```bash
gbrain sync --repo /opt/data/gbrain-content --no-embed --no-pull --yes
```

This is what makes gbrain organically accumulate inspectable knowledge without manual imports. Config changes require a fresh agent instance/restart before the gateway uses the provider for future turns. To smoke-test without a live model call, load `plugins.memory.load_memory_provider('gbrain')` with `HERMES_HOME=/opt/data`, call `initialize(...)`, then `sync_turn(...)`, and verify `gbrain list` includes `sessions/YYYY-MM`.

Important implementation detail: `gbrain sync` advances by git commits in `/opt/data/gbrain-content`; writing markdown files alone is not enough. The provider commits changed `sessions/` or `memory-writes/` files locally before running sync. If a future smoke test writes a markdown file but `gbrain list` does not change, check git status/log in `/opt/data/gbrain-content` first.

## Rendering gbrain → hermes-memories.html

The canonical generator lives at:

```
/opt/data/skills/creative/html-to-cloudflare/scripts/gbrain-to-hermes-memories.py
```

(A canonical copy is also at `/opt/data/scripts/gbrain-to-hermes-memories.py` for cron / out-of-skill use.)

It runs `gbrain export` to a temp dir, strips YAML frontmatter, converts each page's markdown to HTML (headings, paragraphs, code blocks, blockquotes, lists, tables, `[[wikilinks]]`), and composes a single-page compendium with TOC + per-page sections. The SHA-256 client-side auth gate from the existing `hermes-memories.html` is preserved verbatim so Gordon's credentials keep working.

```bash
# Regenerate
python3 /opt/data/skills/creative/html-to-cloudflare/scripts/gbrain-to-hermes-memories.py

# Deploy (Cloudflare Pages project is Direct Upload — git push is not enough)
npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages \
  --project-name hermes-pages --commit-dirty=true

# Verify live
curl -s https://hermes-pages-d55.pages.dev/hermes-memories | grep -E "eyebrow|gbrain pages"
```

Page order is controlled by the `PAGE_ORDER` list at the top of the script. To add new pages, just regenerate after `gbrain sync` — anything exported that isn't in `PAGE_ORDER` is appended alphabetically.

## Pitfalls

- **Don't trust stale stats in the page itself.** The page shows a "N gbrain pages" stat. After running `gbrain sync` to ingest new content, regenerate the page so the stat reflects current state. Gordon will notice if it says "6 pages" but the TOC clearly has more.
- **Don't conflate `gordons-llm-wiki/` (under `hermes-pages/`) with `gbrain-content/`.** The former is the markdown source for the static HTML wiki (now retired — wiki is hand-edited HTML). The latter is gbrain's source-of-truth git repo. Different content, different pipelines, different cadences.
- **The `gbrain` CLI silently uses `/opt/data/.gbrain` only when `HOME=/opt/data`.** If you forget to set HOME, the brain DB ends up in `~/.gbrain` (e.g. `/root/.gbrain`) and the import appears to "succeed" but lands in the wrong place. Always check the result of `gbrain list` after import.
- **`/opt/data/hermes-pages-repo` does not exist** — that's a deprecated path from older sessions. Use `/opt/data/hermes-pages` directly.
- **Cloudflare deploy is required after every content change** — the project is Direct Upload, not Git Integration. `git push` only updates the GitHub mirror. See the "Critical Deployment Failures" section in the SKILL.md for recovery options when live pages don't update.
- **`hermes-memories.html` auth gate uses a separate cookie (`hermes_memories_auth=1`) and a different password from the wiki.** Don't reuse the `wiki_auth=GW2026` cookie on this page — it lives at root scope, not `/wiki/`. The two pages have independent auth.
