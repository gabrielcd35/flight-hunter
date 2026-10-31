"""FLI command integration kept separate from presentation concerns."""

from __future__ import annotations

import json
import subprocess
from typing import Any


SEARCH_TIMEOUT_SECONDS = 150


def _run_fli(command: list[str]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=SEARCH_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None, "A busca demorou mais do que o esperado. Tente menos destinos ou menos datas."
    except OSError as error:
        return None, f"Não foi possível iniciar a busca: {error}"

    if response.returncode != 0:
        message = (response.stderr or response.stdout or "Falha sem detalhes").strip()
        return None, message[-500:]

    try:
        payload = json.loads(response.stdout)
    except ValueError:
        return None, "O serviço de busca retornou uma resposta inválida."

    if payload.get("success") is False:
        message = payload.get("message") or payload.get("error") or "A busca não pôde ser concluída."
        return None, str(message)
    return payload, None


def _append_layover_limit(command: list[str], layover_minutes: int | None) -> None:
    if layover_minutes:
        command.extend(["--max-layover", str(layover_minutes)])


def search_calendar(
    origin: str,
    destination: str,
    first_departure: str,
    last_departure: str,
    duration: int,
    stop_code: str,
    layover_minutes: int | None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Find the lowest calendar fare for a fixed-duration trip."""
    command = [
        "fli",
        "dates",
        origin,
        destination,
        "--from",
        first_departure,
        "--to",
        last_departure,
        "--duration",
        str(duration),
        "--round",
        "--sort",
        "--format",
        "json",
        "--stops",
        stop_code,
    ]
    _append_layover_limit(command, layover_minutes)
    payload, error = _run_fli(command)
    if error or payload is None:
        return None, error
    fares = [item for item in payload.get("dates", []) if isinstance(item.get("price"), (int, float))]
    if not fares:
        return None, "Nenhuma tarifa de calendário foi encontrada para esse período."
    return min(fares, key=lambda item: item["price"]), None


def search_specific_flights(
    origin: str,
    destination: str,
    departure: str,
    returning: str,
    stop_code: str,
    layover_minutes: int | None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Retrieve detailed round-trip itineraries for one exact date pair."""
    command = [
        "fli",
        "flights",
        origin,
        destination,
        departure,
        "--return",
        returning,
        "--stops",
        stop_code,
        "--sort",
        "CHEAPEST",
        "--format",
        "json",
    ]
    _append_layover_limit(command, layover_minutes)
    payload, error = _run_fli(command)
    if error or payload is None:
        return [], error
    flights = [item for item in payload.get("flights", []) if isinstance(item.get("price"), (int, float))]
    if not flights:
        return [], "Nenhum itinerário foi encontrado para essas datas."
    return flights, None


def cheapest_specific_flight(
    origin: str,
    destination: str,
    departure: str,
    returning: str,
    stop_code: str,
    layover_minutes: int | None,
) -> tuple[dict[str, Any] | None, str | None]:
    flights, error = search_specific_flights(
        origin,
        destination,
        departure,
        returning,
        stop_code,
        layover_minutes,
    )
    if error:
        return None, error
    return min(flights, key=lambda item: item["price"]), None

