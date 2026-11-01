"""Controlled Google Flights point-of-sale comparisons.

Each market runs in its own FLI process with explicit ``gl``, ``curr`` and
``hl`` values. These settings do not change the server IP, create a local
payment profile or guarantee that Google/airlines will return different fares.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any
from urllib.parse import parse_qs, urlparse

from flight_hunter.core import airport_code, safe_google_flights_url
from flight_hunter.search import DEFAULT_CURRENCY, DEFAULT_LANGUAGE


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
COMPARISON_TOP_N = 10

ItineraryKey = tuple[tuple[str, ...], ...]
ComparisonSignature = tuple[str, str, str, str, str, tuple[str, ...], ItineraryKey | None]


def _airline_identity(value: Any) -> tuple[str, str]:
    if isinstance(value, dict):
        return str(value.get("code") or ""), str(value.get("name") or "")
    return "", str(value or "")


def itinerary_key(flight: dict[str, Any] | None) -> ItineraryKey | None:
    """Identify one complete itinerary, including every connection airport."""
    if not isinstance(flight, dict):
        return None

    parts: list[tuple[str, ...]] = []
    for direction in ("outbound", "return"):
        segment = flight.get(direction) or {}
        legs = segment.get("legs") or []
        if not isinstance(legs, list) or not legs:
            return None
        for index, leg in enumerate(legs):
            if not isinstance(leg, dict):
                return None
            airline_code, airline_name = _airline_identity(leg.get("airline"))
            identity = (
                direction,
                str(index),
                airport_code(leg.get("departure_airport")),
                airport_code(leg.get("arrival_airport")),
                airline_code,
                airline_name,
                str(leg.get("flight_number") or ""),
                str(leg.get("departure_time") or ""),
                str(leg.get("arrival_time") or ""),
            )
            required = (identity[2], identity[3], identity[6], identity[7], identity[8])
            if any(value in ("", "—") for value in required) or not (airline_code or airline_name):
                return None
            parts.append(identity)
    return tuple(parts)


def comparison_signature(
    origin: str,
    destination: str,
    departure: str,
    returning: str,
    stops: str,
    market_names: list[str],
    reference_flight: dict[str, Any] | None,
) -> ComparisonSignature:
    """Return every input that can change a market-comparison result."""
    countries = tuple(MARKETS.get(name, f"unknown:{name}") for name in market_names)
    return (
        origin.upper(),
        destination.upper(),
        departure,
        returning,
        stops.upper(),
        countries,
        itinerary_key(reference_flight),
    )


def market_command(
    origin: str,
    destination: str,
    departure: str,
    returning: str,
    stops: str,
    country: str,
) -> list[str]:
    """Build one explicit FLI command for a country-of-sale comparison."""
    return [
        "fli",
        "flights",
        origin,
        destination,
        departure,
        "--return",
        returning,
        "--stops",
        stops,
        "--sort",
        "CHEAPEST",
        "--top-n",
        str(COMPARISON_TOP_N),
        "--currency",
        DEFAULT_CURRENCY,
        "--language",
        DEFAULT_LANGUAGE,
        "--country",
        country,
        "--format",
        "json",
    ]


def same_itinerary_spread(rows: list[dict[str, Any]]) -> float | None:
    """Return an apples-to-apples market spread, or None without two matches."""
    prices = [
        float(row["Mesmo itinerário (USD)"])
        for row in rows
        if isinstance(row.get("Mesmo itinerário (USD)"), (int, float))
        and not isinstance(row.get("Mesmo itinerário (USD)"), bool)
    ]
    if len(prices) < 2:
        return None
    return max(prices) - min(prices)


def validated_market_booking_url(value: Any, country: str) -> str | None:
    """Accept only Google Flights links carrying this comparison's locale."""
    safe_url = safe_google_flights_url(str(value)) if value else None
    if not safe_url:
        return None
    params = parse_qs(urlparse(safe_url).query)
    currency = (params.get("curr") or [""])[0].upper()
    language = (params.get("hl") or [""])[0].lower()
    point_of_sale = (params.get("gl") or [""])[0].upper()
    if (
        currency != DEFAULT_CURRENCY
        or language != DEFAULT_LANGUAGE.lower()
        or point_of_sale != country.upper()
    ):
        return None
    return safe_url


def _usd_flights(payload: dict[str, Any]) -> list[dict[str, Any]]:
    flights = payload.get("flights")
    if not isinstance(flights, list):
        return []
    return [
        item
        for item in flights
        if isinstance(item, dict)
        and isinstance(item.get("price"), (int, float))
        and not isinstance(item.get("price"), bool)
        and str(item.get("currency") or "").upper() == DEFAULT_CURRENCY
    ]


def compare_markets(
    origin: str,
    destination: str,
    departure: str,
    returning: str,
    stops: str,
    market_names: list[str],
    reference_flight: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    reference_key = itinerary_key(reference_flight)

    for market_name in market_names:
        country = MARKETS.get(market_name)
        if not country:
            errors.append(f"{market_name}: mercado não reconhecido")
            continue
        command = market_command(origin, destination, departure, returning, stops, country)
        try:
            response = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            errors.append(f"{market_name}: consulta excedeu {TIMEOUT_SECONDS}s")
            continue
        except OSError:
            errors.append(f"{market_name}: não foi possível iniciar o FLI")
            continue

        if response.returncode != 0:
            errors.append(f"{market_name}: consulta indisponível")
            continue
        try:
            data = json.loads(response.stdout)
        except (TypeError, ValueError):
            errors.append(f"{market_name}: resposta inválida")
            continue
        if not isinstance(data, dict) or data.get("success") is False:
            errors.append(f"{market_name}: consulta retornou falha")
            continue

        flights = _usd_flights(data)
        if not flights:
            errors.append(f"{market_name}: nenhuma tarifa válida em USD")
            continue

        best = min(flights, key=lambda item: float(item["price"]))
        match = (
            next((item for item in flights if itinerary_key(item) == reference_key), None)
            if reference_key
            else None
        )
        selected = match or best
        raw_url = selected.get("booking_url") or data.get("booking_url")
        booking_url = validated_market_booking_url(raw_url, country)
        if raw_url and not booking_url:
            errors.append(f"{market_name}: link não confirmou gl={country}, curr=USD e hl=en")

        rows.append(
            {
                "Mercado": market_name,
                "País": country,
                "Parâmetros": f"gl={country} · curr={DEFAULT_CURRENCY} · hl={DEFAULT_LANGUAGE}",
                "Menor tarifa (USD)": float(best["price"]),
                "Mesmo itinerário (USD)": float(match["price"]) if match else None,
                "Link validado": bool(booking_url),
                "Link": booking_url or "",
            }
        )
    return rows, errors
