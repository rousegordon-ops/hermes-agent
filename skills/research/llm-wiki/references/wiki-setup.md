# Gordon's Wiki — Setup Reference

Created: 2026-05-09
Updated: 2026-05-10

## Repo Structure (discovered 2026-05-10)

The wiki lives across two repos, not one:
- **`hermes-pages`** (local: `/opt/data/hermes-pages/`, GitHub: `rousegordon-ops/hermes-pages`)
  — source markdown + images + HTML templates. This is the canonical working directory.
- **`hermes-pages-repo/`** (local: `/opt/data/hermes-pages-repo/`)
  — cloned clone, `md2html.py` writes HTML output here, then copied back to `hermes-pages/`.

The two-repo setup exists because `md2html.py` has a hardcoded output path:
```python
base_out = '/opt/data/hermes-pages-repo/wiki'
```
When the tool runs, it writes HTML to the repo clone. You copy it back to `hermes-pages/` and push.

## Image Embedding

Use `[[assets/filename.jpg]]` in markdown — renders as inline `<img>` in HTML (not a link).
The `md2html.py` script handles this with:
```python
line = re.sub(r'\[\[assets/(.+?)\]\]', inline_img, line)
```

Images must live in `wiki/assets/` within the hermes-pages repo. Cloudflare Pages serves them
from `/wiki/assets/` after deploy.

## Full Publish Sequence

```bash
cd /opt/data

# Clone repos if not present
git clone https://github.com/rousegordon-ops/hermes-pages.git

# Copy image to assets dir (create if missing)
mkdir -p hermes-pages/wiki/assets
cp /path/to/image.jpg hermes-pages/wiki/assets/

# Edit markdown source:
#   Source: hermes-pages/gordons-llm-wiki/
#   Output: hermes-pages-repo/wiki/

# Regenerate HTML
python3 hermes-pages/scripts/md2html.py hermes-pages/gordons-llm-wiki

# Copy output back and push
cp -r hermes-pages-repo/wiki/* hermes-pages/wiki/
cd hermes-pages
git config user.email "rouse.gordon@gmail.com"
git config user.name "Gordon Rouse"
git add -A && git commit -m "Update message" && git push
# Cloudflare deploys in ~30s
```

## Wiki Locations

| Path | Purpose |
|------|---------|
| `/opt/data/hermes-pages/gordons-llm-wiki/` | Markdown source (edit here) |
| `/opt/data/hermes-pages/wiki/` | HTML output (served) |
| `/opt/data/hermes-pages-repo/wiki/` | md2html.py output dir |

Live URL: `https://hermes-pages.rouse-gordon.workers.dev/wiki/`

Auth: email+password. Only `rouse.gordon@gmail.com` / `GordonWiki2026!`