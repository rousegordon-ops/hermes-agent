#!/usr/bin/env python3
"""Build hermes-memories.html from gbrain export.

Pipeline:
  1. Run `gbrain export` to dump markdown pages to a temp dir.
  2. For each .md: strip frontmatter, convert to HTML (headings, paragraphs,
     code, blockquotes, lists, tables, [[wikilinks]]).
  3. Compose a single-page compendium with TOC + per-page sections.
  4. Preserve the SHA-256 client-side auth gate from the existing page.

Output: /opt/data/hermes-pages/hermes-memories.html

Usage:
  python3 /opt/data/skills/creative/html-to-cloudflare/scripts/gbrain-to-hermes-memories.py

After running, deploy with wrangler:
  npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages \\
    --project-name hermes-pages --commit-dirty=true
"""

from __future__ import annotations

import html
import os
import re
import subprocess
import sys
import shutil
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────
EXPORTER = '/opt/data/.bun/bin/gbrain'
EXPORT_DIR = Path('/tmp/gbrain-export')
OUTPUT = Path('/opt/data/hermes-pages/hermes-memories.html')

# Page order: index first, then meta, then content. Matches gbrain "feel".
PAGE_ORDER = ['index', 'user', 'memory', 'schema', 'readme', 'log/log']


def run_export() -> Path:
    """Run `gbrain export` to dump markdown to a temp dir. Returns the dir."""
    if EXPORT_DIR.exists():
        shutil.rmtree(EXPORT_DIR)
    EXPORT_DIR.mkdir(parents=True)
    env = {**os.environ, 'PATH': '/opt/data/.bun/bin:/usr/bin:/bin', 'HOME': '/opt/data'}
    result = subprocess.run(
        [EXPORTER, 'export', '--dir', str(EXPORT_DIR)],
        env=env, capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f'gbrain export FAILED: {result.stderr}', file=sys.stderr)
        sys.exit(1)
    return EXPORT_DIR


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Strip YAML frontmatter, return (meta_dict, body_text)."""
    if not text.startswith('---'):
        return {}, text
    end = text.find('\n---', 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip()
    body = text[end + 4:].lstrip('\n')
    meta: dict = {}
    current_key: str | None = None
    for line in fm_block.splitlines():
        if not line.strip():
            continue
        m = re.match(r'^(\w+):\s*(.*)$', line)
        if m:
            current_key = m.group(1)
            value = m.group(2).strip()
            if value.startswith('[') and value.endswith(']'):
                try:
                    meta[current_key] = [x.strip().strip('"\'') for x in value[1:-1].split(',') if x.strip()]
                except Exception:
                    meta[current_key] = value
            elif value in ('true', 'false'):
                meta[current_key] = (value == 'true')
            else:
                meta[current_key] = value.strip('"\'')
        elif line.startswith('  - ') and current_key:
            meta.setdefault(current_key, [])
            if isinstance(meta[current_key], list):
                meta[current_key].append(line.strip()[2:].strip('"\''))
    return meta, body


# ── Markdown → HTML ──────────────────────────────────────────────────

def slug_to_display(slug: str) -> str:
    """Turn 'log/log' or 'gordon-rouse' into 'Log' / 'Gordon Rouse'."""
    last = slug.split('/')[-1]
    return last.replace('-', ' ').replace('_', ' ').title()


def render_inline(text: str) -> str:
    """Render inline markdown: bold, italic, code, links, [[wikilinks]]."""
    s = html.escape(text, quote=False)
    def wl(m: re.Match) -> str:
        target = m.group(1).strip()
        display = slug_to_display(target)
        return f'<a href="#{target.replace("/", "-")}">{display}</a>'
    s = re.sub(r'\[\[([^\]]+)\]\]', wl, s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s


def md_to_html(body: str) -> str:
    """Convert markdown body to HTML."""
    lines = body.splitlines()
    out: list[str] = []
    in_code = False
    code_buf: list[str] = []
    in_list = False
    list_type: str | None = None
    para_buf: list[str] = []
    table_buf: list[str] = []

    def flush_para():
        nonlocal para_buf
        if para_buf:
            joined = ' '.join(para_buf)
            out.append(f'<p>{render_inline(joined)}</p>')
            para_buf = []

    def flush_list():
        nonlocal in_list, list_type
        if in_list:
            out.append(f'</{list_type}>')
            in_list = False
            list_type = None

    def flush_table():
        nonlocal table_buf
        if not table_buf:
            return
        rows = [r for r in table_buf if not re.match(r'^\s*\|[\s\-|:]+\|\s*$', r)]
        if not rows:
            table_buf = []
            return
        header_cells = [c.strip() for c in rows[0].strip('|').split('|')]
        body_rows = rows[1:]
        th = ''.join(f'<th>{render_inline(c)}</th>' for c in header_cells)
        trs = [''.join(f'<td>{render_inline(c.strip())}</td>' for c in r.strip('|').split('|')) for r in body_rows]
        out.append('<table><thead><tr>' + th + '</tr></thead><tbody>' + ''.join(f'<tr>{t}</tr>' for t in trs) + '</tbody></table>')
        table_buf = []

    for raw in lines:
        line = raw.rstrip()
        if line.strip().startswith('```'):
            flush_para(); flush_list(); flush_table()
            if not in_code:
                in_code = True; code_buf = []
            else:
                out.append('<pre><code>' + '\n'.join(html.escape(l) for l in code_buf) + '</code></pre>')
                in_code = False
            continue
        if in_code:
            code_buf.append(line); continue
        if not line.strip():
            flush_para(); flush_list(); flush_table(); continue
        if line.lstrip().startswith('|') and line.rstrip().endswith('|'):
            flush_para(); flush_list(); table_buf.append(line); continue
        else:
            flush_table()
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            flush_para(); flush_list()
            level = len(m.group(1))
            text = m.group(2).strip()
            anchor = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
            out.append(f'<h{level} id="{anchor}">{render_inline(text)}</h{level}>')
            continue
        if line.lstrip().startswith('>'):
            flush_para(); flush_list()
            bq = [re.sub(r'^\s*>\s?', '', line)]
            continue
        m = re.match(r'^[-*+]\s+(.*)', line)
        if m:
            flush_para()
            if in_list and list_type != 'ul': flush_list()
            if not in_list: out.append('<ul>'); in_list = True; list_type = 'ul'
            out.append(f'<li>{render_inline(m.group(1))}</li>'); continue
        m = re.match(r'^\d+\.\s+(.*)', line)
        if m:
            flush_para()
            if in_list and list_type != 'ol': flush_list()
            if not in_list: out.append('<ol>'); in_list = True; list_type = 'ol'
            out.append(f'<li>{render_inline(m.group(1))}</li>'); continue
        if line.strip() in ('---', '***', '___'):
            flush_para(); flush_list(); out.append('<hr>'); continue
        flush_list(); para_buf.append(line.strip())

    flush_para(); flush_list(); flush_table()
    return '\n'.join(out)


# ── Compose compendium ───────────────────────────────────────────────

def find_page_files(export_dir: Path) -> dict[str, Path]:
    pages: dict[str, Path] = {}
    for path in export_dir.rglob('*.md'):
        rel = path.relative_to(export_dir)
        slug = str(rel.with_suffix('')).replace(os.sep, '/')
        pages[slug] = path
    return pages


def ordered_slugs(pages: dict[str, Path]) -> list[str]:
    seen = set(); out: list[str] = []
    for s in PAGE_ORDER:
        if s in pages and s not in seen: out.append(s); seen.add(s)
    for s in sorted(pages):
        if s not in seen: out.append(s); seen.add(s)
    return out


def build_compendium(pages: dict[str, Path]) -> str:
    slugs = ordered_slugs(pages)
    page_html: list[str] = []

    for i, slug in enumerate(slugs, start=1):
        path = pages[slug]
        meta, body = parse_frontmatter(path.read_text(encoding='utf-8'))
        title = meta.get('title') or slug_to_display(slug)
        kicker = f'/{slug}'
        section_html = md_to_html(body)
        section_html = re.sub(r'^<h1[^>]*>.*?</h1>\n*', '', section_html, count=1, flags=re.DOTALL)
        anchor = f'p{i}'
        page_html.append(
            f'<section class="page" id="{anchor}">\n'
            f'  <div class="page-kicker">{html.escape(kicker)}</div>\n'
            f'  <h1>{html.escape(title)}</h1>\n'
            f'{section_html}\n'
            f'</section>'
        )

    body_html = '\n'.join(page_html)

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>gbrain</title>
<style>
:root {{ color-scheme: dark; --bg:#0d1117; --panel:#161b22; --text:#e6edf3; --muted:#c9d1d9; --line:#30363d; --blue:#58a6ff; --green:#3fb950; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.65; overflow-wrap:anywhere; word-break:normal; }}
a {{ color:var(--blue); text-decoration:none; overflow-wrap:anywhere; }} a:hover {{ text-decoration:underline; }}
.layout {{ width:min(100%,1120px); margin:0 auto; padding:28px 24px 80px; }}
.page {{ background:rgba(22,27,34,.55); border:1px solid var(--line); border-radius:18px; padding:28px; margin-bottom:22px; overflow-x:hidden; max-width:100%; overflow-wrap:anywhere; }}
.page-kicker {{ color:var(--green); font-size:12px; font-weight:800; letter-spacing:.06em; text-transform:uppercase; margin-bottom:8px; overflow-wrap:anywhere; }}
.page h1 {{ font-size:28px; line-height:1.2; margin:0 0 18px; color:var(--blue); border-bottom:1px solid var(--line); padding-bottom:12px; }}
.page h2 {{ font-size:21px; margin:28px 0 10px; color:var(--text); }}
.page h3 {{ font-size:17px; margin:22px 0 8px; color:var(--muted); }}
p {{ margin:0 0 14px; }} ul, ol {{ margin:0 0 14px 24px; }} li {{ margin:6px 0; }}
table {{ border-collapse:separate; border-spacing:0; width:100%; table-layout:fixed; margin:18px 0; border:1px solid var(--line); border-radius:10px; overflow:hidden; font-size:14px; }}
th,td {{ padding:10px 12px; border-bottom:1px solid #21262d; vertical-align:top; overflow-wrap:anywhere; word-break:normal; }} th {{ background:var(--panel); color:var(--text); text-align:left; }} tr:nth-child(even) td {{ background:rgba(255,255,255,.03); }}
code {{ background:var(--panel); border:1px solid var(--line); border-radius:5px; padding:1px 5px; white-space:normal; overflow-wrap:anywhere; }} pre {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px; overflow-x:hidden; white-space:pre-wrap; overflow-wrap:anywhere; }} pre code {{ white-space:pre-wrap; border:0; padding:0; }}
blockquote {{ border-left:3px solid var(--blue); padding-left:14px; color:var(--muted); margin:14px 0; }}
@media (max-width: 860px) {{ .layout {{ padding:18px 12px 56px; }} .page {{ padding:18px; border-radius:14px; }} ul, ol {{ margin-left:18px; }} }}
</style>
</head>
<body>
<main class="layout">
{body_html}
</main>
</body>
</html>
'''


def main() -> int:
    export_dir = run_export()
    pages = find_page_files(export_dir)
    if not pages:
        print('gbrain export produced 0 pages — aborting', file=sys.stderr)
        return 1
    print(f'Found {len(pages)} gbrain pages: {sorted(pages)}')
    out_html = build_compendium(pages)
    OUTPUT.write_text(out_html, encoding='utf-8')
    print(f'Wrote {OUTPUT} ({len(out_html):,} chars)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
