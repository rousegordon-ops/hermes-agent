---
name: html-to-cloudflare
description: "Generate HTML content and publish it to Gordon's Cloudflare Pages site (hermes-pages). Covers the full workflow from HTML generation to live URL."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [html, cloudflare, publishing, static-site]
    homepage: https://github.com/rousegordon-ops/hermes-pages
---

# HTML → Cloudflare Pages

Generate HTML content and publish it to Gordon's personal Cloudflare Pages deployment. **The canonical workflow for any generated HTML that Gordon wants to view live without copy-pasting.**

## Verify pipeline source before answering "is X generated from Y?"

1. **Generate HTML** — write the content to a local file (typically in `/opt/data/repo/` or wherever the work is happening)
2. **Push to hermes-pages** — commit and push to the `hermes-pages` repo. **NOTE: git push to GitHub does NOT trigger Cloudflare deploy for this project.** Confirmed via the Cloudflare API: `POST /accounts/{id}/pages/projects/hermes-pages/deployments/{id}/retry` returns "You cannot retry a Direct Upload deployment. Retries are only possible for builds." The `hermes-pages` project uses **Direct Upload only** — git push to GitHub is for source backup/version control, not deployment. Always follow step 4.
3. **Verify immediately** — always check the deployed URL before declaring success:
   ```python
   import urllib.request
   url = 'https://hermes-pages-d55.pages.dev/<path>'
   req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
   resp = urllib.request.urlopen(req, timeout=30)
   html = resp.read().decode('utf-8', 'replace')
   assert 'expected content' in html, f"Unexpected page: {html[:200]}"
   ```
4. **Deploy via wrangler (REQUIRED, not optional)** — every publish needs a wrangler deploy, even if you just pushed to GitHub:
   ```bash
   cd /opt/data/hermes-pages
   npx -y -p node@22 -p wrangler wrangler pages deploy . --project-name hermes-pages --commit-dirty=true
   ```
   The `--commit-dirty=true` flag deploys the current working tree without requiring a new commit. The deploy prints a preview URL like `https://<hash>.hermes-pages-d55.pages.dev` — the canonical public URL is still `https://hermes-pages-d55.pages.dev/<path>`.

   If `/opt/data/hermes-pages` has unrelated dirty files, do **not** deploy the dirty worktree blindly. Deploy an isolated clone of the committed state instead:
   ```bash
   rm -rf /tmp/hermes-pages-deploy
   git clone --no-local /opt/data/hermes-pages /tmp/hermes-pages-deploy
   npx -y -p node@22 -p wrangler wrangler pages deploy /tmp/hermes-pages-deploy --project-name hermes-pages --commit-dirty=true
   ```

## Git credentials setup (critical)

The `publish_html` tool requires `GITHUB_TOKEN` in the environment. It's NOT automatically set — read it from the credentials file:

```python
import re
with open('/opt/data/.git-credentials') as f:
    cred = f.read()
m = re.search(r'x-access-token:([^\@]+)\@', cred)
token = m.group(1) if m else ''
os.environ['GITHUB_TOKEN'] = token
```

The credentials file has the format: `https://x-access-token:{github_pat_...}@github.com`

### Git push to hermes-pages

**Always configure git identity before committing to hermes-pages** (different from hermes-agent repo):

```bash
git config user.email "hermes@hermes-agent.local"
git config user.name "Hermes"
```

Always use `GIT_TERMINAL_PROMPT=0` to avoid interactive prompts:
```bash
GIT_TERMINAL_PROMPT=0 git push origin main
```

### Pushing to hermes-pages repo directly

If `publish_html` isn't available or you need to push manually:

```bash
cd /opt/data/hermes-pages
git config user.email "hermes@hermes-agent.local"
git config user.name "Hermes"
git add <file>
git commit -m "<message>"
GIT_TERMINAL_PROMPT=0 git push origin main
```

**Always use `GIT_TERMINAL_PROMPT=0`** — avoids interactive SSH/GitHub prompts that would hang.

**Source dir is `/opt/data/hermes-pages` — NOT `/opt/data/hermes-pages-repo`.** The skill previously misnamed this throughout. The canonical paths:

| Path | What it is |
|------|------------|
| `/opt/data/hermes-pages` | Live deploy source — where HTML files live and get pushed from |
| `/opt/data/hermes-pages-repo` | Does NOT exist — do not use |
| `/opt/data/gordon-pages` | Gordon's SW engineering wiki source (separate Cloudflare Pages project) |

**Key reminders:**
- The hub index lives at `/opt/data/hermes-pages/wiki/index.html` (not a separate repo subdirectory)
- Git push from `/opt/data/hermes-pages` directly — no intermediate repo clone needed
- The wiki lives at `/opt/data/hermes-pages/wiki/` — write HTML files there, push, deploy auto-runs
- **Default public:** any page Gordon asks you to create, update, publish, or share should be public unless he specifically asks for private/auth-gated access. Do not add or preserve `wiki_auth` on pages by default. Existing unrelated private pages should be left alone.
- When making a page public, remove/redact booking numbers, reservation IDs, confirmation codes, tokens, credentials, and other sensitive identifiers from user-visible HTML while preserving useful non-sensitive logistics.

## Key repos and URLs

