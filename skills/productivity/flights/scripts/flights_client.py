#!/usr/bin/env python3
"""Search flights via SerpAPI Google Flights engine.

Usage:
    python3 flights_client.py search SFO LAX 2026-05-15
    python3 flights_client.py search JFK LHR 2026-06-01 --return 2026-06-15 --adults 2 --currency GBP

Requires SERPAPI_KEY environment variable.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error


def build_url(params: dict) -> str:
    """Build SerpAPI request URL."""
    base = "https://serpapi.com/search"
    query = urllib.parse.urlencode(params)
    return f"{base}?{query}"


def extract_legs(legs_raw: list) -> list:
    """Extract relevant leg info from SerpAPI leg data."""
    legs = []
    for leg in legs_raw:
        legs.append({
            "airline": leg.get("airline", "Unknown"),
            "flight_number": leg.get("flight_number", "N/A"),
            "departure_airport": leg.get("departure_airport", {}).get("id", "???"),
            "departure_time": leg.get("departure_airport", {}).get("time", ""),
            "arrival_airport": leg.get("arrival_airport", {}).get("id", "???"),
            "arrival_time": leg.get("arrival_airport", {}).get("time", ""),
            "duration": leg.get("duration", 0),
        })
    return legs


def extract_flights(raw_flights: list, limit: int = 5) -> list:
    """Extract up to `limit` flights from SerpAPI response list."""
    results = []
    for flight in raw_flights[:limit]:
        flights_data = flight.get("flights", [])
        results.append({
            "price": flight.get("price", None),
            "total_duration": flight.get("total_duration", 0),
            "legs": extract_legs(flights_data),
        })
    return results


def search_flights(
    departure: str,
    arrival: str,
    outbound_date: str,
    return_date: str | None = None,
    adults: int = 1,
    currency: str = "USD",
) -> dict:
    """Query SerpAPI google_flights engine and return structured results."""
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        print("Error: SERPAPI_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    params = {
        "engine": "google_flights",
        "departure_id": departure.upper(),
        "arrival_id": arrival.upper(),
        "outbound_date": outbound_date,
        "adults": str(adults),
        "currency": currency,
        "api_key": api_key,
        "hl": "en",
    }

    if return_date:
        params["return_date"] = return_date
        params["type"] = "1"  # round trip
    else:
        params["type"] = "2"  # one-way

    url = build_url(params)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HermesAgent/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Error: HTTP {e.code} from SerpAPI: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Network issue: {e.reason}", file=sys.stderr)
        sys.exit(1)

    # Extract google flights URL from metadata
    google_flights_url = (
        data.get("search_metadata", {}).get("google_flights_url", "")
    )

    # Collect flights — prefer best_flights, fall back to other_flights
    best = data.get("best_flights", [])
    other = data.get("other_flights", [])

    combined = best + other
    flights = extract_flights(combined, limit=5)

    return {
        "google_flights_url": google_flights_url,
        "flights": flights,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Search flights via SerpAPI Google Flights"
    )
    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser("search", help="Search for flights")
    search_parser.add_argument("departure", help="Departure IATA code (e.g. SFO)")
    search_parser.add_argument("arrival", help="Arrival IATA code (e.g. LAX)")
    search_parser.add_argument("date", help="Outbound date (YYYY-MM-DD)")
    search_parser.add_argument("--return", dest="return_date", help="Return date (YYYY-MM-DD) for round-trip")
    search_parser.add_argument("--adults", type=int, default=1, help="Number of adults (default: 1)")
    search_parser.add_argument("--currency", default="USD", help="Currency code (default: USD)")

    args = parser.parse_args()

    if args.command != "search":
        parser.print_help()
        sys.exit(1)

    result = search_flights(
        departure=args.departure,
        arrival=args.arrival,
        outbound_date=args.date,
        return_date=args.return_date,
        adults=args.adults,
        currency=args.currency,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
