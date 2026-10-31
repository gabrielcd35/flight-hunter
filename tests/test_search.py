import json
import subprocess
from types import SimpleNamespace

from flight_hunter.search import search_calendar, search_specific_flights


def completed(payload, returncode=0, stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=json.dumps(payload), stderr=stderr)


def test_calendar_search_preserves_filters_and_selects_cheapest(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return completed(
            {
                "success": True,
                "dates": [
                    {"departure_date": "2026-11-02", "return_date": "2026-11-05", "price": 240},
                    {"departure_date": "2026-11-03", "return_date": "2026-11-06", "price": 180},
                ],
            }
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    result, error = search_calendar("PHX", "LAX", "2026-11-02", "2026-11-04", 3, "1", 240)

    assert error is None
    assert result["price"] == 180
    assert captured["command"][:4] == ["fli", "dates", "PHX", "LAX"]
    assert captured["command"][-2:] == ["--max-layover", "240"]
    assert captured["kwargs"]["timeout"] == 150


def test_specific_search_returns_only_priced_itineraries(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: completed(
            {
                "success": True,
                "flights": [
                    {"price": None, "outbound": {}},
                    {"price": 315, "outbound": {}, "return": {}},
                ],
            }
        ),
    )
    flights, error = search_specific_flights("PHX", "JFK", "2026-11-02", "2026-11-06", "0", None)
    assert error is None
    assert flights == [{"price": 315, "outbound": {}, "return": {}}]


def test_search_reports_process_and_timeout_errors(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="provider unavailable"),
    )
    result, error = search_calendar("PHX", "LAS", "2026-11-02", "2026-11-02", 3, "ANY", None)
    assert result is None
    assert error == "provider unavailable"

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=150)

    monkeypatch.setattr(subprocess, "run", timeout)
    flights, error = search_specific_flights("PHX", "LAS", "2026-11-02", "2026-11-05", "ANY", None)
    assert flights == []
    assert "demorou" in error

