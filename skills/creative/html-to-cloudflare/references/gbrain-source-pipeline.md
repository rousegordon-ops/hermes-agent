# gbrain as source for hermes-pages content

Use this when regenerating or building a `hermes-pages` HTML page from a **gbrain** markdown source rather than the hand-edited HTML wiki at `/opt/data/hermes-pages/wiki/`.

## Which source feeds which page

`hermes-pages` is fed by two independent content stores, and pages can come from either:

| Source | Location | Format | Examples |
|--------|----------|--------|----------|
| Static HTML wiki | `/opt/data/hermes-pages/wiki/` | hand-edited `.html` (new/updated content pages are public by default unless Gordon explicitly asks for auth; some legacy/private pages still use `wiki_auth=GW2026`) | `/wiki/entities/gordon-rouse`, `/wiki/hobbies/hiking`, `/wiki/projects/...` |
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

When Gordon says `hermes-memories.html` looks repetitive/gibberish, has no memories, or asks whether Hermes Memories is working, do not detour into the static wiki unless he explicitly asks about it. Answer the binary first:

1. Export gbrain with the correct environment:
   ```bash
   export PATH=/opt/data/.bun/bin:$PATH
   export HOME=/opt/data
   TMP=$(mktemp -d)
   gbrain export --dir "$TMP"
   ```
2. Count exported markdown files and compare with rendered sections in `/opt/data/hermes-pages/hermes-memories.html` (`<section class="page" ...>`, not `<article>` or `.page-section`).
3. If counts and page sections match, Hermes Memories is rendering accurately and the issue is gbrain content quality/population.
   - If gbrain only has scaffold/core pages (`index`, `log/log`, `readme`, `schema`) or almost no durable content, create/import curated markdown pages in `/opt/data/gbrain-content` rather than padding the HTML generator.
   - Keep visible page content only from the current gbrain export; generated HTML/CSS is just presentation.
4. If counts/previews differ, fix the generator before blaming gbrain.
5. Check organic capture wiring:
   - `memory.provider` should be `gbrain` in `/opt/data/config.yaml`.
   - `/opt/data/plugins/gbrain/` should exist.
   - `gbrain sources list` and `gbrain list -n 50` should show the expected source pages after a completed import/sync.

Avoid saying “the wiki pages are separate” as the first response when Gordon’s intent is inspecting gbrain. That framing confused the issue; lead with “Hermes Memories is/is not an accurate render of current gbrain export.”

## Hermes → gbrain capture policy

Gordon does **not** want gbrain to be a redundant dump of native Hermes memory or raw conversation logs. Treat gbrain as curated durable knowledge. The local provider at `/opt/data/plugins/gbrain/` defaults `capture_raw_turns=false` and `capture_memory_writes=false`; do not re-enable raw `sessions/` or `memory-writes/` capture unless Gordon explicitly asks for debugging/audit capture.

If `gbrain export` or `hermes-memories.html` shows `sessions/YYYY-MM`, `memory-writes/*`, `memory`, or `user`, remove/archive those from active gbrain before regenerating the HTML mirror. Raw captures belong outside synced gbrain content (e.g. `/opt/data/gbrain-archive/`) until synthesized.

## Rendering gbrain → hermes-memories.html

The canonical generator lives at:

```
/opt/data/skills/creative/html-to-cloudflare/scripts/gbrain-to-hermes-memories.py
```

(A canonical copy is also at `/opt/data/scripts/gbrain-to-hermes-memories.py` for cron / out-of-skill use.)

It runs `gbrain export` to a temp dir, strips YAML frontmatter, converts each page's markdown to HTML (headings, paragraphs, code blocks, blockquotes, lists, tables, `[[wikilinks]]`), and composes only the exported gbrain pages. Do not add visible chrome that is not in gbrain itself: no auth gate, generated timestamp, stats, explanatory hero, or memory/wiki framing.

```bash
# Regenerate
python3 /opt/data/skills/creative/html-to-cloudflare/scripts/gbrain-to-hermes-memories.py

# Deploy (Cloudflare Pages project is Direct Upload — git push is not enough)
npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages \
  --project-name hermes-pages --commit-dirty=true

# Verify live: no broken in-page anchors, and no non-gbrain chrome
python3 - <<'PY'
import re, urllib.request
url='https://hermes-pages-d55.pages.dev/hermes-memories.html'
html=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode('utf-8','replace')
ids=set(re.findall(r'\bid="([^"]+)"', html))
hrefs=re.findall(r'href="#([^"]+)"', html)
assert not [h for h in hrefs if h not in ids]
for needle in ['Hermes Memories','Generated from gbrain','gbrain pages','hermes_memories_auth','Sign in']:
    assert needle not in html, needle
print('ok', url, len(html))
PY
```

Page order is controlled by the `PAGE_ORDER` list at the top of the script. To add new pages, just regenerate after `gbrain sync` — anything exported that isn't in `PAGE_ORDER` is appended alphabetically.

## Pitfalls

- **The page must not contain non-gbrain visible content.** Gordon wants `hermes-memories.html` to be a mirror of current `gbrain export`, not a branded app. Do not add an auth/login gate, hero, stats, generated timestamp, explanatory provenance text, or TOC unless those strings come from gbrain itself. CSS/HTML structure for presentation is fine.
- **Do not emit broken wikilinks.** Use exported slugs as section ids (`index`, `schema`, `readme`, `log-log`). If a `[[target]]` is not present in the current export, render its display text as plain text rather than `<a href="#target">`. Protect inline code before wikilink expansion so examples like ``[[wikilinks]]`` stay literal.
- **Don't conflate `gordons-llm-wiki/` (under `hermes-pages/`) with `gbrain-content/`.** The former is the markdown source for the static HTML wiki (now retired — wiki is hand-edited HTML). The latter is gbrain's source-of-truth git repo. Different content, different pipelines, different cadences.
- **The `gbrain` CLI silently uses `/opt/data/.gbrain` only when `HOME=/opt/data`.** If you forget to set HOME, the brain DB ends up in `~/.gbrain` (e.g. `/root/.gbrain`) and the import appears to "succeed" but lands in the wrong place. Always check the result of `gbrain list` after import.
- **`/opt/data/hermes-pages-repo` does not exist** — that's a deprecated path from older sessions. Use `/opt/data/hermes-pages` directly.
- **Cloudflare deploy is required after every content change** — the project is Direct Upload, not Git Integration. `git push` only updates the GitHub mirror. See the "Critical Deployment Failures" section in the SKILL.md for recovery options when live pages don't update.
