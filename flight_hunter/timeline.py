"""Duration-based itinerary timeline calculations.

FLI timestamps are local to each airport and usually do not include UTC offsets.
For that reason, proportions are always derived from the duration fields returned
by FLI. Timestamps are only used as an additional validation when both values are
timezone-aware.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Any

from flight_hunter.core import airport_code


@dataclass(frozen=True)
class FlightSpan:
    departure_airport: str
    arrival_airport: str
    duration_minutes: float
    start_percent: float
    end_percent: float


@dataclass(frozen=True)
class ConnectionSpan:
    airport: str
    duration_minutes: float
    arrival_percent: float
    departure_percent: float
    arrival_time: str | None
    departure_time: str | None
    overnight: bool
    change_of_airport: bool

    @property
    def midpoint_percent(self) -> float:
        return round((self.arrival_percent + self.departure_percent) / 2, 4)


@dataclass(frozen=True)
class SegmentTimeline:
    precise: bool
    total_minutes: float | None
    flights: tuple[FlightSpan, ...] = ()
    connections: tuple[ConnectionSpan, ...] = ()
    unavailable_reason: str | None = None


def _duration(value: Any, *, allow_zero: bool = False) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    if not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        return None
    return value


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _timestamp_matches(start: Any, end: Any, expected_minutes: float) -> bool:
    """Validate only timestamps that carry enough timezone information."""
    parsed_start = _parse_timestamp(start)
    parsed_end = _parse_timestamp(end)
    if parsed_start is None or parsed_end is None:
        return True
    elapsed_minutes = (parsed_end - parsed_start).total_seconds() / 60
    tolerance = max(2.0, expected_minutes * 0.01)
    return elapsed_minutes >= 0 and abs(elapsed_minutes - expected_minutes) <= tolerance


def _fallback(segment: dict[str, Any], reason: str) -> SegmentTimeline:
    declared_total = _duration(segment.get("duration"))
    return SegmentTimeline(
        precise=False,
        total_minutes=declared_total,
        unavailable_reason=reason,
    )


def build_segment_timeline(segment: dict[str, Any]) -> SegmentTimeline:
    """Build a 0–100% timeline from authoritative FLI duration fields."""
    legs = segment.get("legs") or []
    if not isinstance(legs, list) or not legs:
        return _fallback(segment, "Os trechos do itinerário não foram informados.")

    layovers = segment.get("layovers") or []
    if not isinstance(layovers, list):
        layovers = []

    leg_durations: list[float] = []
    for leg in legs:
        if not isinstance(leg, dict):
            return _fallback(segment, "Um dos trechos retornou dados incompletos.")
        duration = _duration(leg.get("duration"))
        if duration is None:
            return _fallback(segment, "A duração de um dos voos não foi informada.")
        if not _timestamp_matches(leg.get("departure_time"), leg.get("arrival_time"), duration):
            return _fallback(segment, "Os horários e a duração de um dos voos não são consistentes.")
        leg_durations.append(duration)

    connection_count = len(legs) - 1
    if len(layovers) < connection_count:
        return _fallback(segment, "A duração de uma das conexões não foi informada.")

    layover_durations: list[float] = []
    for index in range(connection_count):
        layover = layovers[index]
        if not isinstance(layover, dict):
            return _fallback(segment, "Uma das conexões retornou dados incompletos.")
        duration = _duration(layover.get("duration"), allow_zero=True)
        if duration is None:
            return _fallback(segment, "A duração de uma das conexões não foi informada.")
        previous_leg = legs[index]
        next_leg = legs[index + 1]
        if not _timestamp_matches(
            previous_leg.get("arrival_time"),
            next_leg.get("departure_time"),
            duration,
        ):
            return _fallback(segment, "Os horários e a duração de uma das conexões não são consistentes.")
        layover_durations.append(duration)

    computed_total = sum(leg_durations) + sum(layover_durations)
    if computed_total <= 0:
        return _fallback(segment, "A duração total do itinerário não foi informada.")

    declared_total = _duration(segment.get("duration"))
    if declared_total is not None:
        tolerance = max(2.0, computed_total * 0.01)
        if abs(declared_total - computed_total) > tolerance:
            return _fallback(segment, "As durações retornadas para o itinerário não são consistentes.")

    flights: list[FlightSpan] = []
    connections: list[ConnectionSpan] = []
    elapsed = 0.0

    for index, (leg, duration) in enumerate(zip(legs, leg_durations)):
        flight_start = elapsed / computed_total * 100
        elapsed += duration
        flight_end = elapsed / computed_total * 100
        if index == len(legs) - 1:
            flight_end = 100.0
        flights.append(
            FlightSpan(
                departure_airport=airport_code(leg.get("departure_airport")),
                arrival_airport=airport_code(leg.get("arrival_airport")),
                duration_minutes=duration,
                start_percent=round(flight_start, 4),
                end_percent=round(flight_end, 4),
            )
        )

        if index < connection_count:
            layover = layovers[index]
            arrival_percent = elapsed / computed_total * 100
            elapsed += layover_durations[index]
            departure_percent = elapsed / computed_total * 100
            connections.append(
                ConnectionSpan(
                    airport=airport_code(layover.get("airport") or leg.get("arrival_airport")),
                    duration_minutes=layover_durations[index],
                    arrival_percent=round(arrival_percent, 4),
                    departure_percent=round(departure_percent, 4),
                    arrival_time=leg.get("arrival_time"),
                    departure_time=legs[index + 1].get("departure_time"),
                    overnight=bool(layover.get("overnight")),
                    change_of_airport=bool(layover.get("change_of_airport")),
                )
            )

    return SegmentTimeline(
        precise=True,
        total_minutes=computed_total,
        flights=tuple(flights),
        connections=tuple(connections),
    )
