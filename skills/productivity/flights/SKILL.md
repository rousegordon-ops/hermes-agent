---
name: flights
description: Search flights via SerpAPI Google Flights engine — one-way or round-trip, with pricing and booking links.
category: productivity
requires_toolsets:
  - terminal
tags:
  - flights
  - travel
  - serpapi
  - google-flights
---

# Flights Search (SerpAPI)

## When to Use

- User asks to find flights between two airports (IATA codes)
- User wants flight prices, durations, or schedules for a specific date
- User needs a Google Flights link to refine/book

## Prerequisites

- `SERPAPI_KEY` environment variable must be set (already provisioned in this container)
- Python 3 with stdlib only (no pip deps)

## CLI Usage

```bash
python3 /opt/data/skills/productivity/flights/scripts/flights_client.py \
  search <DEPARTURE_IATA> <ARRIVAL_IATA> <YYYY-MM-DD> [OPTIONS]
```

### Required Arguments

| Arg | Description |
|-----|-------------|
| `DEP` | Departure airport IATA code (e.g. SFO, JFK, LHR) |
| `ARR` | Arrival airport IATA code (e.g. LAX, NRT, CDG) |
| `DATE` | Outbound date in YYYY-MM-DD format |

### Optional Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--return YYYY-MM-DD` | *(none — one-way)* | Return date for round-trip |
| `--adults N` | 1 | Number of adult passengers |
| `--currency XXX` | USD | Currency code for prices |

### Examples

```bash
# One-way SFO → LAX on May 15
python3 .../flights_client.py search SFO LAX 2026-05-15

# Round-trip JFK → LHR, 2 adults, GBP pricing
python3 .../flights_client.py search JFK LHR 2026-06-01 --return 2026-06-15 --adults 2 --currency GBP
```

## Output Format

JSON object with:
- `google_flights_url` — direct link to Google Flights for the same query
- `flights` — array of up to 5 results, each containing:
  - `price` — integer price in requested currency
  - `total_duration` — total trip duration in minutes
  - `legs` — array of flight segments:
    - `airline` — carrier name
    - `flight_number` — e.g. "UA 1234"
    - `departure_airport` — IATA code
    - `departure_time` — ISO-ish datetime string
    - `arrival_airport` — IATA code
    - `arrival_time` — ISO-ish datetime string
    - `duration` — segment duration in minutes

## Pitfalls

- IATA codes must be uppercase (script uppercases automatically)
- Dates in the past will return empty results from SerpAPI
- SerpAPI free tier has limited monthly searches — don't loop/retry excessively
- Some routes return no "best_flights" — the script falls back to "other_flights"
