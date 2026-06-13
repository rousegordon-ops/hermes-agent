# AI software-engineering article list workflow

Session-derived notes for Gordon's public article list at `/opt/data/hermes-pages/ai-sw-engineering-articles.html`.

## Page contract

- Command phrase: `add article <URL>`.
- Public URL: `https://hermes-pages-d55.pages.dev/ai-sw-engineering-articles`.
- Source file: `/opt/data/hermes-pages/ai-sw-engineering-articles.html`.
- Data lives in `window.__AI_SW_ENGINEERING_ARTICLES` as JS objects.
- Fields used by the renderer:
  - `title`
  - `url`
  - `source`
  - `author` (optional)
  - `published` (optional)
  - `added`
  - `summary`
  - `note` (optional)
- No image is required for article cards.

## X / Twitter article extraction pattern

For an X status that points to an X Article:

1. Try `xurl read <url>` if available/authenticated.
2. If `xurl` is unavailable, use public extraction:
   - `web_extract` the X status URL directly.
   - `web_extract` the oEmbed URL: `https://publish.twitter.com/oembed?url=https://twitter.com/<handle>/status/<id>`.
   - `web_search` the status ID and/or discovered article title.
3. The X status page can expose an article card even when the `/i/article/<id>` page itself cannot be fetched. Capture title, author/handle, date, and card description from that public status page.
4. If the visible post contains only a `t.co` link, resolving it may reveal `/i/article/<id>`, but it may require approval because shortened URLs hide the destination. Use the resolved URL only as provenance; keep Gordon's original URL as the saved outbound URL unless he gave a replacement.

## Deployment checklist

1. Patch only `ai-sw-engineering-articles.html` for article additions.
2. Verify the file contains the expected title and status/article URL before committing.
3. Commit only the relevant file; leave unrelated dirty files alone.
4. Deploy with Wrangler Direct Upload using an isolated clone if the worktree has unrelated dirty files.
5. Verify the canonical URL contains the new title, author/source, and URL identifier.
