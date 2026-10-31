import json
import re
import subprocess
from datetime import date, timedelta

import streamlit as st
import airportsdata

st.set_page_config(page_title="Flight Hunter", page_icon="✈️", layout="wide")
st.title("✈️ Flight Hunter")
st.caption("Encontre tarifas entre destinos selecionados e datas flexíveis. Confirme os valores antes de reservar.")

DESTINATIONS = {
    "Las Vegas": "LAS", "Los Angeles": "LAX", "Denver": "DEN",
    "Miami": "MIA", "Nova York (JFK)": "JFK", "San Francisco": "SFO",
    "Chicago": "ORD", "Seattle": "SEA", "Orlando": "MCO",
    "Boston": "BOS", "Cidade do México": "MEX", "Toronto": "YYZ",
    "Vancouver": "YVR", "São Paulo": "GRU", "Londres": "LHR",
    "Atlanta": "ATL", "Washington DC": "IAD", "Filadélfia": "PHL", "Detroit": "DTW",
    "Minneapolis": "MSP", "Salt Lake City": "SLC", "San Diego": "SAN", "Portland": "PDX",
    "Austin": "AUS", "San Antonio": "SAT", "Nashville": "BNA", "New Orleans": "MSY",
    "Tampa": "TPA", "Fort Lauderdale": "FLL", "Honolulu": "HNL", "San Juan": "SJU",
    "Cancún": "CUN", "Monterrey": "MTY", "Bogotá": "BOG", "Medellín": "MDE",
    "Lima": "LIM", "Santiago": "SCL", "Buenos Aires": "EZE", "Rio de Janeiro": "GIG",
    "Belo Horizonte": "CNF", "Brasília": "BSB", "Salvador": "SSA", "Recife": "REC",
    "Fortaleza": "FOR", "Curitiba": "CWB", "Porto Alegre": "POA", "Campinas": "VCP",
    "Lisboa": "LIS", "Porto": "OPO", "Paris": "CDG", "Madri": "MAD",
    "Barcelona": "BCN", "Roma": "FCO", "Milão": "MXP", "Amsterdã": "AMS",
    "Frankfurt": "FRA", "Zurique": "ZRH", "Dublin": "DUB", "Istambul": "IST",
    "Tóquio": "HND", "Osaka": "KIX", "Seul": "ICN", "Dubai": "DXB",
    "Doha": "DOH", "Bangkok": "BKK", "Singapura": "SIN", "Sydney": "SYD",
}
ORIGINS = {
    "Phoenix": "PHX", "Dallas": "DFW", "Houston": "IAH",
    "Los Angeles": "LAX", "São Paulo": "GRU", "Belo Horizonte": "CNF",
    "Nova York": "JFK", "Miami": "MIA", "Chicago": "ORD", "Atlanta": "ATL",
    "Austin": "AUS", "Rio de Janeiro": "GIG", "Lisboa": "LIS", "Londres": "LHR",
}

@st.cache_resource(show_spinner=False)
def airport_choices():
    from collections import defaultdict
    catalog = airportsdata.load("IATA")
    cities = defaultdict(set)
    choices = {}
    for code, info in catalog.items():
        if not re.fullmatch(r"[A-Z]{3}", code):
            continue
        city = (info.get("city") or "").strip()
        country = (info.get("country") or "").strip()
        name = (info.get("name") or "").strip()
        if city and name:
            cities[(city, country)].add(code)
            choices[f"Aeroporto: {city} · {name} ({code}) · {country}"] = code
    # Include familiar Portuguese names, grouped by the international dataset's city.
    for name, code in {**ORIGINS, **DESTINATIONS}.items():
        choices[f"Aeroporto: {name} ({code})"] = code
    for (city, country), codes in cities.items():
        # A bounded multi-airport request avoids very large queries.
        if len(codes) > 1:
            codes = sorted(codes)
            if len(codes) <= 6:
                choices[f"Cidade: {city} · {country} ({', '.join(codes)})"] = ",".join(codes)
    # Explicit city groups for popular multi-airport metropolitan areas.
    popular = {
        "Nova York": "JFK,LGA,EWR", "São Paulo": "GRU,CGH,VCP",
        "Rio de Janeiro": "GIG,SDU", "Belo Horizonte": "CNF,PLU",
        "Londres": "LHR,LGW,STN,LTN,LCY", "Paris": "CDG,ORY,BVA",
        "Tóquio": "HND,NRT", "Dallas": "DFW,DAL", "Houston": "IAH,HOU",
        "Washington DC": "IAD,DCA,BWI", "Los Angeles": "LAX,BUR,LGB,SNA,ONT",
        "Chicago": "ORD,MDW",
    }
    for name, codes in popular.items():
        choices[f"Cidade: {name} ({codes})"] = codes
    return choices

