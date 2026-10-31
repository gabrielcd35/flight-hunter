from pathlib import Path
import json
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).parents[1] / "app.py"


def labels(elements):
    return [element.label for element in elements]


def test_app_loads_and_progressively_reveals_date_controls():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not app.exception
    assert "Flexibilidade da ida" not in labels(app.selectbox)

    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert "Flexibilidade da ida" in labels(app.selectbox)
    assert "Número de dias" in labels(app.selectbox)


def test_duration_mode_hides_return_flexibility():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    app.radio[0].set_value("Duração da viagem").run()
    assert not app.exception
    assert "Datas de volta flexíveis" not in labels(app.toggle)
    assert "Duração da viagem em dias" in labels(app.number_input)


def test_nonstop_mode_hides_connection_and_layover_controls():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    app.toggle[-1].set_value(True).run()
    assert not app.exception
    assert "Número máximo de conexões" not in labels(app.selectbox)
    assert "Duração máxima de cada conexão" not in labels(app.selectbox)


def test_exact_date_search_renders_real_itinerary_fields(monkeypatch):
    payload = {
        "success": True,
        "flights": [
            {
                "price": 206,
                "currency": "USD",
                "stops": 0,
                "booking_url": "https://www.google.com/travel/flights/booking?tfs=test",
                "outbound": {
                    "duration": 77,
                    "stops": 0,
                    "legs": [
                        {
                            "departure_airport": {"code": "PHX"},
                            "arrival_airport": {"code": "LAS"},
                            "departure_time": "2026-11-01T08:30:00",
                            "arrival_time": "2026-11-01T08:47:00",
                            "duration": 77,
                            "airline": {"name": "Frontier Airlines"},
                            "flight_number": "1019",
                        }
                    ],
                },
                "return": {
                    "duration": 82,
                    "stops": 0,
                    "legs": [
                        {
                            "departure_airport": {"code": "LAS"},
                            "arrival_airport": {"code": "PHX"},
                            "departure_time": "2026-11-03T11:08:00",
                            "arrival_time": "2026-11-03T13:30:00",
                            "duration": 82,
                            "airline": {"name": "Frontier Airlines"},
                            "flight_number": "4048",
                        }
                    ],
                },
            }
        ],
    }
    monkeypatch.setattr(
        "flight_hunter.search.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""),
    )

    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    app.multiselect[0].set_value(["Aeroporto · Las Vegas (LAS)"]).run()
    app.button[0].click().run()

    assert not app.exception
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "US$ 206" in rendered
    assert "Frontier Airlines" in rendered
    assert "PHX" in rendered and "LAS" in rendered
