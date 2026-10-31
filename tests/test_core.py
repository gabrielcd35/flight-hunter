from datetime import date

from flight_hunter.core import (
    connection_label,
    date_options,
    filter_destinations,
    safe_google_flights_url,
    valid_airport_codes,
    valid_date_pairs,
)


def test_date_options_supports_independent_directions_and_excludes_past_dates():
    today = date(2026, 10, 31)
    assert date_options(today, True, "Antes e depois", 2, today=today) == [
        date(2026, 10, 31),
        date(2026, 11, 1),
        date(2026, 11, 2),
    ]
    assert date_options(date(2026, 11, 5), True, "Somente antes", 2, today=today) == [
        date(2026, 11, 3),
        date(2026, 11, 4),
        date(2026, 11, 5),
    ]


def test_valid_date_pairs_rejects_same_day_and_return_before_departure():
    departures = [date(2026, 11, 2), date(2026, 11, 3)]
    returns = [date(2026, 11, 2), date(2026, 11, 4)]
    assert valid_date_pairs(departures, returns) == [
        (date(2026, 11, 2), date(2026, 11, 4)),
        (date(2026, 11, 3), date(2026, 11, 4)),
    ]


def test_airport_validation_and_same_city_filtering():
    assert valid_airport_codes("JFK,LGA,EWR")
    assert not valid_airport_codes("JFK,evil")
    destinations = {"Nova York": "JFK,LGA,EWR", "Miami": "MIA"}
    assert filter_destinations("JFK,LGA,EWR", destinations) == {"Miami": "MIA"}


def test_only_google_flights_links_are_allowed():
    valid = "https://www.google.com/travel/flights/search?tfs=abc"
    assert safe_google_flights_url(valid) == valid
    assert safe_google_flights_url("http://www.google.com/travel/flights") is None
    assert safe_google_flights_url("https://example.com/travel/flights") is None
    assert safe_google_flights_url("https://www.google.com/search?q=flights") is None


def test_connection_label_uses_stops_or_legs():
    assert connection_label({"stops": 0, "legs": [{}, {}]}) == "Voo direto"
    assert connection_label({"stops": 1}) == "1 conexão"
    assert connection_label({"legs": [{}, {}, {}]}) == "2 conexões"

