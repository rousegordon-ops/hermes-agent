# Telegram image documents in Hermes gateway

## Trigger

Use this when Telegram receives a PNG/JPG/WebP/GIF as a **document** rather than as a Telegram photo and Hermes says it is unsupported or cannot see the image.

Telegram users often attach screenshots/files as documents. These arrive through the document handler, not the photo handler, even when the MIME type is `image/png` or the filename ends in `.png`.

## Fix pattern

In `gateway/platforms/telegram.py`, document handling should detect image documents before rejecting unsupported document types:

- Accept image MIME types such as `image/png`, `image/jpeg`, `image/webp`, `image/gif`.
- Accept common image extensions such as `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif` when MIME type is missing or generic.
- Preserve the existing Telegram document size limit (20 MB in the Gordon fix) before download/cache.
- Download/cache accepted image documents through the same image-cache path used by photo attachments so downstream vision/image tools can read them.
- Keep non-image documents on the normal supported-document path; do not broaden support for arbitrary files accidentally.

## Regression test pattern

Add or update tests in `tests/gateway/test_telegram_documents.py`:

- Set up an image cache directory in the test fixture/temp `HERMES_HOME`.
- Create a fake Telegram document with `mime_type='image/png'` and/or a `.png` filename.
- Mock the bot file download path.
- Assert the document is cached as an image rather than reported as unsupported.
- Run the targeted test first, then the whole document test file.

Known-good commands from the Gordon session:

```bash
python -m pytest tests/gateway/test_telegram_documents.py::TestDocumentDownloadBlock::test_png_document_is_cached_as_image -q
python -m pytest tests/gateway/test_telegram_documents.py -q
ruff check --select F821 gateway/platforms/telegram.py tests/gateway/test_telegram_documents.py
```

## Deployment note

Committing/pushing the gateway code is not enough for a live Telegram bot. Restart/redeploy the running gateway service after code changes, but ask Gordon before interrupting the bot unless he already approved the restart.

## Pitfalls

- Do not assume Telegram photos and Telegram image documents share the same update shape.
- Do not bypass document size checks for image documents.
- Do not print env vars or tokens while debugging Railway/Telegram deployment.
- Full `ruff check` may report unrelated style issues; use `--select F821` as the source-watcher-compatible safety check when validating a narrow gateway fix.
