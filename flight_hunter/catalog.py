"""Airport catalog construction for the Flight Hunter search form."""

from __future__ import annotations

import re
from collections import defaultdict

import airportsdata


DESTINATIONS = {
    "Las Vegas": "LAS",
    "Los Angeles": "LAX",
    "Denver": "DEN",
    "Miami": "MIA",
    "Nova York (JFK)": "JFK",
    "San Francisco": "SFO",
    "Chicago": "ORD",
    "Seattle": "SEA",
    "Orlando": "MCO",
    "Boston": "BOS",
    "Cidade do México": "MEX",
    "Toronto": "YYZ",
    "Vancouver": "YVR",
    "São Paulo": "GRU",
    "Londres": "LHR",
    "Atlanta": "ATL",
    "Washington DC": "IAD",
    "Filadélfia": "PHL",
    "Detroit": "DTW",
    "Minneapolis": "MSP",
    "Salt Lake City": "SLC",
    "San Diego": "SAN",
    "Portland": "PDX",
    "Austin": "AUS",
    "San Antonio": "SAT",
    "Nashville": "BNA",
    "New Orleans": "MSY",
    "Tampa": "TPA",
    "Fort Lauderdale": "FLL",
    "Honolulu": "HNL",
    "San Juan": "SJU",
    "Cancún": "CUN",
    "Monterrey": "MTY",
    "Bogotá": "BOG",
    "Medellín": "MDE",
    "Lima": "LIM",
    "Santiago": "SCL",
    "Buenos Aires": "EZE",
    "Rio de Janeiro": "GIG",
    "Belo Horizonte": "CNF",
    "Brasília": "BSB",
    "Salvador": "SSA",
    "Recife": "REC",
    "Fortaleza": "FOR",
    "Curitiba": "CWB",
    "Porto Alegre": "POA",
    "Campinas": "VCP",
    "Lisboa": "LIS",
    "Porto": "OPO",
    "Paris": "CDG",
    "Madri": "MAD",
    "Barcelona": "BCN",
    "Roma": "FCO",
    "Milão": "MXP",
    "Amsterdã": "AMS",
    "Frankfurt": "FRA",
    "Zurique": "ZRH",
    "Dublin": "DUB",
    "Istambul": "IST",
    "Tóquio": "HND",
    "Osaka": "KIX",
    "Seul": "ICN",
    "Dubai": "DXB",
    "Doha": "DOH",
    "Bangkok": "BKK",
    "Singapura": "SIN",
    "Sydney": "SYD",
}

ORIGINS = {
    "Phoenix": "PHX",
    "Dallas": "DFW",
    "Houston": "IAH",
    "Los Angeles": "LAX",
    "São Paulo": "GRU",
    "Belo Horizonte": "CNF",
    "Nova York": "JFK",
    "Miami": "MIA",
    "Chicago": "ORD",
    "Atlanta": "ATL",
    "Austin": "AUS",
    "Rio de Janeiro": "GIG",
    "Lisboa": "LIS",
    "Londres": "LHR",
}

POPULAR_CITY_GROUPS = {
    "Nova York": "JFK,LGA,EWR",
    "São Paulo": "GRU,CGH,VCP",
    "Rio de Janeiro": "GIG,SDU",
    "Belo Horizonte": "CNF,PLU",
    "Londres": "LHR,LGW,STN,LTN,LCY",
    "Paris": "CDG,ORY,BVA",
    "Tóquio": "HND,NRT",
    "Dallas": "DFW,DAL",
    "Houston": "IAH,HOU",
    "Washington DC": "IAD,DCA,BWI",
    "Los Angeles": "LAX,BUR,LGB,SNA,ONT",
    "Chicago": "ORD,MDW",
}


def build_airport_choices() -> dict[str, str]:
    """Return searchable city and airport labels mapped to FLI IATA values."""
    catalog = airportsdata.load("IATA")
    cities: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    choices: dict[str, str] = {}

    for code, info in catalog.items():
        if not re.fullmatch(r"[A-Z]{3}", code):
            continue
        city = (info.get("city") or "").strip()
        country = (info.get("country") or "").strip()
        name = (info.get("name") or "").strip()
        if city and name:
            cities[(city, country)].add(code)
            choices[f"Aeroporto · {city} — {name} ({code}) · {country}"] = code

    # Keep familiar Portuguese labels near the top of the searchable list.
    familiar: dict[str, str] = {}
    for name, code in {**ORIGINS, **DESTINATIONS}.items():
        familiar[f"Aeroporto · {name} ({code})"] = code

    grouped: dict[str, str] = {}
    for (city, country), codes in cities.items():
        ordered_codes = sorted(codes)
        if 1 < len(ordered_codes) <= 6:
            code_list = ",".join(ordered_codes)
            grouped[f"Cidade · {city}, {country} ({', '.join(ordered_codes)})"] = code_list

    for name, codes in POPULAR_CITY_GROUPS.items():
        grouped[f"Cidade · {name} ({codes.replace(',', ', ')})"] = codes

    return {**familiar, **grouped, **choices}


def build_origin_choices(airport_choices: dict[str, str]) -> dict[str, str]:
    """Put common origin cities first while preserving the full airport catalog."""
    common: dict[str, str] = {}
    for name, fallback_code in ORIGINS.items():
        grouped_code = next(
            (
                value
                for label, value in airport_choices.items()
                if label.startswith(f"Cidade · {name} (")
            ),
            fallback_code,
        )
        common[f"Cidade · {name}"] = grouped_code
    return {**common, **airport_choices}

