import copy
import json
import subprocess
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

from flight_hunter.market_compare import (
    MARKETS,
    TIMEOUT_SECONDS,
    compare_markets,
    comparison_signature,
    itinerary_key,
    same_itinerary_spread,
    validated_market_booking_url,
)


def leg(origin, destination, number, departure, arrival, airline="AA"):
    return {
        "departure_airport": {"code": origin},
        "arrival_airport": {"code": destination},
        "departure_time": departure,
        "arrival_time": arrival,
        "duration": 120,
        "airline": {"code": airline, "name": "Test Air"},
        "flight_number": number,
    }


def itinerary(price=1160, currency="USD", country="US"):
    return {
        "price": price,
        "currency": currency,
        "booking_url": (
            "https://www.google.com/travel/flights/booking?"
            f"tfs=test&curr=USD&hl=en&gl={country}"
        ),
        "outbound": {
            "legs": [
                leg("DFW", "MIA", "AA100", "2027-01-06T08:00:00", "2027-01-06T11:00:00"),
                leg("MIA", "CNF", "AA200", "2027-01-06T13:00:00", "2027-01-07T00:30:00"),
            ]
        },
        "return": {
            "legs": [
                leg("CNF", "DFW", "AA300", "2027-01-20T09:00:00", "2027-01-20T18:00:00")
            ]
        },
    }


def completed(payload, returncode=0, stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=json.dumps(payload), stderr=stderr)


def test_every_supported_market_reaches_fli_with_explicit_locale(monkeypatch):
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        country = command[command.index("--country") + 1]
        return completed({"success": True, "flights": [itinerary(country=country)]})

    monkeypatch.setattr(subprocess, "run", fake_run)
    rows, errors = compare_markets(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "ANY", list(MARKETS)
    )

    assert not errors
    assert {row["País"] for row in rows} == {"US", "BR", "IN", "MX", "CA", "CO", "GB"}
    assert all(row["Link validado"] for row in rows)
    for command, expected_country in zip(commands, MARKETS.values(), strict=True):
        assert command[command.index("--country") + 1] == expected_country
        assert command[command.index("--currency") + 1] == "USD"
        assert command[command.index("--language") + 1] == "en"
        assert command[command.index("--top-n") + 1] == "10"


@pytest.mark.parametrize("country", ["US", "BR", "IN", "MX", "CA", "CO", "GB"])
def test_installed_fli_builds_the_expected_google_locale_url(country):
    from fli.search._tfs import page_url

    params = parse_qs(urlparse(page_url("token", "USD", "en", country)).query)
    assert params == {"tfs": ["token"], "curr": ["USD"], "hl": ["en"], "gl": [country]}


def test_itinerary_key_matches_identical_flights_only():
    original = itinerary()
    assert itinerary_key(original) == itinerary_key(copy.deepcopy(original))

    different_number = copy.deepcopy(original)
    different_number["outbound"]["legs"][0]["flight_number"] = "AA999"
    assert itinerary_key(original) != itinerary_key(different_number)

    different_departure = copy.deepcopy(original)
    different_departure["outbound"]["legs"][0]["departure_time"] = "2027-01-06T09:00:00"
    assert itinerary_key(original) != itinerary_key(different_departure)

    different_arrival = copy.deepcopy(original)
    different_arrival["outbound"]["legs"][1]["arrival_time"] = "2027-01-07T01:30:00"
    assert itinerary_key(original) != itinerary_key(different_arrival)

    different_connection = copy.deepcopy(original)
    different_connection["outbound"]["legs"][0]["arrival_airport"] = {"code": "ATL"}
    different_connection["outbound"]["legs"][1]["departure_airport"] = {"code": "ATL"}
    assert itinerary_key(original) != itinerary_key(different_connection)


def test_itinerary_key_rejects_missing_flight_data():
    incomplete = itinerary()
    incomplete["outbound"]["legs"][0].pop("flight_number")
    assert itinerary_key(incomplete) is None
    assert itinerary_key({"outbound": {}, "return": {}}) is None


def test_comparison_reports_cheapest_and_same_itinerary_separately(monkeypatch):
    reference = itinerary(price=700)
    cheaper_different_flight = itinerary(price=500, country="BR")
    cheaper_different_flight["outbound"]["legs"][0]["flight_number"] = "AA999"
    same_flight = itinerary(price=650, country="BR")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: completed(
            {"success": True, "flights": [cheaper_different_flight, same_flight]}
        ),
    )

    rows, errors = compare_markets(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "ANY", ["Brasil"], reference
    )

    assert not errors
    assert rows[0]["Menor tarifa (USD)"] == 500
    assert rows[0]["Mesmo itinerário (USD)"] == 650