AIRPORTS = airport_choices()
ORIGIN_OPTIONS = {
    **{f"Cidade: {name}": next((value for label, value in AIRPORTS.items()
        if label.startswith(f"Cidade: {name} (")), code) for name, code in ORIGINS.items()},
    **AIRPORTS,
}
st.info("Escolha uma cidade para incluir os aeroportos apresentados entre parênteses, ou escolha um aeroporto específico. A busca por cidade compara os aeroportos disponíveis, quando compatíveis com o motor.")
departure_flexible = st.checkbox("Flexibilidade na ida", help="Ative para pesquisar antes e/ou depois da data escolhida.")
return_flexible = st.checkbox("Flexibilidade na volta", help="Ative para pesquisar antes e/ou depois da data de volta.")
stop_filter = st.selectbox("Escalas", ["Qualquer voo", "Somente direto", "Até 1 escala"], help="Selecione Somente direto para ocultar opções de conexão.")
with st.form("search"):
    a, b, c = st.columns(3)
    with a:
        origin_name = st.selectbox("Saindo de (cidade ou aeroporto)", list(ORIGIN_OPTIONS), help="Escolha Cidade para incluir todos os aeroportos listados; ou Aeroporto para escolher somente um. Digite o nome para localizar.")
        budget = st.number_input("Orçamento máximo (USD)", min_value=20, max_value=20000, value=500, step=25)
    with b:
        start = st.date_input("Data de ida (MM/DD/YYYY)", value=date.today(), min_value=date.today(), format="MM/DD/YYYY")
        return_mode = st.radio("Como escolher a volta?", ["Data de volta", "Duração da viagem"], horizontal=True, help="Escolha a data exata de volta ou use duração fixa para encontrar preços flexíveis.")
        if return_mode == "Data de volta":
            returning = st.date_input("Data de volta (MM/DD/YYYY)", value=date.today() + timedelta(days=3), min_value=date.today(), format="MM/DD/YYYY")
            trip_duration = None
        else:
            trip_duration = st.number_input("Duração da viagem (dias)", min_value=1, max_value=30, value=3)
            returning = None
    with c:
        if departure_flexible:
            outbound_direction = st.selectbox("Direção da flexibilidade da ida", ["Antes e depois", "Somente antes", "Somente depois"])
            outbound_days = st.slider("Dias de flexibilidade da ida", 1, 5, 2)
        else:
            outbound_direction, outbound_days = "Somente depois", 0
        if return_flexible and return_mode == "Data de volta":
            inbound_direction = st.selectbox("Direção da flexibilidade da volta", ["Antes e depois", "Somente antes", "Somente depois"])
            inbound_days = st.slider("Dias de flexibilidade da volta", 1, 5, 2)
        else:
            inbound_direction, inbound_days = "Somente depois", 0
        selected = st.multiselect("Destinos (cidade ou aeroporto)", list(AIRPORTS), default=[f"Aeroporto: {name} ({code})" for name, code in list(DESTINATIONS.items())[:5]], max_selections=8, help="Digite uma cidade e escolha Cidade para incluir os aeroportos indicados. Escolha Aeroporto para selecionar apenas um.")
        if stop_filter != "Somente direto":
            layover_limit = st.selectbox("Tempo máximo de escala", ["Sem limite", "2 horas", "3 horas", "4 horas", "6 horas", "8 horas"], help="Este filtro é aplicado na busca detalhada dos voos.")
        else:
            layover_limit = "Sem limite"
    submitted = st.form_submit_button("🔎 Encontrar passagens", type="primary", use_container_width=True)

