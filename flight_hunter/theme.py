"""Shared visual system for the Streamlit interface."""

APP_CSS = r"""
<style>
:root {
    --fh-ink: #10233f;
    --fh-muted: #607086;
    --fh-border: #dfe6ee;
    --fh-soft: #f4f7fa;
    --fh-paper: #ffffff;
    --fh-navy: #0a2240;
    --fh-navy-2: #123760;
    --fh-teal: #19a89d;
    --fh-teal-dark: #087c74;
    --fh-gold: #f2b84b;
}

html { scroll-behavior: smooth; }
body, .stApp { color: var(--fh-ink); }
.stApp { background: #f5f7fa; }
[data-testid="stHeader"] { display: none; }
[data-testid="stAppViewContainer"] > .main .block-container,
[data-testid="stMainBlockContainer"] {
    max-width: 1180px !important;
    padding: 1.4rem 2rem 4rem !important;
}

.fh-hero {
    position: relative;
    overflow: hidden;
    margin: .25rem 0 1.35rem;
    padding: 2.25rem 2.5rem 2rem;
    border-radius: 24px;
    background: var(--fh-navy);
    color: #fff;
    box-shadow: 0 18px 50px rgba(10, 34, 64, .18);
}
.fh-hero::after {
    content: "";
    position: absolute;
    width: 280px;
    height: 280px;
    right: -95px;
    top: -125px;
    border: 1px solid rgba(255,255,255,.16);
    border-radius: 50%;
    box-shadow: 0 0 0 34px rgba(255,255,255,.035), 0 0 0 68px rgba(255,255,255,.025);
}
.fh-brand {
    display: flex;
    align-items: center;
    gap: .75rem;
    margin-bottom: 2rem;
    font-weight: 750;
    letter-spacing: -.02em;
}
.fh-mark {
    display: grid;
    place-items: center;
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 10px;
    background: var(--fh-teal);
    color: #fff;
    font-size: 1.05rem;
    transform: rotate(-8deg);
}
.fh-mark span { transform: rotate(8deg); }
.fh-eyebrow {
    margin: 0 0 .7rem;
    color: #88ded6;
    font-size: .74rem;
    font-weight: 750;
    letter-spacing: .14em;
    text-transform: uppercase;
}
.fh-hero h1 {
    max-width: 780px;
    margin: 0;
    color: #fff;
    font-size: clamp(2.05rem, 5vw, 3.45rem);
    line-height: 1.03;
    letter-spacing: -.045em;
}
.fh-hero h1 span { color: #8ce1d9; }
.fh-hero-copy {
    max-width: 670px;
    margin: 1rem 0 1.6rem;
    color: #cad7e6;
    font-size: 1.03rem;
    line-height: 1.65;
}
.fh-trust-row { display: flex; flex-wrap: wrap; gap: .55rem; }
.fh-trust-chip {
    padding: .42rem .7rem;
    border: 1px solid rgba(255,255,255,.17);
    border-radius: 999px;
    color: #e9f1f8;
    background: rgba(255,255,255,.06);
    font-size: .78rem;
}

.fh-intro {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 1rem;
    margin: 2rem 0 .8rem;
}
.fh-intro h2 { margin: 0; color: var(--fh-ink); font-size: 1.55rem; letter-spacing: -.025em; }
.fh-intro p { margin: .35rem 0 0; color: var(--fh-muted); }
.fh-step {
    display: flex;
    align-items: flex-start;
    gap: .85rem;
    margin: .1rem 0 1.1rem;
}
.fh-step-number {
    flex: 0 0 auto;
    display: grid;
    place-items: center;
    width: 2rem;
    height: 2rem;
    border-radius: 9px;
    color: #08776f;
    background: #e3f7f4;
    font-size: .78rem;
    font-weight: 800;
}
.fh-step h3 { margin: -.05rem 0 .2rem; color: var(--fh-ink); font-size: 1.03rem; }
.fh-step p { margin: 0; color: var(--fh-muted); font-size: .86rem; }

div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid var(--fh-border);
    border-radius: 18px;
    background: var(--fh-paper);
    box-shadow: 0 8px 24px rgba(16, 35, 63, .05);
}
div[data-baseweb="select"] > div,
[data-testid="stDateInput"] > div > div,
[data-testid="stNumberInput"] > div > div {
    border-color: #cfd8e3;
    border-radius: 11px;
    min-height: 2.8rem;
}
div[data-baseweb="select"] > div:focus-within,
[data-testid="stDateInput"] > div > div:focus-within,
[data-testid="stNumberInput"] > div > div:focus-within {
    border-color: var(--fh-teal);
    box-shadow: 0 0 0 3px rgba(25,168,157,.13);
}
[data-testid="stWidgetLabel"] p { color: #263a54; font-size: .88rem; font-weight: 650; }
[data-testid="stCheckbox"] p, [data-testid="stRadio"] p { font-weight: 500; }

.stButton > button[kind="primary"] {
    min-height: 3.25rem;
    border: 0;
    border-radius: 12px;
    background: var(--fh-teal-dark);
    box-shadow: 0 8px 22px rgba(8, 124, 116, .2);
    font-size: 1rem;
    font-weight: 750;
}
.stButton > button[kind="primary"]:hover { background: #066c65; }
.stButton > button:focus-visible, .stLinkButton > a:focus-visible {
    outline: 3px solid rgba(25,168,157,.3);
    outline-offset: 2px;
}
.stButton > button:not([kind="primary"]), .stLinkButton > a {
    border-radius: 10px;
    font-weight: 650;
}
.stLinkButton > a {
    border-color: var(--fh-teal-dark);
    color: var(--fh-teal-dark);
}
.fh-search-note { margin: .55rem 0 0; color: var(--fh-muted); text-align: center; font-size: .8rem; }

.fh-results-head {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 1rem;
    margin: 2.7rem 0 1rem;
}
.fh-results-head h2 { margin: 0; color: var(--fh-ink); font-size: 1.65rem; letter-spacing: -.03em; }
.fh-results-head p { margin: .35rem 0 0; color: var(--fh-muted); }
.fh-count { color: var(--fh-teal-dark); font-weight: 800; }
.fh-fare-head {
    display: flex;
    justify-content: space-between;
    gap: 1.25rem;
    align-items: flex-start;
    padding: .2rem 0 .35rem;
}
.fh-badge {
    display: inline-flex;
    align-items: center;
    gap: .32rem;
    margin-bottom: .62rem;
    padding: .28rem .55rem;
    border-radius: 999px;
    background: #edf2f7;
    color: #51647a;
    font-size: .68rem;
    font-weight: 800;
    letter-spacing: .05em;
    text-transform: uppercase;
}
.fh-badge.confirmed { background: #e1f6f2; color: #08776f; }
.fh-fare-title { margin: 0; color: var(--fh-ink); font-size: 1.35rem; letter-spacing: -.02em; }
.fh-fare-title span { color: #7a8a9e; font-size: .9rem; font-weight: 650; }
.fh-route { margin: .35rem 0 0; color: var(--fh-muted); font-size: .86rem; }
.fh-price { min-width: 155px; text-align: right; }
.fh-price span { display: block; color: var(--fh-muted); font-size: .7rem; text-transform: uppercase; letter-spacing: .07em; }
.fh-price strong { display: block; color: var(--fh-ink); font-size: 1.65rem; letter-spacing: -.035em; }
.fh-price small { color: var(--fh-muted); font-size: .72rem; }
.fh-facts {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin: .85rem 0 .25rem;
    border: 1px solid #e6ebf1;
    border-radius: 12px;
    background: #f8fafc;
}
.fh-fact { padding: .72rem .85rem; border-right: 1px solid #e6ebf1; }
.fh-fact:last-child { border-right: 0; }
.fh-fact span { display: block; color: var(--fh-muted); font-size: .67rem; text-transform: uppercase; letter-spacing: .06em; }
.fh-fact strong { display: block; margin-top: .16rem; color: #263a54; font-size: .83rem; }
.fh-calendar-note {
    margin: .8rem 0 .25rem;
    padding: .75rem .85rem;
    border-left: 3px solid var(--fh-gold);
    border-radius: 0 9px 9px 0;
    background: #fff9ec;
    color: #645432;
    font-size: .81rem;
}
.fh-confirm-note {
    margin: .8rem 0 .25rem;
    color: var(--fh-muted);
    font-size: .79rem;
}

.fh-itinerary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; margin: .8rem 0; }
.fh-segment { padding: .95rem; border: 1px solid #e1e7ee; border-radius: 13px; background: #fbfcfd; }
.fh-segment-top { display: flex; justify-content: space-between; gap: .7rem; align-items: center; margin-bottom: .7rem; }
.fh-segment-top strong { color: var(--fh-ink); font-size: .86rem; }
.fh-segment-top span { color: var(--fh-muted); font-size: .72rem; }
.fh-time-row { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: .55rem; }
.fh-time { color: var(--fh-ink); font-size: 1.12rem; font-weight: 800; }
.fh-flight-line { height: 1px; background: #bcc8d5; position: relative; }
.fh-flight-line::before, .fh-flight-line::after { content: ""; position: absolute; top: -3px; width: 7px; height: 7px; border-radius: 50%; background: var(--fh-teal); }
.fh-flight-line::before { left: 0; } .fh-flight-line::after { right: 0; }
.fh-airports { display: flex; justify-content: space-between; margin-top: .18rem; color: #43566e; font-size: .74rem; font-weight: 750; }
.fh-segment-meta { margin-top: .65rem; color: var(--fh-muted); font-size: .73rem; line-height: 1.5; }
.fh-leg-list { margin: .7rem 0 0; padding-top: .65rem; border-top: 1px solid #e7ebf0; }
.fh-leg { margin: .35rem 0; color: #43566e; font-size: .72rem; }
.fh-layover { margin: .38rem 0; padding: .38rem .5rem; border-radius: 7px; background: #edf6f5; color: #226c67; font-size: .7rem; }

.fh-empty {
    padding: 2rem;
    border: 1px dashed #cbd5e0;
    border-radius: 16px;
    background: #fff;
    text-align: center;
}
.fh-empty strong { display: block; color: var(--fh-ink); font-size: 1.05rem; }
.fh-empty span { display: block; margin-top: .4rem; color: var(--fh-muted); }
.fh-footer { margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid var(--fh-border); color: var(--fh-muted); font-size: .76rem; line-height: 1.6; }

@media (max-width: 760px) {
    [data-testid="stAppViewContainer"] > .main .block-container,
    [data-testid="stMainBlockContainer"] { padding: .75rem .8rem 3rem !important; }
    .fh-hero { padding: 1.45rem 1.2rem 1.35rem; border-radius: 18px; }
    .fh-brand { margin-bottom: 1.4rem; }
    .fh-hero-copy { font-size: .93rem; }
    .fh-trust-chip { font-size: .7rem; }
    .fh-intro, .fh-results-head, .fh-fare-head { align-items: flex-start; flex-direction: column; }
    .fh-price { min-width: 0; text-align: left; }
    .fh-facts { grid-template-columns: 1fr; }
    .fh-fact { border-right: 0; border-bottom: 1px solid #e6ebf1; }
    .fh-fact:last-child { border-bottom: 0; }
    .fh-itinerary-grid { grid-template-columns: 1fr; }
    [data-testid="column"] { min-width: 100% !important; }
}
</style>
"""
