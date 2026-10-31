import json
import subprocess
from datetime import date, timedelta

import streamlit as st

st.set_page_config(page_title="Flight Hunter", page_icon="✈️", layout="wide")
st.title("✈️ Flight Hunter")
st.caption("Encontre tarifas entre destinos selecionados e datas flexíveis. Confirme os valores antes de reservar.")

DESTINATIONS = {
    "Las Vegas": "LAS", "Los Angeles": "LAX", "Denver": "DEN",
    "Miami": "MIA", "Nova York (JFK)": "JFK", "San Francisco": "SFO",
    "Chicago": "ORD", "Seattle": "SEA", "Orlando": "MCO",
    "Boston": "BOS", "Cidade do México": "MEX", "Toronto": "YYZ",
    "Vancouver": "YVR", "São Paulo": "GRU", "Londres": "LHR",
}
ORIGINS = {
    "Phoenix": "PHX", "Dallas": "DFW", "Houston": "IAH",
    "Los Angeles": "LAX", "São Paulo": "GRU",
}

st.info("Nesta versão, 'qualquer lugar' significa pesquisar os destinos selecionados. Não inclui todos os aeroportos do mundo.")
with st.form("search"):
    a, b, c = st.columns(3)
    with a:
        origin_name = st.selectbox("Saindo de", list(ORIGINS))
        budget = st.number_input("Orçamento máximo (USD)", min_value=20, max_value=20000, value=500, step=25)
    with b:
        start = st.date_input("Primeira data de ida", value=date.today() + timedelta(days=20), min_value=date.today())
        trip_duration = st.number_input("Duração da viagem (dias)", min_value=1, max_value=30, value=3)
    with c:
        window = st.slider("Pesquisar quantos dias de saída?", min_value=3, max_value=14, value=7)
        selected = st.multiselect("Destinos", list(DESTINATIONS), default=list(DESTINATIONS)[:5], max_selections=8)
    submitted = st.form_submit_button("🔎 Encontrar passagens", type="primary", use_container_width=True)

@st.cache_data(ttl=3600, show_spinner=False)
def search(origin, destination, start_str, last_str, duration):
    cmd = [
        "fli", "dates", origin, destination,
        "--from", start_str, "--to", last_str,
        "--duration", str(duration), "--round", "--sort", "--format", "json",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        if proc.returncode != 0:
            return None, (proc.stderr or proc.stdout or "Falha sem detalhes")[-500:]
        payload = json.loads(proc.stdout)
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

if submitted:
    origin = ORIGINS[origin_name]
    selected = [city for city in selected if DESTINATIONS[city] != origin]
    if not selected:
        st.warning("Selecione pelo menos um destino diferente da origem.")
    else:
        first_day = start.isoformat()
        last_day = (start + timedelta(days=window - 1)).isoformat()
        status = st.empty()
        progress = st.progress(0)
        results, errors = [], []
        for i, city in enumerate(selected, start=1):
            status.write(f"Pesquisando {city} ({i} de {len(selected)})...")
            item, error = search(
                origin, DESTINATIONS[city], first_day, last_day, trip_duration
            )
            if error:
                errors.append((city, error))
            else:
                results.append({
                    "Destino": city,
                    "Preço USD": item["price"],
                    "Ida": item["departure_date"],
                    "Volta": item["return_date"],
                    "Link": item.get("booking_url", ""),
                })
            progress.progress(i / len(selected))
        status.empty()
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
        st.caption("Preços indicativos do Google Flights via FLI. Verifique bagagem, disponibilidade e preço final.")

st.divider()
st.caption("Protótipo familiar. A coleta pode falhar em servidores compartilhados devido a mudanças ou restrições do Google.")
