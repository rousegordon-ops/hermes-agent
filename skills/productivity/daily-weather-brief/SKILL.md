---
name: daily-weather-brief
description: "Gordon's daily weather brief — 6 locations, Open-Meteo, sent to Telegram at 6 AM PT."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [weather, telegram, daily-routine, forecast]
    homepage: https://github.com/NousResearch/hermes-agent
---

# daily-weather-brief

Sends a weather brief to Telegram at 6 AM PT daily — mirroring GordonClaw's weather section in the daily brief.

## Locations

6 locations from `locations.json`:
- Dublin, CA
- Ventura, CA
- Santa Barbara, CA
- Cal Poly SLO, CA
- Truckee, CA
- Edinburgh, UK

## Script

`/opt/data/skills/productivity/daily-weather-brief/scripts/format_brief_weather.py`

Fetches Open-Meteo forecast (no API key), emits Markdown per location:
```
*Dublin*
• Today: 61°/52°, light drizzle, breezy
• Tmrw: 69°/52°, overcast, breezy
• Thu–Sat: warming, dry
```

## Cron Setup

**Must use `--deliver telegram` for Gordon** (not `origin` — origin delivers to the cron runner's message history, not to Gordon). For another explicit Telegram recipient, use `--deliver telegram:<chat_id>`.

Gordon's existing weather cron:
- Job ID: `757ccab5fca7`
- Schedule: `0 13 * * *` = 6 AM PT
- Deliver: `telegram`

Megan's existing weather cron:
- Job ID: `791cad428cb4`
- Schedule: `0 13 * * *` = 6 AM PT
- Deliver: `telegram:8763410743`

```bash
# Fire at 6 AM PT = 13:00 UTC
cronjob create \
  --name "Gordon morning weather" \
  --prompt "Run: python3 /opt/data/skills/productivity/daily-weather-brief/scripts/format_brief_weather.py
Capture stdout and send the weather brief as a Telegram message to Gordon." \
  --schedule "0 13 * * *" \
  --deliver telegram

cronjob create \
  --name "Megan morning weather" \
  --prompt "Run: python3 /opt/data/skills/productivity/daily-weather-brief/scripts/format_brief_weather.py
Capture stdout and send the weather brief as the final response. This is for Megan." \
  --schedule "0 13 * * *" \
  --deliver telegram:8763410743
```

### Additional Telegram recipients

For another person, create a separate cron using direct-chat delivery: `--deliver telegram:<chat_id>`. Do not change Gordon's existing job unless asked; duplicate the same script/prompt so each recipient has an independently manageable cron.

Example for Megan:

```bash
cronjob create \
  --name "Megan morning weather" \
  --prompt "Run: python3 /opt/data/skills/productivity/daily-weather-brief/scripts/format_brief_weather.py
Capture stdout and send the weather brief as the final response. This is for Megan." \
  --schedule "0 13 * * *" \
  --deliver telegram:8763410743
```

After creating, verify with `cronjob list` that the new job is enabled, scheduled at `0 13 * * *`, and has `deliver: telegram:<chat_id>`.

## Tokens

Uses `TELEGRAM_BOT_TOKEN` and `TELEGRAM_HOME_CHANNEL` from `/opt/data/.env.tokens` — no additional config needed.

## Testing

```bash
python3 /opt/data/skills/productivity/daily-weather-brief/scripts/format_brief_weather.py
```

## Cron-run execution notes

- For scheduled runs, the final response is the Telegram-delivered message. Do **not** call `send_message` or otherwise try to deliver manually; just return the weather brief as the final response.
- If the script exits `0` but prints per-location errors such as `HTTP Error 502: Bad Gateway` or `HTTP Error 429: Too Many Requests`, rerun once to rule out a transient Open-Meteo failure.
- If errors persist, preserve the script's stdout as the final brief rather than synthesizing a replacement from other weather sources, unless the user explicitly asks for a fallback. This keeps the cron output faithful to the configured formatter.
- Current failure mode observed: Open-Meteo may return `502` for the legacy daily parameter names (`weathercode`, `windspeed_10m_max`) and `429`/connection resets for the newer names (`weather_code`, `wind_speed_10m_max`) under rate limiting. Treat this as an upstream/API compatibility issue to debug separately, not as a reason to silently change the delivered brief.
