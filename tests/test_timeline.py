import pytest

from flight_hunter.timeline import build_segment_timeline


def leg(origin, destination, duration, departure="2026-11-01T08:00:00", arrival="2026-11-01T10:00:00"):
    return {
        "departure_airport": {"code": origin},
        "arrival_airport": {"code": destination},
        "departure_time": departure,
        "arrival_time": arrival,
        "duration": duration,
    }


def layover(airport, duration, **flags):
    return {"airport": {"code": airport}, "duration": duration, **flags}


def test_nonstop_flight_occupies_the_full_timeline():
    timeline = build_segment_timeline(
        {"duration": 180, "legs": [leg("PHX", "ORD", 180)], "layovers": []}
    )

    assert timeline.precise
    assert timeline.total_minutes == 180
    assert timeline.connections == ()
    assert timeline.flights[0].start_percent == 0
    assert timeline.flights[0].end_percent == 100


def test_one_connection_markers_follow_cumulative_elapsed_time():
    timeline = build_segment_timeline(
        {
            "duration": 1200,
            "legs": [
                leg("PHX", "JFK", 600, arrival="2026-11-01T18:00:00"),
                leg("JFK", "LHR", 480, departure="2026-11-01T20:00:00"),
            ],
            "layovers": [layover("JFK", 120)],
        }
    )

    connection = timeline.connections[0]
    assert timeline.precise
    assert connection.arrival_percent == 50
    assert connection.departure_percent == 60
    assert timeline.flights[1].start_percent == 60
    assert timeline.flights[1].end_percent == 100


def test_two_connections_use_each_flight_and_layover_duration():
    timeline = build_segment_timeline(
        {
            "duration": 1620,
            "legs": [
                leg("PHX", "AAA", 600),
                leg("AAA", "BBB", 480),
                leg("BBB", "CCC", 360),
            ],
            "layovers": [layover("AAA", 120), layover("BBB", 60)],
        }
    )

    assert timeline.precise
    assert timeline.connections[0].arrival_percent == pytest.approx(37.037, abs=0.001)
    assert timeline.connections[0].departure_percent == pytest.approx(44.444, abs=0.001)
    assert timeline.connections[1].arrival_percent == pytest.approx(74.074, abs=0.001)
    assert timeline.connections[1].departure_percent == pytest.approx(77.778, abs=0.001)
    assert timeline.flights[-1].end_percent == 100


def test_long_layover_dominates_the_visual_width():
    timeline = build_segment_timeline(
        {
            "duration": 720,
            "legs": [leg("PHX", "DFW", 60), leg("DFW", "AUS", 60)],
            "layovers": [layover("DFW", 600, overnight=True)],
        }
    )

    connection = timeline.connections[0]
    assert connection.arrival_percent == pytest.approx(8.3333, abs=0.001)
    assert connection.departure_percent == pytest.approx(91.6667, abs=0.001)
    assert connection.overnight


def test_naive_local_times_across_midnight_and_time_zones_are_not_subtracted():
    timeline = build_segment_timeline(
        {
            "duration": 900,
            "legs": [
                leg(
                    "LAX",
                    "LHR",
                    600,
                    departure="2026-11-01T23:30:00",
                    arrival="2026-11-02T05:30:00",
                ),
                leg(
                    "LHR",
                    "ATH",
                    180,
                    departure="2026-11-02T08:00:00",
                    arrival="2026-11-02T13:00:00",
                ),
            ],
            "layovers": [layover("LHR", 120)],
        }
    )

    assert timeline.precise
    assert timeline.total_minutes == 900
    assert timeline.connections[0].arrival_percent == pytest.approx(66.6667, abs=0.001)
    assert timeline.connections[0].departure_percent == 80


def test_timezone_aware_timestamps_are_used_as_an_extra_validation():
    timeline = build_segment_timeline(
        {
            "duration": 120,
            "legs": [
                leg(
                    "PHX",
                    "DEN",
                    120,
                    departure="2026-11-01T08:00:00-07:00",
                    arrival="2026-11-01T12:00:00-05:00",
                )
            ],
        }
    )

    assert timeline.precise


def test_missing_layover_duration_uses_clear_fallback():
    timeline = build_segment_timeline(
        {
            "duration": 300,
            "legs": [leg("PHX", "DEN", 120), leg("DEN", "ORD", 120)],
            "layovers": [{"airport": {"code": "DEN"}}],
        }
    )

    assert not timeline.precise
    assert timeline.flights == ()
    assert "conexões" in timeline.unavailable_reason


def test_inconsistent_declared_total_uses_fallback():
    timeline = build_segment_timeline(
        {
            "duration": 999,
            "legs": [leg("PHX", "DEN", 120), leg("DEN", "ORD", 120)],
            "layovers": [layover("DEN", 60)],
        }
    )

    assert not timeline.precise
    assert "não são consistentes" in timeline.unavailable_reason