@st.cache_data(ttl=3600, show_spinner=False)
def search(origin, destination, start_str, last_str, duration, stop_code, return_str=None):
    cmd = [
        "fli", "dates", origin, destination,
        "--from", start_str, "--to", last_str,
        "--duration", str(duration), "--round", "--sort", "--format", "json", "--stops", stop_code,
    ]
    if return_str:
        cmd = ["fli", "flights", origin, destination, start_str, "--return", return_str, "--stops", stop_code, "--sort", "CHEAPEST", "--format", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        if proc.returncode != 0:
            return None, (proc.stderr or proc.stdout or "Falha sem detalhes")[-500:]
        payload = json.loads(proc.stdout)
        if return_str:
            flights = [x for x in payload.get("flights", []) if isinstance(x.get("price"), (int, float))]
            if not flights:
                return None, "Nenhum voo encontrado para essas datas"
            best = min(flights, key=lambda x: x["price"])
            return {"departure_date": start_str, "return_date": return_str, "price": best["price"], "booking_url": best.get("booking_url") or payload.get("booking_url", "")}, None
        prices = [
            x for x in payload.get("dates", [])
            if isinstance(x.get("price"), (int, float))
        ]
        if not prices:
            return None, "Nenhuma tarifa encontrada para esse período"
        return min(prices, key=lambda x: x["price"]), None
    except subprocess.TimeoutExpired:
        return None, "A consulta demorou demais"
    except (ValueError, OSError) as err:
        return None, str(err)


def pretty_time(raw):
    if not raw:
        return "Horário indisponível"
    try:
        return __import__("datetime").datetime.fromisoformat(raw).strftime("%m/%d %I:%M %p")
    except (ValueError, TypeError):
        return str(raw)

def pretty_minutes(raw):
    if not isinstance(raw, (int, float)):
        return "Não informado"
    raw = int(raw)
    return f"{raw // 60}h {raw % 60:02d}min"

def airport_code(obj):
    if isinstance(obj, dict):
        return str(obj.get("code") or obj.get("iata_code") or obj.get("name") or "?")
    return str(obj or "?")

@st.cache_data(ttl=1800, show_spinner=False)
def detailed_search(origin, destination, departure, returning, stop_code, layover_limit):
    command = [
        "fli", "flights", origin, destination, departure,
        "--return", returning, "--stops", stop_code,
        "--sort", "CHEAPEST", "--format", "json",
    ]
    if layover_limit != "Sem limite":
        command += ["--max-layover", str(int(layover_limit.split()[0]) * 60)]
    try:
        response = subprocess.run(command, text=True, capture_output=True, timeout=150)
        if response.returncode != 0:
            return [], (response.stderr or response.stdout or "Falha na consulta")[-400:]
        data = json.loads(response.stdout)
        return data.get("flights", []), None
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        return [], str(error)

def display_segment(name, segment):
    st.markdown(f"**{name}**")
    legs = segment.get("legs") or []
    if not legs:
        st.caption("Horários indisponíveis.")
        return
    layovers = segment.get("layovers") or []
    for index, leg in enumerate(legs):
        departure = airport_code(leg.get("departure_airport"))
        arrival = airport_code(leg.get("arrival_airport"))
        st.write(f"✈️ {departure} {pretty_time(leg.get('departure_time'))} → {arrival} {pretty_time(leg.get('arrival_time'))}")
        st.caption(f"Voo {leg.get('flight_number', '')} • Duração {pretty_minutes(leg.get('duration'))}")
        if index < len(legs) - 1:
            if index < len(layovers):
                layover = layovers[index]
                st.info(f"Conexão em {airport_code(layover.get('airport'))} • {pretty_minutes(layover.get('duration'))}" + (" • Pernoite" if layover.get("overnight") else "") + (" • Troca de aeroporto" if layover.get("change_of_airport") else ""))
            else:
                st.info("Conexão com duração não informada")
    st.caption(f"Total: {pretty_minutes(segment.get('duration'))}. Horários locais conforme retornados pela fonte.")

if submitted or st.session_state.get("last_search"):
    origin = ORIGIN_OPTIONS[origin_name]
    destinations_for_search = {city: AIRPORTS[city] for city in selected}
    origin_airports = set(origin.split(","))
    destinations_for_search = {name: code for name, code in destinations_for_search.items() if not set(code.split(",")).issubset(origin_airports)}
    invalid = [code for code in [origin] + list(destinations_for_search.values()) if not re.fullmatch(r"[A-Z]{3}(?:,[A-Z]{3})*", code)]
    if submitted and invalid:
        st.error("O aeroporto selecionado tem um código inválido. Selecione outro aeroporto.")
    elif submitted and len(destinations_for_search) > 8:
        st.error("Selecione no máximo 8 destinos.")
    elif not destinations_for_search and submitted:
        st.warning("Selecione pelo menos um destino diferente da origem.")
    else:
        stop_code = {"Qualquer voo": "ANY", "Somente direto": "0", "Até 1 escala": "1"}[stop_filter]
        def date_options(base, enabled, direction, days):
            offsets = [0]
            if enabled and direction in ("Antes e depois", "Somente antes"):
                offsets += list(range(-days, 0))
            if enabled and direction in ("Antes e depois", "Somente depois"):
                offsets += list(range(1, days + 1))
            return sorted({base + timedelta(days=n) for n in offsets if base + timedelta(days=n) >= date.today()})
        departures = date_options(start, departure_flexible, outbound_direction, outbound_days)
        returns = date_options(returning, return_flexible, inbound_direction, inbound_days) if returning else []
        pairs = [(d, r) for d in departures for r in returns if r > d]
        invalid_return = bool(returning and not pairs)
        calls = len(destinations_for_search) * (len(pairs) if returning else 1)
        skip_search = invalid_return or calls > 40
        if invalid_return:
            st.error("A volta precisa ser posterior à ida.")
        elif submitted and calls > 40:
            st.error(f"Essa pesquisa exigiria {calls} consultas. Reduza a flexibilidade ou o número de destinos (limite de 40).")
        status = st.empty()
        progress = st.progress(0)
        results, errors = [], []
        for i, city in enumerate(destinations_for_search if submitted and not skip_search else [], start=1):
            status.write(f"Pesquisando {city} ({i} de {len(destinations_for_search)})...")
            if returning:
                options, failures = [], []
                for dep, ret in pairs:
                    choice, failure = search(origin, destinations_for_search[city], dep.isoformat(), dep.isoformat(), None, stop_code, ret.isoformat())
                    if choice:
                        options.append(choice)
                    elif failure:
                        failures.append(failure)
                item = min(options, key=lambda x: x["price"]) if options else None
                error = None if item else (failures[0] if failures else "Nenhum voo encontrado.")
            else:
                item, error = search(origin, destinations_for_search[city], departures[0].isoformat(), departures[-1].isoformat(), trip_duration, stop_code)
            if error:
                errors.append((city, error))
            else:
                results.append({
                    "Destino": city,
                    "Código": destinations_for_search[city],
                    "Preço USD": item["price"],
                    "Ida": item["departure_date"],
                    "Volta": item["return_date"],
                    "Link": item.get("booking_url", ""),
                })
            progress.progress(i / len(destinations_for_search))
        status.empty()
        if submitted and not skip_search:
            st.session_state["last_search"] = {"results": results, "errors": errors, "origin": origin, "budget": budget, "stop_code": stop_code, "layover": ("Sem limite" if stop_code == "0" else layover_limit)}
            st.session_state["details"] = {}
        saved = st.session_state.get("last_search")
        if saved is None:
            st.stop()
        results, errors = saved["results"], saved["errors"]
        origin, budget, stop_code, layover_limit = saved["origin"], saved["budget"], saved["stop_code"], saved["layover"]
        results.sort(key=lambda x: x["Preço USD"])
        affordable = [x for x in results if x["Preço USD"] <= budget]
        st.subheader(f"{len(affordable)} opções até ${budget:,.0f}")
        if affordable:
            for r in affordable:
                with st.container(border=True):
                    left, middle, right = st.columns([2, 2, 1])
                    left.markdown(f"**{r['Destino']}**")
                    left.caption(f"{r['Ida']} a {r['Volta']}")
                    middle.metric("Ida e volta", f"${r['Preço USD']:,.0f}")
                    if r["Link"].startswith("https://www.google.com/travel/flights"):
                        right.link_button("Conferir preço", r["Link"])
                    with st.expander("🕒 Horários de saída, chegada e conexões", expanded=True):
                        st.caption("Clique para consultar detalhes do itinerário; o preço pode variar em relação ao calendário.")
                        detail_key = f"detail_{origin}_{r['Destino']}_{r['Ida']}"
                        if st.button("Carregar horários e escalas", key=detail_key):
                            with st.spinner("Consultando voos detalhados..."):
                                st.session_state["details"][detail_key] = detailed_search(origin, r["Código"], r["Ida"], r["Volta"], stop_code, layover_limit)
                        if detail_key in st.session_state.get("details", {}):
                            flights, error = st.session_state["details"][detail_key]
                            if error:
                                st.error(error)
                            else:
                                eligible = sorted([f for f in flights if isinstance(f.get("price"), (int, float)) and f["price"] <= budget], key=lambda f: f["price"])
                                if not eligible:
                                    st.warning("Nenhum itinerário detalhado dentro do orçamento e filtros selecionados. Confira no Google Flights.")
                                for f in eligible[:3]:
                                    st.markdown(f"### USD {f['price']:,.0f}")
                                    st.caption(f"Total de escalas (ida e volta): {f.get('stops', 'não informado')}")
                                    display_segment("Ida", f.get("outbound") or {})
                                    display_segment("Volta", f.get("return") or {})
                                    url = f.get("booking_url", "")
                                    if url.startswith("https://www.google.com/travel/flights"):
                                        st.link_button("Conferir itinerário", url)
                                    st.divider()
        else:
            st.warning("Nenhuma tarifa consultada ficou dentro do orçamento. Tente outras datas ou destinos.")
        if results:
            st.dataframe(results, hide_index=True, use_container_width=True)
            st.download_button(
                "Baixar resultados JSON",
                json.dumps(results, ensure_ascii=False, indent=2),
                file_name="flight_hunter_results.json",
                mime="application/json",
            )
        if errors:
            with st.expander(f"Consultas sem resultado ({len(errors)})"):
                for city, err in errors:
                    st.write(f"**{city}:** {err}")
        st.caption("O filtro de escalas é aplicado ao calendário. O limite de tempo de conexão é aplicado somente na busca detalhada. Horários locais. Confira bagagem, disponibilidade e tarifa final no Google Flights.")

st.divider()
st.caption("Protótipo familiar. A coleta pode falhar em servidores compartilhados devido a mudanças ou restrições do Google.")
