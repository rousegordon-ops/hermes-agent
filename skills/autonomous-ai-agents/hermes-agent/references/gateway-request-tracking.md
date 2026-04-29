# Gateway Request Tracking & Cost Report Customization

## Problem
OpenRouter's `/api/v1/activity` endpoint (daily request counts by model) requires a **management key** — returns HTTP 403 with a regular API key. Most users won't have one. The `/api/v1/generation` endpoint only fetches metadata for a single known generation ID (not a listing). So there's no way to get request counts from OpenRouter with a normal key.

## Solution: Local JSONL Request Log

Hook into the gateway's "response ready" log point in `gateway/run.py` (~line 5172) to append a JSONL file:

### Gateway Hook (gateway/run.py)
After the `logger.info("response ready: ...")` line, add:

```python
# Append to persistent request log for daily cost report metrics
try:
    import json as _json
    _req_log_path = os.environ.get("REQUEST_LOG_PATH", "/opt/data/request-log.jsonl")
    with open(_req_log_path, "a") as _rl:
        _rl.write(_json.dumps({
            "ts": time.time(),
            "api_calls": _api_calls,
            "platform": _platform_name,
            "chat": source.chat_id or "unknown",
            "duration": round(_response_time, 1),
        }) + "\n")
except Exception:
    pass  # non-critical — don't break gateway for metrics
```

Each line = one user interaction. `api_calls` = number of LLM API requests that interaction consumed (multiple for tool-calling loops).

### Reading the Log (cost_report.py)
```python
def compute_request_metrics() -> dict:
    """Returns total_requests_24h, max_requests_5h, interactions_24h."""
    # Read JSONL, filter to last 24h
    # Sum api_calls for total
    # Sliding two-pointer window (5h = 18000s) for peak
```

Key metrics:
- **API Requests (24h)**: sum of `api_calls` across all entries — this is the number that maps to subscription rate limits
- **User Interactions (24h)**: count of JSONL lines (user messages handled)
- **Max Requests in 5h Window**: sliding-window max of `api_calls` sum — directly comparable to provider rate-limit windows

### Log Maintenance
Prune entries older than 7 days on each report run to prevent unbounded growth.

### Data Sources Considered & Rejected
- **OpenRouter `/activity`**: 403 without management key
- **OpenRouter `/generation`**: single-ID lookup only, no listing
- **state.db `sessions` table**: has `api_call_count` per session but sessions can span days (no per-interaction granularity for 5h window)
- **state.db `messages` table**: assistant message timestamps cluster (stored together, not per-API-call)
- **gateway.log**: has "response ready" lines but lost on container restart

### Cost Report Daemon
`cost_report_daemon.py` sleeps until `COST_REPORT_HOUR` (default 6 AM PT), runs `cost_report.py`, repeats. Runs as a background process in the container.

### Environment
- `COST_STATE_PATH` (default `/opt/data/cost-state.json`) — balance snapshot
- `REQUEST_LOG_PATH` (default `/opt/data/request-log.jsonl`) — request log
- `OPENROUTER_API_KEY` — for balance check
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_HOME_CHANNEL` — for report delivery

### Seeding Historical Data
On fresh deploy, seed the JSONL from existing gateway.log:
```python
import json, re
pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ INFO gateway\.run: response ready: platform=(\w+) chat=(\S+) time=([\d.]+)s api_calls=(\d+)'
# Parse matches, write as JSONL entries
```