def test_same_itinerary_spread_detects_differences_and_ignores_missing_matches():
    rows = [
        {"Mesmo itinerário (USD)": 1160},
        {"Mesmo itinerário (USD)": None},
        {"Mesmo itinerário (USD)": 1095},
    ]
    assert same_itinerary_spread(rows) == 65
    assert same_itinerary_spread(rows[:2]) is None
    assert same_itinerary_spread(
        [{"Mesmo itinerário (USD)": 1160}, {"Mesmo itinerário (USD)": 1160}]
    ) == 0


def test_non_usd_fares_are_never_compared_as_usd(monkeypatch):
    eur = itinerary(price=400, currency="EUR", country="CA")
    usd = itinerary(price=600, currency="USD", country="CA")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: completed({"success": True, "flights": [eur, usd]}),
    )
    rows, errors = compare_markets(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "ANY", ["Canadá"]
    )
    assert not errors
    assert rows[0]["Menor tarifa (USD)"] == 600

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: completed({"success": True, "flights": [eur]}),
    )
    rows, errors = compare_markets(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "ANY", ["Canadá"]
    )
    assert rows == []
    assert errors == ["Canadá: nenhuma tarifa válida em USD"]


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (SimpleNamespace(returncode=1, stdout="", stderr="failed"), "consulta indisponível"),
        (SimpleNamespace(returncode=0, stdout="not-json", stderr=""), "resposta inválida"),
        (completed({"success": False, "error": "blocked"}), "consulta retornou falha"),
        (completed({"success": True, "flights": []}), "nenhuma tarifa válida em USD"),
        (completed({"success": True}), "nenhuma tarifa válida em USD"),
    ],
)
def test_failed_and_empty_responses_are_reported(monkeypatch, response, message):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: response)
    rows, errors = compare_markets(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "ANY", ["México"]
    )
    assert rows == []
    assert message in errors[0]


def test_timeout_isolated_to_its_market(monkeypatch):
    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, TIMEOUT_SECONDS)

    monkeypatch.setattr(subprocess, "run", timeout)
    rows, errors = compare_markets(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "ANY", ["Índia"]
    )
    assert rows == []
    assert errors == [f"Índia: consulta excedeu {TIMEOUT_SECONDS}s"]


def test_cache_signature_changes_for_every_material_input():
    base = comparison_signature(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "ANY", ["Brasil"], itinerary()
    )
    assert base != comparison_signature(
        "DFW", "CNF", "2027-01-07", "2027-01-20", "ANY", ["Brasil"], itinerary()
    )
    assert base != comparison_signature(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "0", ["Brasil"], itinerary()
    )
    assert base != comparison_signature(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "ANY", ["México"], itinerary()
    )
    changed_reference = itinerary()
    changed_reference["return"]["legs"][0]["flight_number"] = "AA301"
    assert base != comparison_signature(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "ANY", ["Brasil"], changed_reference
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/travel/flights/booking?curr=USD&hl=en&gl=BR",
        "http://www.google.com/travel/flights/booking?curr=USD&hl=en&gl=BR",
        "https://www.google.com/travel/flights/booking?curr=EUR&hl=en&gl=BR",
        "https://www.google.com/travel/flights/booking?curr=USD&hl=pt-BR&gl=BR",
        "https://www.google.com/travel/flights/booking?curr=USD&hl=en&gl=US",
        "https://www.google.com/travel/flights/booking?tfs=test",
    ],
)
def test_market_booking_url_rejects_wrong_or_missing_locale(url):
    assert validated_market_booking_url(url, "BR") is None


def test_market_booking_url_accepts_exact_country_currency_and_language():
    url = "https://www.google.com/travel/flights/booking?tfs=test&curr=USD&hl=en&gl=BR"
    assert validated_market_booking_url(url, "BR") == url


def test_invalid_returned_booking_url_is_not_exposed(monkeypatch):
    result = itinerary(country="US")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: completed({"success": True, "flights": [result]}),
    )
    rows, errors = compare_markets(
        "DFW", "CNF", "2027-01-06", "2027-01-20", "ANY", ["Brasil"]
    )
    assert rows[0]["Link"] == ""
    assert not rows[0]["Link validado"]
    assert "link não confirmou" in errors[0]