| Repo | URL | Project name | Source dir |
|------|-----|--------------|------------|
| hermes-pages repo | `https://github.com/rousegordon-ops/hermes-pages` | `hermes-pages` | `/opt/data/hermes-pages` |
| Gordon's SW engineering wiki | `https://github.com/rousegordon-ops/hermes-pages` | `gordon-pages` | `/opt/data/gordon-pages` |
| Current public hermes-pages deployment | `https://hermes-pages-d55.pages.dev/` | `hermes-pages` | `/opt/data/hermes-pages` |
| Current public gordon-pages deployment | `https://gordon-pages.pages.dev/` | `gordon-pages` | `/opt/data/gordon-pages` |
| Hermes-agent repo | `https://github.com/rousegordon-ops/hermes-agent` | — | — |
| Gordon's GitHub org/user | `https://github.com/rousegordon-ops` | — | — |

**⚠️ Two separate Cloudflare Pages projects.** Deleting or deploying files affects only the project whose `--project-name` matches. Always verify `wrangler pages project list` output if unsure which project a source dir maps to.

**⚠️ Pre-deletion checklist.** Before deleting any file, directory, or wiki:
1. Confirm the target URL with the user (e.g. "delete the wiki at hermes-pages-d55.pages.dev/wiki/")
2. Check `wrangler pages project list` to see which project the source dir belongs to
3. If the user references a URL, map it to the correct source dir using the table above
4. A URL like `gordon-pages.pages.dev` maps to `/opt/data/gordon-pages/`, NOT `/opt/data/hermes-pages/`
5. **Ask the user to confirm** before running any destructive command — do not assume from context alone

## Current direct deploy workflow

| Deployment target | Source dir | Deploy command |
|-----------------|-----------|----------------|
| hermes-pages-d55.pages.dev | `/opt/data/hermes-pages` | `wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages` |
| gordon-pages.pages.dev | `/opt/data/gordon-pages` | `wrangler pages deploy /opt/data/gordon-pages --project-name gordon-pages` |

Always use `npx -y -p node@22 -p wrangler wrangler pages deploy <dir> --project-name <project> --commit-dirty=true`.

**Confirm project before destructive operations.** If asked to delete a wiki or site, verify the source directory AND the Cloudflare project name before proceeding. A URL like `https://gordon-pages.pages.dev/` does NOT map to `/opt/data/hermes-pages/` — they are separate Cloudflare Pages projects.

For LLM-backed static apps, especially apps that call a Cloudflare Pages Function and should leverage an existing local/site knowledge base, follow `references/llm-backed-static-apps.md`: keep secrets server-side, include a fallback/example mode, sanitize model JSON, surface KB grounding in the UI, run syntax checks, deploy, and verify the canonical URL plus API response.

## Generated compendium pages (gbrain → HTML)

`/opt/data/hermes-pages/hermes-memories.html` is a single-page HTML compendium of Gordon's **gbrain** knowledge base. It is NOT generated from the static HTML wiki at `/opt/data/hermes-pages/wiki/` — the eyebrow div names the gbrain runtime DB. If Gordon asks whether Hermes Memories is working or says it looks like gibberish, lead with the direct diagnostic: compare `gbrain export` output to the rendered page sections. If they match, the renderer is accurate and gbrain content/population is the issue; don't start by explaining the static wiki separation. See `references/gbrain-source-pipeline.md` for the exact diagnostic and organic-capture wiring.

To regenerate it from current gbrain content:

```bash
python3 /opt/data/skills/creative/html-to-cloudflare/scripts/gbrain-to-hermes-memories.py
npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages \
  --project-name hermes-pages --commit-dirty=true
```

The script exports all gbrain pages to a temp dir, renders each to HTML, and composes a TOC + per-page section view. The SHA-256 client-side auth gate (cookie `hermes_memories_auth=1`) is preserved verbatim from the existing page so Gordon's credentials keep working. See `references/gbrain-source-pipeline.md` for source sync, export details, and the two parallel content sources for hermes-pages.

1. Edit static HTML directly under `/opt/data/hermes-pages`.
2. Deploy with Wrangler to the **project name `hermes-pages`**:
   ```bash
   npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages --commit-dirty=true
   ```
   Use this `node@22` wrapper because the base system node may be v20 while current Wrangler requires Node 22+.
3. Verify the canonical URL, not just the preview URL:
   ```bash
   python3 - <<'PY'
   import urllib.request
   url='https://hermes-pages-d55.pages.dev/'
   html=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode('utf-8','replace')
   print('ok', len(html), html[:80])
   PY
   ```

Pitfalls:
- `--project-name hermes-pages-d55` fails with "Project not found"; use `hermes-pages`.
- Avoid `curl | python` verification patterns; security tooling may block or require approval. Fetch inside Python instead.
- A successful deploy prints a preview URL, but Gordon's preferred public URL remains `https://hermes-pages-d55.pages.dev/`.

## Verify pipeline source before answering "is X generated from Y?"

When the user asks whether a page/feature is generated from source X (e.g. "is `hermes-memories.html` generated from gbrain?"):

1. **Open the file and look for provenance strings.** Many generated pages contain explicit "Generated from <source>" markers in their HTML/CSS/comments. **For `hermes-memories.html`, the eyebrow div names the gbrain runtime DB (`/opt/data/.gbrain`)** — that is the source. Do not claim it comes from the static HTML wiki; the name "wiki" is historical, not semantic. Gordon has been emphatic: hermes-memories is an HTML rendering of gbrain, full stop.
2. **If the marker is absent**, `grep -l "<claimed_source>"` the candidate source dir for the page's distinctive content (e.g. unique headings, page names) to confirm what produced it.
3. **If you guessed wrong, correct immediately and explicitly.** A wrong "yes" leaves the user building on a false model. Say "Correction: my previous answer was wrong — the page says it comes from X, not Y. Sorry for the confusion."

