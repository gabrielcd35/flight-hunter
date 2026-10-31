"""Pure helpers shared by the Streamlit UI and tests."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, Iterable
from urllib.parse import urlparse


AIRPORT_CODES = re.compile(r"[A-Z]{3}(?:,[A-Z]{3})*")


def valid_airport_codes(value: str) -> bool:
    return bool(AIRPORT_CODES.fullmatch(value))


def filter_destinations(origin: str, destinations: dict[str, str]) -> dict[str, str]:
    """Remove selections that contain only airports already in the origin."""
    origin_airports = set(origin.split(","))
    return {
        name: codes
        for name, codes in destinations.items()
        if not set(codes.split(",")).issubset(origin_airports)
    }


def date_options(
    base: date,
    enabled: bool,
    direction: str,
    days: int,
    *,
    today: date | None = None,
) -> list[date]:
    """Build a bounded list of future dates around a selected date."""
    today = today or date.today()
    offsets = [0]
    if enabled and direction in ("Antes e depois", "Somente antes"):
        offsets.extend(range(-days, 0))
    if enabled and direction in ("Antes e depois", "Somente depois"):
        offsets.extend(range(1, days + 1))
    return sorted({base + timedelta(days=offset) for offset in offsets if base + timedelta(days=offset) >= today})


def valid_date_pairs(departures: Iterable[date], returns: Iterable[date]) -> list[tuple[date, date]]:
    return [(departure, returning) for departure in departures for returning in returns if returning > departure]


def format_date(raw: str | date | None) -> str:
    if not raw:
        return "Data indisponível"
    try:
        value = raw if isinstance(raw, date) else date.fromisoformat(str(raw)[:10])
        return value.strftime("%m/%d/%Y")
    except (TypeError, ValueError):
        return str(raw)


def format_short_date(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw).strftime("%m/%d")
    except (TypeError, ValueError):
        return str(raw)[:10]


def format_time(raw: str | None) -> str:
    if not raw:
        return "—"
    try:
        return datetime.fromisoformat(raw).strftime("%H:%M")
    except (TypeError, ValueError):
        return str(raw)


def format_minutes(raw: Any) -> str:
    if not isinstance(raw, (int, float)):
        return "Não informado"
    minutes = int(raw)
    return f"{minutes // 60}h {minutes % 60:02d}min"


def airport_code(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("code") or value.get("iata_code") or value.get("name") or "—")
    return str(value or "—")


def airline_label(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("code") or "Companhia não informada")
    return str(value or "Companhia não informada")


def segment_airlines(segment: dict[str, Any]) -> list[str]:
    airlines: list[str] = []
    for leg in segment.get("legs") or []:
        name = airline_label(leg.get("airline"))
        if name not in airlines:
            airlines.append(name)
    return airlines


def connection_label(segment: dict[str, Any]) -> str:
    stops = segment.get("stops")
    if not isinstance(stops, int):
        stops = max(len(segment.get("legs") or []) - 1, 0)
    if stops == 0:
        return "Voo direto"
    if stops == 1:
        return "1 conexão"
    return f"{stops} conexões"


def safe_google_flights_url(url: str | None) -> str | None:
    """Allow only HTTPS Google Flights links returned by FLI."""
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"google.com", "www.google.com"}:
        return None
    if not parsed.path.startswith("/travel/flights"):
        return None
    return url

