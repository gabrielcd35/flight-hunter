from __future__ import annotations

import html
import json
from datetime import date, timedelta
from typing import Any

import streamlit as st

from flight_hunter.catalog import build_airport_choices, build_origin_choices
from flight_hunter.core import (
    airport_code,
    airline_label,
    connection_label,
    date_options,
    filter_destinations,
    format_date,
    format_minutes,
    format_short_date,
    format_time,
    safe_google_flights_url,
    segment_airlines,
    valid_airport_codes,
    valid_date_pairs,
)
from flight_hunter.search import cheapest_specific_flight, search_calendar, search_specific_flights
from flight_hunter.theme import APP_CSS


st.set_page_config(
    page_title="Flight Hunter · Descubra voos melhores",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(APP_CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def airport_catalogs() -> tuple[dict[str, str], dict[str, str]]:
    airports = build_airport_choices()
    return airports, build_origin_choices(airports)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_calendar_search(
    origin: str,
    destination: str,
    first_departure: str,
    last_departure: str,
    duration: int,
    stop_code: str,
    layover_minutes: int | None,
) -> tuple[dict[str, Any] | None, str | None]:
    return search_calendar(
        origin,
        destination,
        first_departure,
        last_departure,
        duration,
        stop_code,
        layover_minutes,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def cached_specific_search(
    origin: str,
    destination: str,
    departure: str,
    returning: str,
    stop_code: str,
    layover_minutes: int | None,
) -> tuple[dict[str, Any] | None, str | None]:
    return cheapest_specific_flight(
        origin,
        destination,
        departure,
        returning,
        stop_code,
        layover_minutes,
    )


@st.cache_data(ttl=1800, show_spinner=False)
def cached_itinerary_search(
    origin: str,
    destination: str,
    departure: str,
    returning: str,
    stop_code: str,
    layover_minutes: int | None,
) -> tuple[list[dict[str, Any]], str | None]:
    return search_specific_flights(
        origin,
        destination,
        departure,
        returning,
        stop_code,
        layover_minutes,
    )


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_hero() -> None:
    st.markdown(
        """
        <section class="fh-hero">
            <div class="fh-brand">
                <div class="fh-mark"><span>✈</span></div>
                <span>Flight Hunter</span>
            </div>
            <p class="fh-eyebrow">Busca inteligente de passagens</p>
            <h1>Mais possibilidades.<br><span>Uma escolha mais simples.</span></h1>
            <p class="fh-hero-copy">
                Compare datas e destinos em uma única busca. Encontre uma tarifa promissora,
                confira o itinerário real e finalize com segurança no Google Flights.
            </p>
            <div class="fh-trust-row">
                <span class="fh-trust-chip">✓ Aeroportos internacionais</span>
                <span class="fh-trust-chip">✓ Datas flexíveis independentes</span>
                <span class="fh-trust-chip">✓ Verificação no Google Flights</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_step(number: int, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="fh-step">
            <span class="fh-step-number">{number:02d}</span>
            <div><h3>{escape(title)}</h3><p>{escape(description)}</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def segment_markup(title: str, segment: dict[str, Any]) -> str:
    legs = segment.get("legs") or []
    if not legs:
        return (
            '<div class="fh-segment"><div class="fh-segment-top">'
            f"<strong>{escape(title)}</strong></div>"
            '<div class="fh-segment-meta">Horários não informados pela fonte.</div></div>'
        )

    first_leg, last_leg = legs[0], legs[-1]
    departure_time = format_time(first_leg.get("departure_time"))
    arrival_time = format_time(last_leg.get("arrival_time"))
    departure_date = format_short_date(first_leg.get("departure_time"))
    arrival_date = format_short_date(last_leg.get("arrival_time"))
    departure_airport = airport_code(first_leg.get("departure_airport"))
    arrival_airport = airport_code(last_leg.get("arrival_airport"))
    airlines = " + ".join(segment_airlines(segment)) or "Companhia não informada"

    details: list[str] = []
    layovers = segment.get("layovers") or []
    for index, leg in enumerate(legs):
        airline = airline_label(leg.get("airline"))
        flight_number = leg.get("flight_number") or ""
        details.append(
            '<div class="fh-leg">'
            f"{escape(airport_code(leg.get('departure_airport')))} {escape(format_time(leg.get('departure_time')))}"
            " &nbsp;→&nbsp; "
            f"{escape(airport_code(leg.get('arrival_airport')))} {escape(format_time(leg.get('arrival_time')))}"
            f" · {escape(airline)} {escape(flight_number)} · {escape(format_minutes(leg.get('duration')))}"
            "</div>"
        )
        if index < len(legs) - 1:
            if index < len(layovers):
                layover = layovers[index]
                flags = []
                if layover.get("overnight"):
                    flags.append("pernoite")
                if layover.get("change_of_airport"):
                    flags.append("troca de aeroporto")
                suffix = f" · {', '.join(flags)}" if flags else ""
                details.append(
                    '<div class="fh-layover">Conexão em '
                    f"{escape(airport_code(layover.get('airport')))} · "
                    f"{escape(format_minutes(layover.get('duration')))}{escape(suffix)}</div>"
                )
            else:
                details.append('<div class="fh-layover">Duração da conexão não informada</div>')

    return f"""
        <div class="fh-segment">
            <div class="fh-segment-top">
                <strong>{escape(title)}</strong>
                <span>{escape(airlines)}</span>
            </div>
            <div class="fh-time-row">
                <span class="fh-time">{escape(departure_time)}</span>
                <span class="fh-flight-line"></span>
                <span class="fh-time">{escape(arrival_time)}</span>
            </div>
            <div class="fh-airports">
                <span>{escape(departure_airport)} · {escape(departure_date)}</span>
                <span>{escape(arrival_airport)} · {escape(arrival_date)}</span>
            </div>
            <div class="fh-segment-meta">
                {escape(format_minutes(segment.get('duration')))} · {escape(connection_label(segment))}
            </div>
            <div class="fh-leg-list">{''.join(details)}</div>
        </div>
    """


def render_itinerary(flight: dict[str, Any]) -> None:
    outbound = flight.get("outbound") or {}
    returning = flight.get("return") or {}
    st.html(
        '<div class="fh-itinerary-grid">'
        + segment_markup("Ida", outbound)
        + segment_markup("Volta", returning)
        + "</div>",
    )
    st.markdown(
        '<p class="fh-confirm-note">Horários exibidos no fuso local de cada aeroporto, conforme retornados pela fonte.</p>',
        unsafe_allow_html=True,
    )


def signature_for(values: dict[str, Any]) -> str:
    return json.dumps(values, sort_keys=True, ensure_ascii=False, default=str)


def render_fare_card(
    result: dict[str, Any],
    index: int,
    saved: dict[str, Any],
    current_budget: int,
) -> None:
    is_confirmed = result["fare_type"] == "specific"
    badge_class = "confirmed" if is_confirmed else ""
    badge_label = "Itinerário encontrado" if is_confirmed else "Tarifa de calendário"
    source_label = "Busca detalhada" if is_confirmed else "Estimativa de calendário"
    price = float(result["price"])
    price_text = f"US$ {price:,.0f}"

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="fh-fare-head">
                <div>
                    <span class="fh-badge {badge_class}">{escape(badge_label)}</span>
                    <h3 class="fh-fare-title">{escape(result['destination'])}
                        <span>{escape(result['code'])}</span>
                    </h3>
                    <p class="fh-route">{escape(saved['origin'])} → {escape(result['code'])} · ida e volta</p>
                </div>
                <div class="fh-price">
                    <span>Preço total</span>
                    <strong>{escape(price_text)}</strong>
                    <small>1 adulto · classe econômica</small>
                </div>
            </div>
            <div class="fh-facts">
                <div class="fh-fact"><span>Ida</span><strong>{escape(format_date(result['departure_date']))}</strong></div>
                <div class="fh-fact"><span>Volta</span><strong>{escape(format_date(result['return_date']))}</strong></div>
                <div class="fh-fact"><span>Tipo de resultado</span><strong>{escape(source_label)}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        booking_url = safe_google_flights_url(result.get("booking_url"))

        if is_confirmed and result.get("itinerary"):
            render_itinerary(result["itinerary"])
            st.caption(
                "Este preço está associado ao itinerário exibido, mas disponibilidade e valor final ainda podem mudar."
            )
            if booking_url:
                st.link_button(
                    "Verificar este itinerário no Google Flights ↗",
                    booking_url,
                    use_container_width=True,
                )
            return

        st.markdown(
            """
            <div class="fh-calendar-note">
                Este é o menor valor encontrado no calendário para estas datas. Companhia, horários e conexões
                só aparecem depois da consulta detalhada — nenhum dado de itinerário é estimado.
            </div>
            """,
            unsafe_allow_html=True,
        )
        detail_key = (
            f"details_{saved['origin']}_{result['code']}_"
            f"{result['departure_date']}_{result['return_date']}_{saved['stop_code']}_{saved['layover_minutes']}"
        )
        action_col, link_col = st.columns(2, gap="small")
        with action_col:
            load_details = st.button(
                "Consultar horários e conexões",
                key=f"load_{index}_{detail_key}",
                use_container_width=True,
            )
        with link_col:
            if booking_url:
                st.link_button(
                    "Ver tarifa no Google Flights ↗",
                    booking_url,
                    use_container_width=True,
                )

        if load_details:
            with st.spinner("Consultando itinerários reais para estas datas…"):
                st.session_state["details"][detail_key] = cached_itinerary_search(
                    saved["origin"],
                    result["code"],
                    result["departure_date"],
                    result["return_date"],
                    saved["stop_code"],
                    saved["layover_minutes"],
                )

        if detail_key not in st.session_state.get("details", {}):
            return

        flights, error = st.session_state["details"][detail_key]
        if error:
            st.error(error)
            return

        eligible = sorted(
            [flight for flight in flights if float(flight["price"]) <= current_budget],
            key=lambda flight: flight["price"],
        )
        if not eligible:
            st.warning(
                "Os itinerários detalhados disponíveis agora estão acima do orçamento. "
                "A tarifa de calendário pode ter mudado."
            )
            return

        st.markdown("#### Itinerários detalhados dentro do orçamento")
        for option_index, flight in enumerate(eligible[:3], start=1):
            st.markdown(
                f"**Opção {option_index} · US$ {float(flight['price']):,.0f} · "
                f"{escape(connection_label(flight.get('outbound') or {}))} na ida**"
            )
            render_itinerary(flight)
            option_url = safe_google_flights_url(flight.get("booking_url"))
            if option_url:
                st.link_button(
                    f"Verificar opção {option_index} no Google Flights ↗",
                    option_url,
                    key=f"book_{detail_key}_{option_index}",
                )
            if option_index < min(len(eligible), 3):
                st.divider()


AIRPORTS, ORIGIN_OPTIONS = airport_catalogs()
st.session_state.setdefault("details", {})

render_hero()
st.markdown(
    """
    <div class="fh-intro">
        <div><h2>Planeje sua próxima viagem</h2><p>As opções aparecem somente quando são relevantes.</p></div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    render_step(1, "Onde você quer voar?", "Pesquise por cidade para incluir aeroportos próximos ou escolha um aeroporto específico.")
    origin_col, destination_col = st.columns(2, gap="large")
    with origin_col:
        origin_name = st.selectbox(
            "De onde você sai?",
            list(ORIGIN_OPTIONS),
            help="A opção Cidade inclui os aeroportos listados quando o motor de busca permite.",
        )
    with destination_col:
        selected = st.multiselect(
            "Para onde você quer ir?",
            list(AIRPORTS),
            default=[],
            max_selections=8,
            placeholder="Digite uma cidade ou código IATA",
            help="Você pode comparar até oito destinos na mesma busca.",
        )

with st.container(border=True):
    render_step(2, "Quando você quer sair?", "Comece por uma data exata e amplie a busca apenas se quiser flexibilidade.")
    departure_col, departure_flex_col = st.columns([1, 1.2], gap="large")
    with departure_col:
        start = st.date_input(
            "Data de ida (MM/DD/YYYY)",
            value=date.today(),
            min_value=date.today(),
            format="MM/DD/YYYY",
        )
    with departure_flex_col:
        departure_flexible = st.toggle(
            "Datas de ida flexíveis",
            help="Pesquise alguns dias antes, depois ou nos dois sentidos.",
        )
        if departure_flexible:
            direction_col, days_col = st.columns([1.4, 1], gap="small")
            with direction_col:
                outbound_direction = st.selectbox(
                    "Flexibilidade da ida",
                    ["Antes e depois", "Somente antes", "Somente depois"],
                )
            with days_col:
                outbound_days = st.selectbox("Número de dias", [1, 2, 3, 4, 5], index=1)
        else:
            outbound_direction, outbound_days = "Somente depois", 0

with st.container(border=True):
    render_step(3, "Quando você quer voltar?", "Escolha uma volta exata ou deixe o Flight Hunter calcular pela duração da viagem.")
    return_mode = st.radio(
        "Como definir a volta?",
        ["Data de volta", "Duração da viagem"],
        horizontal=True,
    )
    if return_mode == "Data de volta":
        return_col, return_flex_col = st.columns([1, 1.2], gap="large")
        with return_col:
            returning = st.date_input(
                "Data de volta (MM/DD/YYYY)",
                value=max(start + timedelta(days=3), date.today() + timedelta(days=1)),
                min_value=start + timedelta(days=1),
                format="MM/DD/YYYY",
            )
        trip_duration = None
        with return_flex_col:
            return_flexible = st.toggle(
                "Datas de volta flexíveis",
                help="A flexibilidade da volta funciona de forma independente da ida.",
            )
            if return_flexible:
                return_direction_col, return_days_col = st.columns([1.4, 1], gap="small")
                with return_direction_col:
                    inbound_direction = st.selectbox(
                        "Flexibilidade da volta",
                        ["Antes e depois", "Somente antes", "Somente depois"],
                    )
                with return_days_col:
                    inbound_days = st.selectbox("Número de dias da volta", [1, 2, 3, 4, 5], index=1)
            else:
                inbound_direction, inbound_days = "Somente depois", 0
    else:
        returning = None
        return_flexible = False
        inbound_direction, inbound_days = "Somente depois", 0
        trip_duration = st.number_input(
            "Duração da viagem em dias",
            min_value=1,
            max_value=30,
            value=3,
            help="A volta será calculada a partir de cada data de ida pesquisada.",
        )

with st.container(border=True):
    render_step(4, "Preferências do voo", "Defina o que realmente importa; os demais filtros ficam fora do caminho.")
    budget_col, nonstop_col = st.columns(2, gap="large")
    with budget_col:
        budget = st.number_input(
            "Orçamento máximo por pessoa (USD)",
            min_value=20,
            max_value=20_000,
            value=500,
            step=25,
        )
    with nonstop_col:
        nonstop_only = st.toggle("Somente voos diretos")
        st.caption("Sem conexões na ida e na volta." if nonstop_only else "Voos com conexão também podem aparecer.")

    with st.expander("Preferências avançadas", expanded=False):
        if nonstop_only:
            stop_label = "Somente direto"
            stop_code = "0"
            layover_label = "Não se aplica"
            layover_minutes = None
            st.info("O limite de conexão não se aplica porque você escolheu somente voos diretos.")
        else:
            connection_col, layover_col = st.columns(2, gap="large")
            with connection_col:
                stop_label = st.selectbox(
                    "Número máximo de conexões",
                    ["Sem limite", "Até 1 conexão", "Até 2 conexões"],
                    index=1,
                )
                stop_code = {"Sem limite": "ANY", "Até 1 conexão": "1", "Até 2 conexões": "2"}[stop_label]
            with layover_col:
                layover_label = st.selectbox(
                    "Duração máxima de cada conexão",
                    ["Sem limite", "2 horas", "3 horas", "4 horas", "6 horas", "8 horas"],
                )
                layover_minutes = None if layover_label == "Sem limite" else int(layover_label.split()[0]) * 60

submitted = st.button("Buscar melhores voos  →", type="primary", use_container_width=True)
st.markdown(
    '<p class="fh-search-note">Buscas detalhadas podem levar alguns instantes. Nunca exibimos horários ou companhias inventados.</p>',
    unsafe_allow_html=True,
)

origin = ORIGIN_OPTIONS[origin_name]
destinations_for_search = filter_destinations(
    origin,
    {label: AIRPORTS[label] for label in selected},
)
departures = date_options(start, departure_flexible, outbound_direction, outbound_days)
returns = date_options(returning, return_flexible, inbound_direction, inbound_days) if returning else []
pairs = valid_date_pairs(departures, returns) if returning else []

current_signature = signature_for(
    {
        "origin": origin,
        "destinations": destinations_for_search,
        "start": start,
        "departure_flexible": departure_flexible,
        "outbound_direction": outbound_direction,
        "outbound_days": outbound_days,
        "return_mode": return_mode,
        "returning": returning,
        "return_flexible": return_flexible,
        "inbound_direction": inbound_direction,
        "inbound_days": inbound_days,
        "trip_duration": trip_duration,
        "stop_code": stop_code,
        "layover_minutes": layover_minutes,
    }
)

if submitted:
    invalid_codes = [
        codes
        for codes in [origin, *destinations_for_search.values()]
        if not valid_airport_codes(codes)
    ]
    call_count = len(destinations_for_search) * (len(pairs) if returning else 1)

    if invalid_codes:
        st.error("Um dos aeroportos selecionados tem código inválido. Escolha outra opção no catálogo.")
    elif not destinations_for_search:
        st.warning("Escolha pelo menos um destino diferente da origem.")
    elif returning and not pairs:
        st.error("A data de volta precisa ser posterior à data de ida.")
    elif call_count > 40:
        st.error(
            f"Essa combinação exigiria {call_count} consultas. Reduza a flexibilidade ou o número de destinos "
            "para ficar no limite de 40."
        )
    else:
        results: list[dict[str, Any]] = []
        errors: list[tuple[str, str]] = []
        search_status = st.status("Preparando a busca…", expanded=True)
        progress = search_status.progress(0.0)

        for destination_index, (destination_name, destination_code) in enumerate(
            destinations_for_search.items(), start=1
        ):
            search_status.update(
                label=f"Pesquisando {destination_name} · destino {destination_index} de {len(destinations_for_search)}",
                state="running",
            )
            if returning:
                candidates: list[dict[str, Any]] = []
                failures: list[str] = []
                for departure_option, return_option in pairs:
                    item, error = cached_specific_search(
                        origin,
                        destination_code,
                        departure_option.isoformat(),
                        return_option.isoformat(),
                        stop_code,
                        layover_minutes,
                    )
                    if item:
                        candidate = dict(item)
                        candidate["_departure_date"] = departure_option.isoformat()
                        candidate["_return_date"] = return_option.isoformat()
                        candidates.append(candidate)
                    elif error:
                        failures.append(error)
                if candidates:
                    best = min(candidates, key=lambda item: item["price"])
                    results.append(
                        {
                            "destination": destination_name,
                            "code": destination_code,
                            "price": best["price"],
                            "currency": best.get("currency", "USD"),
                            "departure_date": best["_departure_date"],
                            "return_date": best["_return_date"],
                            "booking_url": best.get("booking_url", ""),
                            "fare_type": "specific",
                            "itinerary": best,
                        }
                    )
                else:
                    errors.append((destination_name, failures[0] if failures else "Nenhum voo encontrado."))
            else:
                item, error = cached_calendar_search(
                    origin,
                    destination_code,
                    departures[0].isoformat(),
                    departures[-1].isoformat(),
                    int(trip_duration),
                    stop_code,
                    layover_minutes,
                )
                if item:
                    results.append(
                        {
                            "destination": destination_name,
                            "code": destination_code,
                            "price": item["price"],
                            "currency": item.get("currency", "USD"),
                            "departure_date": item["departure_date"],
                            "return_date": item["return_date"],
                            "booking_url": item.get("booking_url", ""),
                            "fare_type": "calendar",
                            "itinerary": None,
                        }
                    )
                elif error:
                    errors.append((destination_name, error))

            progress.progress(destination_index / len(destinations_for_search))

        search_status.update(
            label=(
                f"Busca concluída · {len(results)} destino(s) com resultado"
                if results
                else "Busca concluída sem tarifas disponíveis"
            ),
            state="complete",
            expanded=False,
        )
        st.session_state["last_search"] = {
            "results": results,
            "errors": errors,
            "origin": origin,
            "stop_code": stop_code,
            "stop_label": stop_label,
            "layover_minutes": layover_minutes,
            "layover_label": layover_label,
            "signature": current_signature,
            "searched_destinations": len(destinations_for_search),
        }
        st.session_state["details"] = {}

saved = st.session_state.get("last_search")
if saved:
    results = sorted(saved["results"], key=lambda item: item["price"])
    affordable = [item for item in results if float(item["price"]) <= budget]
    result_label = "opção" if len(affordable) == 1 else "opções"
    st.markdown(
        f"""
        <div class="fh-results-head">
            <div><h2>Voos que valem sua atenção</h2>
            <p><span class="fh-count">{len(affordable)} {result_label}</span> até US$ {budget:,.0f}, ordenadas pelo menor preço.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if saved["signature"] != current_signature:
        st.info("Você alterou os critérios. Os resultados abaixo ainda são da última busca; clique em buscar para atualizar.")

    if affordable:
        for index, result in enumerate(affordable):
            render_fare_card(result, index, saved, int(budget))
    else:
        st.markdown(
            """
            <div class="fh-empty"><strong>Nenhuma tarifa ficou dentro do orçamento.</strong>
            <span>Aumente o limite, tente datas flexíveis ou compare outros destinos.</span></div>
            """,
            unsafe_allow_html=True,
        )

    if results:
        export_rows = [
            {
                "Destino": item["destination"],
                "Aeroportos": item["code"],
                "Preço USD": item["price"],
                "Ida": item["departure_date"],
                "Volta": item["return_date"],
                "Tipo": "Itinerário detalhado" if item["fare_type"] == "specific" else "Tarifa de calendário",
                "Google Flights": item.get("booking_url", ""),
            }
            for item in results
        ]
        with st.expander("Ver tabela e exportar resultados"):
            st.dataframe(export_rows, hide_index=True, use_container_width=True)
            st.download_button(
                "Baixar resultados em JSON",
                json.dumps(export_rows, ensure_ascii=False, indent=2),
                file_name="flight_hunter_results.json",
                mime="application/json",
            )

    if saved["errors"]:
        with st.expander(f"Destinos sem resultado ({len(saved['errors'])})"):
            for destination_name, error in saved["errors"]:
                st.write(f"**{destination_name}:** {error}")

st.markdown(
    """
    <footer class="fh-footer">
        <strong>Antes de reservar:</strong> preços e disponibilidade podem mudar. Confira tarifa final, bagagem,
        aeroportos e condições diretamente no Google Flights. O Flight Hunter usa dados do FLI/Google Flights
        e não vende passagens.
    </footer>
    """,
    unsafe_allow_html=True,
)