Pitfall: pattern-matching the question to a plausible source without checking. The `html-to-cloudflare` skill is loaded because Gordon edits `/opt/data/hermes-pages/`; that doesn't mean every file in it flows from the wiki pipeline. Each file has its own provenance. When the page itself names a source, that is the truth — do not invent a different source from naming intuition.

## Pre-deletion / pre-modification verification

Before deleting or moving any page, wiki, or section in `/opt/data/hermes-pages/`:

1. **Confirm with the user** what URL they want gone (especially if the request references a page you don't immediately recognize).
2. **Check the page on disk** — `grep -l <page>` the source dir AND the parent index to make sure you understand all the references to it. For wiki pages, search the hub index for the link and any sub-page that links back to it.
3. **Verify the live URL** is the one Gordon means (not a similarly-named one elsewhere). `curl -sI <url>` and check the body for the title.
4. **For wikis specifically:** confirm whether the source is the markdown pipeline (now retired — wiki pages are hand-edited HTML at `/opt/data/hermes-pages/wiki/`) or a different generator. Removing the wrong file leaves orphan references.

Pitfall: I once deleted `wiki/hobbies/alcove-bathtubs.html` without first checking the `wiki/projects/alcove-bathtubs.html` copy that was the actual live link. The hub index pointed to the projects copy, so the deletion was harmless, but the verification step would have caught a different intent.

## Homepage and hub index maintenance

There are two different indexes; update the one the user actually means:

- Public homepage `https://hermes-pages-d55.pages.dev/` → `/opt/data/hermes-pages/index.html`. If Gordon says “I don’t see it here” and links the root URL, add a `.page-card` link here and verify the root page contains the new link. If `index.html` is root-owned or otherwise not writable by the Hermes user, do not block the standalone page/deploy; mention that the page is live but homepage indexing needs a permission fix or operator action.
- Private wiki hub `https://hermes-pages-d55.pages.dev/wiki/` → `/opt/data/hermes-pages/wiki/index.html`. Every time a new wiki page is published, add a link in the appropriate section using the same pattern as existing links — no summary or description, just a link.

After updating either index, push from `/opt/data/hermes-pages`, deploy with wrangler, and verify the canonical URL. Do not assume publishing a standalone HTML file makes it discoverable from the homepage.

### Homepage card structure and de-duplication

The homepage (`/opt/data/hermes-pages/index.html`) groups pages into flat `.page-card` links inside `<div class="page-grid">` sections. The card pattern is:

```html
<a href="<path>" class="page-card">
  <div class="info">
    <span class="name">Display Name</span>
    <span class="hash">/path — short tagline</span>
  </div>
  <span class="arrow">→</span>
</a>
```

**De-duplication rule:** a page should appear in the homepage card list at most once. If a sub-page (e.g. `pivotal-systems-business-plan`) is already linked from its parent page's section (e.g. `pivotal-systems.html`), do NOT also link it as a top-level card on the homepage. Verify by curling the live homepage and grepping for the path. When removing a card, delete the entire `<a>...</a>` block including the closing `</a>` tag.

**Current homepage card taxonomy (as of 2026-06-02):**
- `career.html` — Ventura vocation ideas
- `pivotal-systems.html` — Pivotal Systems business hub (links to the business plan as a sub-page)
- `wiki/login` — personal wiki
- `ai-in-vet-hospitals/` — vet hospitals AI research
- `financial-planning-ai-wiki/` — financial planning AI wiki
- `business-opportunities/ai-consulting-workflow-automation/` — AI consulting workflow

### Wiki index section structure

The wiki hub (`/opt/data/hermes-pages/wiki/index.html`) groups pages into `<div class="section">` blocks. Each section has an `<h3>` heading and a `<ul>` of link items. Current sections (2026-06-02):

| Section | Path prefix | Examples |
|---------|-------------|----------|
| Wiki | `/wiki/log` | Log |
| Identity | `/wiki/entities/` | Gordon Rouse, KLA |
| Decisions | `/wiki/concepts/` | Ventura Relocation |
| Projects | `/wiki/projects/` | Ventura Renovation, Hermes Agent, Sidekick Studio |
| Home Renovation | mix | Bathroom vanity lights, Recessed gimbal lights, plus project-style renovation research pages |
| Hobbies | `/wiki/hobbies/` | Backcountry Fishing, Backpacking, Hiking, Fitness, Personal Style, London |

When Gordon asks to "move" an item between sections, the move is purely a nav edit in `wiki/index.html` — the page file itself stays in its original directory and keeps its existing URL. E.g. moving "Alcove Bathtubs" from Projects to Home Renovation: edit the `<ul>` in the Projects section to remove the `<li>`, then insert the same `<li>` at the top of the Home Renovation `<ul>`. Keep link text and href unchanged.

### Personal utility list pages

Gordon uses short commands to maintain lightweight product-list pages on `hermes-pages`:
- `add light <URL>` → Bathroom Vanity Lights at `/opt/data/hermes-pages/bathroom-vanity-lights.html` (`https://hermes-pages-d55.pages.dev/bathroom-vanity-lights`)
- `add gimbal <URL>` → Recessed Gimbal Lights at `/opt/data/hermes-pages/recessed-gimbal-lights.html` (`https://hermes-pages-d55.pages.dev/recessed-gimbal-lights`)
- `add showerhead <URL or product name>` → **Rain Shower Heads** at `/opt/data/hermes-pages/showerheads.html` (`https://hermes-pages-d55.pages.dev/showerheads`)

For each item, save a product image locally under `/opt/data/hermes-pages/assets/`, keep the original/specified product URL as the card link, add useful metadata when available, commit, deploy with Wrangler, and verify the canonical URL contains the new item and image. On the page itself, use the exact preferred command phrase for that list (e.g. `add light <URL>`, `add showerhead <URL or product name>`). For provider quirks and list-specific metadata fields, see `references/personal-utility-product-lists.md`.

For each new URL:
1. Fetch/inspect the product page for title, price/specs, and candidate images (Open Graph/product image first; otherwise choose a clear product photo).
2. If direct fetch is blocked (common with Home Depot/Walmart), use `web_search`/`web_extract` on the product title, model number, and item ID to find reseller mirrors, review pages, or indexed snippets for specs/images. Keep the original user URL as the product link unless Gordon gave a replacement link.
3. Download the chosen image locally into `assets/` with a stable descriptive filename; do not hotlink fragile vendor CDN URLs unless downloading is blocked. If an image tool is available, visually verify that the saved image is actually a clear product photo.
4. If visual verification says the first image is poor (cropped, mostly blank, not centered, wrong product), try another candidate image such as `og:image`, Shopify JSON-LD variant image, or a product mirror before adding it.
5. Add a card/object to the existing list page without turning it into a wiki-auth page. Keep existing product cards intact; patch only the JS data array/object.
6. Commit only the relevant page/assets, deploy to the `hermes-pages` project, and verify the canonical URL includes the new item and image.

Session notes for this utility workflow are in `references/personal-utility-product-lists.md`.

Pitfalls:
- Do **not** protect root-level utility pages like `/bathroom-vanities` with the wiki login snippet. The wiki login currently redirects already-authenticated users to `/wiki/`, and its auth cookie path is `/wiki/`; a root page using `wiki_auth` will appear broken or bounce users back to the wiki/homepage. Keep root utility pages public unless Gordon explicitly asks for a proper root-scoped auth flow.
- If Gordon says a published link “doesn't work,” do not stop at “HTTP 200” verification. Check redirect/login snippets, index/hub links, and whether the user-visible click path lands on the intended page. Fix the page/link chain before replying.
- Cloudflare auto-deploy has repeatedly lagged or not run for product-list pages; because `hermes-pages` uses Direct Upload, run Wrangler after the git push instead of waiting through repeated stale checks. Prefer a direct `terminal` call for the Wrangler deploy (`npx -y -p node@22 -p wrangler ...`) rather than wrapping a long deploy/retry loop inside `execute_code`, which can hit the tool timeout and obscure partial progress.
- On mobile, product-list cards need obvious association between image and details. Use strong high-contrast card boundaries (e.g. blue border), generous vertical gaps, and a clear separator between image and text; do not rely on subtle dark borders only.

## Design preferences (from Gordon's feedback)

- **High contrast:** Gordon dislikes low-contrast formatting. Use readable high-contrast text; do not put substantive content in dim gray.
- **Concise public-site CTAs:** Avoid noisy CTA clusters and marketing jargon. For Pivotal Systems, keep the primary CTA simple (e.g. "Book a free consult") and avoid piling on parallel offers like "request an audit," trust pills, "human-in-the-loop," "SMB and semicap," etc. unless explicitly requested.
- **Pivotal Systems positioning language:** Do not publicly pitch Gordon's target clients as "low urgency" or "non-urgent." That is useful internal client-selection language, but owners may hear it as "my business is unimportant" or "this supplier won't move fast." Public copy should say "established, document-heavy businesses," "important, process-driven work," "operationally steady," or "workflow-rich." Do not lead public copy with defensive support-boundary language like "no 24/7 hotline," "quiet systems," or "I do not sell emergency IT support" — Gordon says it reads like "don't bug me." If support must be mentioned publicly, frame it positively as "clear ownership," "practical response expectations," "built to be maintainable," or "monitoring, maintenance, and small improvements during normal business operations." Avoid public framing like "deliberately small" or random contrasts such as "not a startup grind"; use "tailored," "bespoke," "focused," or "senior attention for each engagement" instead. Keep Pivotal Systems public copy customer-centered: avoid "I work best with..." / "good fit" language that sounds like Gordon is interviewing or picking customers; say what customer workflows/problems the service improves. Avoid jargon or insider metaphors like "workflow shopping cart"; use plain business language such as "long-term relationship" and "operations that matter most."
- **Public email exposure:** Do not expose Gordon's personal email in public site UI or client-side fallback text. For contact forms, route privately through Cloudflare Pages Functions/secrets such as `CONTACT_TO` and `RESEND_API_KEY`.
- **GitHub link:** Use `⚙️ GitHub` button in the hero actions area when appropriate. Don't put it in the footer alongside contact info.
- **Hero layout:** Avatar + name + role + company + tenure + status badge + action buttons.

## Common page types Gordon publishes

- **Profession/career** — landing page with work history, targets, contact info (email as plain text, GitHub in hero)
- **Hobbies** — future: interests, projects outside work, GitHub link goes here per Gordon's preference
- **Reports** — one-off generated content (job search summaries, analysis, etc.)

Each gets its own entry in the hub index.

## Wiki as HTML pages (md2html)

Gordon maintains his personal wiki in markdown (`/opt/data/wiki/`). Convert and publish as auth-protected HTML at `https://hermes-pages.rouse-gordon.workers.dev/wiki/`.

### CRITICAL: Cloudflare Pages .html redirect quirk

**Cloudflare Pages serves static files from a directory but strips `.html` from URLs** — requesting `/wiki/entities/gordon-rouse.html` gets a 307 redirect to `/wiki/entities/gordon-rouse`. This means:

1. **Never use `.html` in any href** used in nav, hub, or any link on wiki pages. Always link to the path WITHOUT the extension. The files exist as `.html` on disk but URLs are extensionless.
2. **Auth check redirect target must also be extensionless**: `window.location.href='/wiki/login?dst='+...` not `/wiki/login.html?...`
3. The `md2html.py` script handles this correctly — do NOT hand-write wiki HTML links.

### Workflow

**Gordon retired the markdown pipeline (2026-05-10). Wiki pages are now written directly in HTML.** The old md2html.py script exists but is no longer used. Do NOT write markdown and convert — edit HTML files directly and push.

**Current workflow:**
1. Edit HTML source directly under `/opt/data/hermes-pages/wiki/` (e.g. `wiki/hobbies/new-topic.html`)
2. Update the wiki hub index at `/opt/data/hermes-pages/wiki/index.html` to add a link to the new page
3. Commit and push from `/opt/data/hermes-pages`:
   ```bash
   cd /opt/data/hermes-pages
   git add wiki/hobbies/new-topic.html wiki/index.html
   git commit -m "Add new wiki page"
   GIT_TERMINAL_PROMPT=0 git push origin main
   ```
4. Live on Cloudflare Pages in ~30 seconds at `https://hermes-pages-d55.pages.dev/wiki/hobbies/new-topic`

### Wiki as HTML pages
- `wiki/index.html` → **hub page** (auth check + page links, entry point at `/wiki/`)
- `wiki/login.html` → **login page** (email + password, NO auth required, URL: `/wiki/login`)
- `wiki/entities/<name>.html` → entity pages (auth check, nav links WITHOUT .html)
- `wiki/concepts/<name>.html` → concept pages (auth check, nav links WITHOUT .html)
- `wiki/schema.html`, `wiki/log.html` → meta pages (auth check)
- `wiki/raw/articles/<name>.html` → raw sources (auth check)

### Public career/vocation section pattern

Gordon wants the career/vocation material publicly accessible while the rest of the personal wiki remains password protected. Current public label is **Vocation Ideas**.

Pattern:
- Homepage card label: `Vocation Ideas`, alongside `Resume`.
- Public hub: `/career` backed by `/opt/data/hermes-pages/career.html`.
- Public pages: `/career-opportunities`, `/business-opportunities`, and `/business-opportunities/...` drilldowns.
- Old protected wiki career URLs should redirect to the public equivalents, e.g. `/wiki/career-opportunities` → `/career-opportunities` and `/wiki/business-opportunities/...` → `/business-opportunities/...`.
- Do **not** change unrelated existing private pages unless they are part of the request. For new or updated pages, default to public unless Gordon specifically asks for private/auth-gated access.
- Update scheduled jobs that maintain this content to write to the public `/opt/data/hermes-pages/...` paths, not `/wiki/...` copies.

**3. Push to hermes-pages:**
```bash
cd /opt/data/hermes-pages-repo && git add wiki/ && git commit -m "Update wiki" && GIT_TERMINAL_PROMPT=0 git push origin main
```
Live in ~30 seconds.

**4. Update the hub index** (`/opt/data/hermes-pages-repo/index.html`) with link to `/wiki/` (or `/wiki/login` for direct login link). Push separately.

### Auth system (client-side, no Cloudflare Access needed)

| File | URL | Auth required | Purpose |
|------|-----|--------------|---------|
| `index.html` | `/wiki/` | ✅ Yes | Hub page — list of wiki pages, auth check on load |
| `login.html` | `/wiki/login` | ❌ No | Login form — email + password |
| `*.html` | `/wiki/<path>` | ❌ Default public; ✅ only when explicitly requested | Content pages — hand-authored pages, optionally protected with inline auth check when Gordon asks |

**Credentials / password maintenance:**
- Email: Gordon's Gmail address from user profile/memory.
- Password: do not rely on stale hardcoded docs; inspect `/opt/data/hermes-pages/wiki/login.html` or reset it on request.
- Cookie: `wiki_auth=GW2026` (path=`/wiki`, max-age=1yr, SameSite=Strict)
- If changing the password, update `/opt/data/hermes-pages/wiki/login.html` and any standalone generated gated pages that have their own password hash (e.g. `/opt/data/hermes-pages/hermes-memories.html`), then commit, deploy, and verify both pages.
- If Gordon asks for the password to be visible while typing, use `type="text" autocomplete="off"` for the password input on the relevant lightweight auth pages.
- If Gordon says “set the password to the wiki name,” disambiguate from the target page title. In the 2026-05-16 case, the intended password for `/hermes-memories` was the page/wiki name “Hermes Memories,” not the older login title “Gordon's Wiki.”

**Login flow:**
1. Unauthenticated user → hits any `/wiki/*` page → inline script redirects to `/wiki/login?dst=<current path>`
2. Login form shows email + password fields
3. On success: sets cookie `wiki_auth=GW2026`, redirects to `?dst` param (or `/wiki/` hub if no dst)
4. If already logged in: login page auto-redirects to `/wiki/`

**Error messages:**
- Wrong email → "Email not recognized"
- Wrong password (right email) → "Incorrect password"
- Separate messages so user knows which field is wrong

**Enterprise upgrade path:** Set up **Cloudflare Zero Trust** → cloudflare.com/zero-trust → Authentication → Add GitHub identity provider → Access Policy for `/wiki/*`. Replaces client-side auth with proper OAuth/GitHub login. Remove client-side auth check scripts when that is done.

### Wiki content strategy

Gordon's wiki is a long-term knowledge base. When incorporating new information (e.g. from chat exports):

**What to add:** Things that reveal something personally significant — not random factoids:
- Interests, likes/dislikes (e.g. hiking, fishing, style)
- Career/project details (e.g. Sidekick Studio evolution)
- Health or behavioral patterns (e.g. cutting back on alcohol)
- Financial life decisions
- Travel that reveals preferences

**What to skip:** One-off factoids, recipes, restaurant tips, ephemeral advice.
- Trivial "how many minutes" questions
- Generic questions answered quickly
- Things that would be outdated in 6 months

**Content sensitivity:** Gordon corrects overstatements. E.g. Sidekick Studio is a **hobby project** — don't frame it as a career pivot or viable post-Ventura option. When in doubt, understate rather than overstate significance. Gordon will correct you if you go too far; don't make him repeat it.

**How to incorporate:**
1. Read the JSON export (`/opt/data/cache/documents/`) — scan titles first with a quick loop to identify meaty conversations
2. Read the content of significant ones
3. Write new markdown pages under `/opt/data/wiki/` in the appropriate subdirectory:
   - `hobbies/` — outdoor activities, fitness, style, travel, home renovation research (e.g. alcove bathtubs, hiking, fishing)
   - `projects/` — Sidekick Studio and similar
   - `personal/` — health, habits
   - `entities/` — update the person entity
   - `concepts/` — update concept pages (e.g. Ventura relocation) with new context
4. Re-run `python3 /opt/data/scripts/md2html.py /opt/data/wiki`
5. Git add, commit, push
6. Update nav bar in `md2html.py` if adding entirely new categories

### Wiki page category conventions

- **Day Hikes** — separate from overnight trips. Day hike content goes in `hobbies/hiking.md`
- **Backpacking** — overnight wilderness trips (hiking + camping). Goes in `hobbies/backpacking.md`. This is where Tinker Knob and training hikes belong.
- **Fishing** — specifically backcountry/trout fishing, which is a component of backpacking trips. Goes in `hobbies/backcountry-fishing.md`.
- These are three distinct categories — don't conflate them.

### Wiki content strategy (when adding from chat exports)

See `references/wiki-content-strategy.md` for the full guide. Key rules:
- **Add** personally significant things — interests, career context, health patterns, financial decisions, travel that reveals preferences.
- **Skip** trivial one-off facts, generic advice, anything outdated in 6 months.
- **Understate rather than overstate** — Gordon corrects overstatements. "A hobby project" is safe; "a viable career option" gets corrected. Use "hobby" as the load-bearing word for Sidekick Studio.

### Wiki index page structure

The index is an HTML file (`wiki/index.html`), not markdown. When adding a new page, insert a link in the appropriate section using the same pattern as existing links. Don't create a summary or description — just a link.

### Hobbies wiki pages

For new pages under `/wiki/hobbies/`, follow `references/hobbies-wiki-pages.md`: hand-edit HTML directly, keep the page public by default unless Gordon explicitly asks for private/auth-gated access, add an extensionless Hobbies link in `wiki/index.html`, use high-contrast styling, download/credit local images under `/wiki/assets/`, create a custom local SVG when exact method illustrations are unavailable, then commit, Wrangler deploy, and verify the page, index link, and asset URLs.

For enriching travel itinerary pages, also follow `references/travel-itinerary-page-enrichment.md`: use locally saved Commons/public images, hero sections, mood-board grids, day cards/timelines, playful prompts, and route SVGs; keep itinerary pages public by default, remove existing wiki auth guards unless Gordon requested privacy, handle Wikimedia `Special:FilePath` downloads with exact filenames, URL encoding, retry/backoff for 429s, and live asset verification.

### Home renovation wiki pages

For renovation research pages (solar, fixtures, flooring, fixtures, rough-in planning, product research), follow `references/home-renovation-wiki-pages.md`: edit hand-written HTML under `/opt/data/hermes-pages`, place discoverability links in the **Home Renovation** section of `wiki/index.html`, use local SVG/assets where useful, preserve auth/public behavior intentionally, deploy via Wrangler Direct Upload, and verify canonical `hermes-pages-d55.pages.dev` URLs. If the source is a Sidekick Studio share URL, fetch the JSON message payload directly from `/share/<token>/messages` (ignore the `#msg-N` fragment for HTTP; use it only to identify the relevant message), summarize the discussion into durable guidance, and save any useful embedded `data:image/...;base64,...` images as local assets under `/wiki/assets/<topic>/`. See `references/home-renovation-wiki-pages.md` for the exact pattern.

For repo-wide markdown audits in `/opt/data/hermes-pages`, follow `references/hermes-pages-markdown-review.md`. Key: markdown in `gordons-llm-wiki/` is an archived prototype, not active wiki source; update stale docs and pointer files, then commit, Wrangler deploy, and verify live `.md` URLs because Cloudflare serves them.

For solar/open-wall electrical planning, keep construction-phase advice on a dedicated planning subpage and emphasize only work that is costly/ugly after drywall: oversized empty conduit, hidden pathways to remote battery locations, gateway/load-management space, service/panel capacity, communications conduit, labeled large-load circuits, and pre-drywall photos/labels. If Gordon says the long-term target is whole-home backup with smart load management, avoid prematurely forcing a critical-loads subpanel or vendor-specific battery architecture.

### Nav bar organization

**User preference: hide the top nav bar.** Set `.topbar { display: none; }` in the CSS. Gordon preferred a clean page without it.

The nav list is still generated (so `[[wikilinks]]` in content stay correct and `active` highlighting works), but the entire `.topbar` div is hidden via CSS:

```python
.topbar { display: none; }
```

If you need a visual separator between nav groups (e.g. between Ventura and Fishing to show "Hobbies" group), insert a `<li class="sep">|` after a known anchor in the nav HTML via string replacement after generation:

```python
nav_html = '\n'.join(
    f'<li><a href="{href}" class="...">{label}</a></li>'
    for href, label in nav_items
)
nav_html = nav_html.replace(
    'Ventura</a></li>',
    'Ventura</a></li>\n        <li class="sep">|</li>'
)
```

Current nav order: Home → Gordon → KLA → Ventura → Sidekick → Fishing → Hiking → Backpacking → Fitness → Style → London → Log. No "Health" separate nav item — health/alcohol content lives inline in Fitness.

### Wiki content strategy (when adding from chat exports)

- **Forgetting to update the index** — results in stale links on the hub page pointing to old filenames
- **`GITHUB_TOKEN` not set** — `publish_html` returns `{"success": false, "error": "GITHUB_TOKEN is not set"}`. Fix: read from `/opt/data/.git-credentials` as shown above
- **Interactive git prompts** — never run `git push` without `GIT_TERMINAL_PROMPT=0` in this environment
- **Git author identity unknown** — always configure `user.email` and `user.name` before committing to hermes-pages repo (different from hermes-agent repo which has its own gitconfig)
- **Wiki subdirectory in hermes-pages** — the `.git` directory from the original wiki clone can cause `git add` failures. Always `rm -rf /opt/data/hermes-pages-repo/gordons-llm-wiki/.git` before adding.
- **`md2html.py` runs on import** — the old version had a top-level for-loop that executed immediately on `import`, which is dangerous if the script is ever imported elsewhere. The script now guards all work behind `if __name__ == '__main__'`. Never add top-level side effects to this script.
- **Login redirect must NOT include `.html`** — the Cloudflare Pages static file server strips `.html` from URLs (returning a 307 to the extensionless version). The auth redirect in `build_page()` MUST use `/wiki/login?dst=...` not `/wiki/login.html?dst=...`. The script generates this inline; verify the generated HTML contains the extensionless URL.
- **Old wiki source path** — the original script hardcoded `/opt/data/hermes-pages-repo/gordons-llm-wiki` as the markdown source. Always pass the source dir as the first argument: `python3 /opt/data/scripts/md2html.py /opt/data/wiki`.
- **Wiki page URLs, display names, and nav order** — All driven by `WIKI_PATH_MAP` in `md2html.py`. This map is the single source of truth for: URL path (what appears in href), display label (what the user sees), and nav order (items appear in `nav_items` list in insertion order). Changes to page names or paths require updating the map AND the `index.md` wikilink AND rebuilding. Missing map entries = wrong links and garbled labels.

**Table rendering (md2html bug fix):** The old code emitted one `<table>` per row. The fix uses a `table_buf` list that collects consecutive pipe-delimited rows, then flushes them as a single `<table>` on the next non-table line. First row gets `<th>` cells. Current CSS: `border-collapse: separate; border-radius: 8px; overflow: hidden` on the `<table>`, header row distinct background, `tr:hover td` hover effect.

**Git commit/push:** Use `execute_code` with subprocess — `terminal` blocks compound `&` commands. Set `GIT_TERMINAL_PROMPT=0` in the subprocess environment, not as a shell string prefix.

**Overstating Gordon's projects:** Sidekick Studio is a hobby project. "A hobby project he's building" is safe; "a viable post-Ventura career option" gets corrected. Understate by default.

  ```python
  WIKI_PATH_MAP = {
      'gordon-rouse':      ('entities/gordon-rouse',      'Gordon Rouse'),
      'hobbies/backcountry-fishing': ('hobbies/backcountry-fishing', 'Backcountry Fishing'),
      ...
  }
  
  def wiki_link(name):
      name = name.replace('.md', '').replace('.html', '')
      if name in WIKI_PATH_MAP:
          path, label = WIKI_PATH_MAP[name]
      else:
          path = name
          label = name.split('/')[-1].replace('-', ' ').title()
      return f'<a href="/wiki/{path}">{label}</a>'
  ```

  Every page in `/opt/data/wiki/` must have a corresponding entry. Missing entries cause wrong URLs and garbled display names (e.g. "hobbies/backcountry-fishing" instead of "Backcountry Fishing"). The map also serves as the canonical list of all wiki pages.
- **Combining wiki pages** — Valid pattern. When combining: pull the secondary section to the bottom of the primary page. Remove the merged page's markdown file, remove it from nav, rebuild, commit, push.
- **Overstating significance triggers corrections** — Gordon corrected the Sidekick Studio framing twice. When in doubt, understate. "A hobby project he's building" is safer than "a viable post-Ventura option." Don't make him repeat it.
- **Terminal blocks `git commit && git push`** — Compound commands with `&` cause errors. Use `execute_code` with subprocess instead:
  ```python
  import subprocess, os
  os.chdir('/opt/data/hermes-pages-repo')
  os.environ['GIT_TERMINAL_PROMPT'] = '0'
  subprocess.run(['git', 'commit', '-m', 'message'])
  subprocess.run(['git', 'push', 'origin', 'main'])
  ```
Pitfalls:

- **Verify working-tree content before committing** — When patching a data array or render script into an HTML file, always grep the *actual file on disk* before committing. The patch tool modifies the working tree; if you commit immediately after patching, the old committed state may not contain your new data. Pattern used this session: `with open(path) as f: content = f.read(); assert 'expected content' in content` before `git add`. If the assert fails, the patch didn't land — investigate and re-patch before committing.

- **`rousegordon-ops` is a GitHub USER, not an org** — `https://api.github.com/users/rousegordon-ops/repos` works; `https://api.github.com/orgs/rousegordon-ops/repos` returns 404.

- **Python 3.13 f-string brace collision — CRITICAL** — Literal `{` and `}` in CSS inside f-strings must be doubled to `{{` and `}}`. Python 3.13 added dict unpacking syntax `{**}` as a reserved pattern, making bare `{` in f-strings a syntax error. The script appears to run (compiles OK) but fails at runtime inside `build_page()` with `NameError: name 'border' is not defined` (or whichever CSS property word comes first after the unparsed brace). The error occurs AFTER the truncated HTML has been written to disk — so the file exists with wrong content and `git status` shows "nothing to commit." **Verification:** After running md2html.py, ALWAYS grep the actual output file for expected content before committing. Example failure: `table { border-collapse: ... }` → `NameError: name 'border'`. **Fix:** Identify the `<style>` block in the f-string and replace ALL `{` with `{{` and all `}` with `}}`:
  ```python
  style_start = content.find('  <style>\n')
  style_end = content.find('\n  </style>')
  style_block_fixed = style_block.replace('{', '{{').replace('}', '}}')
  content = before + style_block_fixed + after
  ```

- **Script sync between `/opt/data/scripts/` and `/opt/data/hermes-pages-repo/scripts/`** — Edit `/opt/data/scripts/md2html.py` first (canonical). Then `shutil.copy('/opt/data/scripts/md2html.py', '/opt/data/hermes-pages-repo/scripts/md2html.py')`. Always copy before running, and always run from the repo directory (`python3 /opt/data/hermes-pages-repo/scripts/md2html.py`). The two copies diverge over time — assume the repo copy is stale until just synced.

- **Always verify generated HTML before committing** — md2html.py may run without crashing but produce wrong output (e.g. "8 sidekicks" when source says "9 sidekicks"). `git status` shows "nothing to commit" while the file is wrong. Grep the actual output file: `grep "9 sidekicks" wiki/entities/gordon-rouse.html`. If wrong, the script errored after writing truncated output — fix script, re-sync, re-run, verify again.

- **Git clone private repos works with the PAT** — `GIT_TERMINAL_PROMPT=0 git clone https://github.com/rousegordon-ops/SidekickStudio.git` succeeds. Don't assume a repo is inaccessible without trying.

- **Source repo is ground truth over session memory** — When Gordon says "get the latest info from the source repo," clone it and read actual files. Don't rely on wiki pages that may be stale. The source repo is authoritative.

## Critical Deployment Failures and How to Recover

These are session-proven failure patterns. When a normal push-and-wait doesn't work, use this decision tree:

### Pattern 1: Git push succeeds but live page is stale

Symptoms: `git push` returns `To https://github.com/...`. `git log` shows the commit on `main`. Live URL returns old content across all retry attempts. GitHub API confirms the file has the new content.

Root cause: **The `hermes-pages` Cloudflare Pages project is configured as Direct Upload, not Git Integration.** Git push to GitHub does NOT trigger a Cloudflare deploy. The GitHub repo is for source backup/version control only. **Always deploy with wrangler** after pushing.

Recovery options (in order of feasibility):
1. **wrangler force-deploy** — Requires Node 22+. Use `npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages --commit-dirty=true`. This is the ONLY reliable deploy path; not just a fallback.
2. **Isolated clean deploy** — If the worktree has unrelated dirty files, clone the committed state to a temp dir and deploy from there: `rm -rf /tmp/hermes-pages-deploy && git clone --no-local /opt/data/hermes-pages /tmp/hermes-pages-deploy && npx -y -p node@22 -p wrangler wrangler pages deploy /tmp/hermes-pages-deploy --project-name hermes-pages --commit-dirty=true`
3. **Cloudflare Dashboard** — Trigger manually at dash.cloudflare.com → Pages → hermes-pages → (no retry button for Direct Upload; you must use the CLI or upload via the dashboard).
4. **No recovery available** — If no Node 22+, no CF credentials, and no Dashboard access: the content is committed to GitHub but will NOT go live on its own. Tell Gordon.

**How to confirm the project is Direct Upload:** `curl -X POST -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/hermes-pages/deployments/<dep-id>/retry"` returns `"You cannot retry a Direct Upload deployment. Retries are only possible for builds."`

### Pattern 2: Wrangler returns "Project not found"

Cause: Wrong project name. The Pages project is named `hermes-pages`, not `hermes-pages-d55`.

Fix: Always use `--project-name hermes-pages`.

### Pattern 3: Verification returns 404 but the URL looks right

The Pages domain `hermes-pages-d55.pages.dev` serves from the `hermes-pages` project. A 404 from this domain means the file isn't in that project yet, not that the URL is wrong. Push or deploy the file to the correct project.
