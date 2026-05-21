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

**Must use `--deliver telegram` for Gordon** (not `origin` — origin delivers to the cron runner's message history, not to Gordon).

```bash
# Fire at 6 AM PT = 13:00 UTC
cronjob create \
  --name "Gordon morning weather" \
  --prompt "Run: python3 /opt/data/skills/productivity/daily-weather-brief/scripts/format_brief_weather.py
Capture stdout and send the weather brief as a Telegram message to Gordon." \
  --schedule "0 13 * * *" \
  --deliver telegram
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
