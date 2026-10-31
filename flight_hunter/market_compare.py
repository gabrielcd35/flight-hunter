"""Compare Google Flights country-of-sale settings using the same exact itinerary.

These calls do not change IP geolocation or promise booking eligibility.
All queries request USD, avoiding FX-conversion false savings.
"""
from __future__ import annotations

import json
import subprocess
from typing import Any

MARKETS = {
    "Estados Unidos": "US",
    "Brasil": "BR",
    "Índia": "IN",
    "México": "MX",
    "Colômbia": "CO",
    "Canadá": "CA",
    "Reino Unido": "GB",
}
TIMEOUT_SECONDS = 100


def itinerary_key(flight: dict[str, Any]) -> tuple[str, ...] | None:
    """Identify the actual flights in both directions, not just their route."""
    parts = []
    for direction in ("outbound", "return"):
        segment = flight.get(direction) or {}
        legs = segment.get("legs") or []
        if not legs:
            return None
        for leg in legs:
            airline = leg.get("airline") or {}
            airline_name = airline.get("name") if isinstance(airline, dict) else str(airline)
            parts.append("|".join((
                str(airline_name or ""),
                str(leg.get("flight_number") or ""),
                str(leg.get("departure_time") or ""),
                str(leg.get("arrival_time") or ""),
            )))
    return tuple(parts)


def compare_markets(
    origin: str,
    destination: str,
    departure: str,
    returning: str,
    stops: str,
    market_names: list[str],
    reference_flight: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows = []
    errors = []
    reference_key = itinerary_key(reference_flight) if reference_flight else None
    for market_name in market_names:
        country = MARKETS[market_name]
        command = [
            "fli", "flights", origin, destination, departure,
            "--return", returning, "--stops", stops, "--sort", "CHEAPEST",
            "--currency", "USD", "--country", country, "--format", "json",
        ]
        try:
            response = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
            if response.returncode != 0:
                errors.append(f"{market_name}: consulta indisponível")
                continue
            data = json.loads(response.stdout)
            flights = [
                item for item in data.get("flights", [])
                if isinstance(item.get("price"), (int, float)) and (item.get("currency") in ("USD", None))
            ]
            if not flights:
                errors.append(f"{market_name}: nenhuma tarifa em USD")
                continue
            best = min(flights, key=lambda item: item["price"])
            match = next((x for x in flights if itinerary_key(x) == reference_key), None) if reference_key else None
            rows.append({
                "Mercado": market_name,
                "País": country,
                "Menor tarifa (USD)": float(best["price"]),
                "Mesmo itinerário (USD)": float(match["price"]) if match else None,
                "Link": (match or best).get("booking_url") or data.get("booking_url", ""),
            })
        except (OSError, ValueError, subprocess.TimeoutExpired):
            errors.append(f"{market_name}: falha ou tempo esgotado")
    return rows, errors
