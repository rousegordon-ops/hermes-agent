---
name: weather
description: "Current weather and 1–7 day forecast via Open-Meteo. Free, no API key."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [weather, forecast, temperature, rain, wind, openmeteo]
    category: productivity
    requires_toolsets: [terminal]
---

# Weather Skill

Free weather data from Open-Meteo with automatic geocoding via Nominatim.
Python stdlib only — no pip installs, no API key.

Script path: `~/.hermes/skills/weather/scripts/weather_client.py`

## When to Use

- User asks about current weather, temperature, conditions, or forecast.
- User asks "should I bring a jacket / umbrella" type questions.
- Travel/event planning where weather matters (next 1–7 days only).
- For climate or seasonal questions beyond 7 days, use `web_search` instead.

## Commands

```bash
WEATHER=~/.hermes/skills/weather/scripts/weather_client.py
```

### at — Weather for a named place (auto-geocodes)

```bash
python3 $WEATHER at "Dublin, CA"
python3 $WEATHER at "Tokyo" --days 5
python3 $WEATHER at "Reykjavik, Iceland" --days 7
```

### coords — Weather for explicit lat/lon

```bash
python3 $WEATHER coords 37.702 -121.935
python3 $WEATHER coords 37.702 -121.935 --days 5
```

Use this when the user has sent a Telegram location pin — the message
contains `latitude:` and `longitude:` fields, pass those straight in.

## Output

Returns JSON with `location`, `timezone`, `current`, and `forecast`:

- **current**: temperature_f, feels_like_f, conditions, humidity_pct,
  wind_mph, gusts_mph
- **forecast** (per day): date, conditions, high_f, low_f, feels_like
  variants, precip_chance_pct, uv_index, sunrise, sunset

All temperatures are Fahrenheit, wind in mph, precipitation in inches.

## Pitfalls

- Forecast is capped at 7 days. For anything beyond, fall back to
  `web_search` for climate/seasonal averages.
- `at` geocodes via Nominatim — ambiguous names (e.g. "Dublin") may
  resolve to the wrong city. Include state/country if it matters.
- Sunrise/sunset are in the location's local time (not user's).

## Examples

**"What's the weather in Dublin, CA tomorrow?"**
```bash
python3 $WEATHER at "Dublin, CA" --days 2
```
Read `forecast[1]` (index 1 = tomorrow; index 0 = today).

**"Should I bring an umbrella to Seattle this week?"**
```bash
python3 $WEATHER at "Seattle, WA" --days 7
```
Check `precip_chance_pct` across the forecast array.

**Telegram location pin → "what's the weather here?"**
```bash
python3 $WEATHER coords <lat> <lon> --days 1
```
