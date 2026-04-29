#!/usr/bin/env python3
"""Open-Meteo weather client. Free, no API key, no third-party deps."""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "hermes-weather-skill/1.0"

WMO = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def http_get(url, params=None):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def geocode(place):
    # Nominatim ToS: max 1 req/s; mild courtesy delay.
    time.sleep(0.2)
    results = http_get(NOMINATIM, {"q": place, "format": "json", "limit": 1})
    if not results:
        raise SystemExit(f"Could not geocode: {place}")
    r = results[0]
    return float(r["lat"]), float(r["lon"]), r.get("display_name", place)


def fetch_weather(lat, lon, days):
    days = max(1, min(int(days), 7))
    return http_get(OPEN_METEO, {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                   "weather_code,wind_speed_10m,wind_gusts_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                 "apparent_temperature_max,apparent_temperature_min,"
                 "precipitation_probability_max,uv_index_max,sunrise,sunset",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "forecast_days": days,
        "timezone": "auto",
    })


def shape(data, label):
    out = {"location": label, "timezone": data.get("timezone")}
    c = data.get("current") or {}
    if c:
        out["current"] = {
            "temperature_f": round(c.get("temperature_2m", 0)),
            "feels_like_f": round(c.get("apparent_temperature", 0)),
            "conditions": WMO.get(c.get("weather_code"), "Unknown"),
            "humidity_pct": c.get("relative_humidity_2m"),
            "wind_mph": round(c.get("wind_speed_10m", 0)),
            "gusts_mph": round(c["wind_gusts_10m"]) if c.get("wind_gusts_10m") else None,
        }
    d = data.get("daily") or {}
    if d.get("time"):
        out["forecast"] = [{
            "date": d["time"][i],
            "conditions": WMO.get(d["weather_code"][i], "Unknown"),
            "high_f": round(d["temperature_2m_max"][i]),
            "low_f": round(d["temperature_2m_min"][i]),
            "feels_like_high_f": round(d["apparent_temperature_max"][i]),
            "feels_like_low_f": round(d["apparent_temperature_min"][i]),
            "precip_chance_pct": d["precipitation_probability_max"][i],
            "uv_index": d["uv_index_max"][i],
            "sunrise": d["sunrise"][i].split("T")[1] if d["sunrise"][i] else None,
            "sunset":  d["sunset"][i].split("T")[1]  if d["sunset"][i]  else None,
        } for i in range(len(d["time"]))]
    return out


def main():
    p = argparse.ArgumentParser(description="Open-Meteo weather lookup.")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("at", help="Weather at a place name (geocoded).")
    a.add_argument("place")
    a.add_argument("--days", type=int, default=3)

    c = sub.add_parser("coords", help="Weather at lat/lon.")
    c.add_argument("lat", type=float)
    c.add_argument("lon", type=float)
    c.add_argument("--days", type=int, default=3)

    args = p.parse_args()

    if args.cmd == "at":
        lat, lon, label = geocode(args.place)
    else:
        lat, lon, label = args.lat, args.lon, f"{args.lat},{args.lon}"

    data = fetch_weather(lat, lon, args.days)
    print(json.dumps(shape(data, label), indent=2))


if __name__ == "__main__":
    main()
