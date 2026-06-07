# hermes-pages markdown review workflow

Use when Gordon asks to “review all the md files in the repo” for `/opt/data/hermes-pages`.

## Scope

The active repo is `/opt/data/hermes-pages`. Markdown files currently include a mix of:

- Root docs such as `README.md`.
- Empty or pointer `.md` files that can be mistaken for active source.
- `gordons-llm-wiki/`, an archived markdown prototype.
- Active site/wiki pages are mostly hand-authored HTML, not generated from these markdown files.

## Review steps

1. Find markdown files:
   ```bash
   cd /opt/data/hermes-pages
   find . -name '*.md' -not -path './.git/*' | sort
   ```
2. Read every file before editing. Check for:
   - obsolete `/opt/data/hermes-pages-repo` workflow language;
   - false “Cloudflare auto-deploys on push” claims;
   - stale Cloudflare Access/privacy language;
   - empty markdown files that should be pointer notes;
   - stale user facts/email/address/commute constraints;
   - archived prototype pages presenting themselves as active source.
3. Update docs to reflect current source-of-truth split:
   - `/opt/data/hermes-pages` = static site source.
   - Wrangler Direct Upload is required after git push.
   - `/opt/data/gbrain-content` = gbrain markdown source.
   - `/opt/data/.gbrain` = gbrain runtime DB.
   - `gordons-llm-wiki/` in `hermes-pages` is archived/prototype unless Gordon explicitly reactivates it.
4. Run content checks over all markdown files: none empty; no stale deployment claims; no stale email/address strings.
5. Commit/push relevant markdown changes and deploy with Wrangler, because `.md` files are publicly served by the Pages project.
6. Verify at least representative live markdown URLs, e.g. `/README.md`, `/gordons-llm-wiki/index.md`, and any updated entity page.

## Session-proven stale strings

Search for these during review:

- `auto-deploys on push`
- `Cloudflare Access`
- `/opt/data/hermes-pages-repo`
- `gordon.rouse@gmail.com`
- exact street addresses unless Gordon explicitly wants them public

## Notes

Do not import or sync `gordons-llm-wiki/` into gbrain as a “fix” just because it is markdown. It is an archived prototype; gbrain’s durable source is `/opt/data/gbrain-content`.
