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

## X / Twitter extraction pattern

For an X status, first classify whether it is an X Article card or just a thread/status worth saving:

1. Try `xurl read <url>` if available/authenticated.
2. If `xurl` is unavailable, use public extraction in this order:
   - `web_extract` the X status URL directly.
   - X oEmbed via Python stdlib (no `requests` dependency assumed):
     ```bash
     python3 - <<'PY'
     import urllib.parse, urllib.request
     status_url='https://x.com/<handle>/status/<id>'
     url='https://publish.twitter.com/oembed?'+urllib.parse.urlencode({'url':status_url,'omit_script':'1'})
     req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
     print(urllib.request.urlopen(req,timeout=20).read().decode('utf-8','replace'))
     PY
     ```
   - For public tweet JSON, `https://api.fxtwitter.com/<handle>/status/<id>` often returns `tweet.text`, author metadata, counts, and `created_at` when X/browser extraction fails.
   - `web_search` the status ID and/or discovered article/thread title.
3. If the status exposes an article card even when `/i/article/<id>` cannot be fetched, capture title, author/handle, date, and card description from that public status page.
4. If the status is itself the saved item (for example a thread opener like “Here are 6 free courses…”), use source `X Thread`, title it from the visible subject, set `published` from oEmbed/fxtwitter date, and write a short summary/note from the visible post. Do not invent the hidden thread contents if only the opener is available.
5. If the visible post contains only a `t.co` link, resolving it may reveal `/i/article/<id>`, but it may require approval because shortened URLs hide the destination. Use the resolved URL only as provenance; keep Gordon's original URL as the saved outbound URL unless he gave a replacement.

## Deployment checklist

1. Patch only `ai-sw-engineering-articles.html` for article additions.
2. Verify the file contains the expected title and status/article URL before committing.
3. Commit only the relevant file; leave unrelated dirty files alone.
4. Deploy with Wrangler Direct Upload using an isolated clone if the worktree has unrelated dirty files.
5. Verify the canonical URL contains the new title, author/source, and URL identifier.
