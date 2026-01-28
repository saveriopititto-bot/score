import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 1. IMPORT MODULI ---
from engine.core import ScoreEngine, RunMetrics
from services.api import StravaService, WeatherService, AICoachService
from services.db import DatabaseService
from ui.visuals import (
    render_benchmark_chart,
    render_zones_chart,
    render_scatter_chart,
    render_history_table,
    render_trend_chart
)
from ui.style import apply_custom_style

# --- 2. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="SCORE 4.1",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 3. STILE ---
apply_custom_style()

# --- 4. SECRETS & SERVIZI ---
strava_conf = st.secrets.get("strava", {})
gemini_conf = st.secrets.get("gemini", {})
supa_conf = st.secrets.get("supabase", {})

auth_svc = StravaService(
    strava_conf.get("client_id", ""),
    strava_conf.get("client_secret", "")
)
db_svc = DatabaseService(
    supa_conf.get("url", ""),
    supa_conf.get("key", "")
)

# --- 5. SESSION STATE ---
if "strava_token" not in st.session_state:
    st.session_state.strava_token = None

if "data" not in st.session_state:
    st.session_state.data = db_svc.get_history()

# --- CALLBACK STRAVA ---
if "code" in st.query_params and not st.session_state.strava_token:
    tk = auth_svc.get_token(st.query_params["code"])
    if tk:
        st.session_state.strava_token = tk
        st.query_params.clear()
        st.rerun()

# --- 6. HEADER ---
col_header, col_profile = st.columns([3, 1])

with col_header:
    st.title("🏃‍♂️ SCORE 4.1 Lab")

with col_profile:
    if st.session_state.strava_token:
        athlete = st.session_state.strava_token.get("athlete", {})
        athlete_name = f"{athlete.get('firstname','Atleta')} {athlete.get('lastname','')}"
        st.markdown(
            f"""
            <div style="text-align:right;background:white;padding:10px;
            border-radius:12px;border:1px solid #eee">
            <small>Benvenuto</small><br><b>{athlete_name}</b>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Logout", use_container_width=True):
            st.session_state.strava_token = None
            st.rerun()
    elif strava_conf.get("client_id"):
        st.link_button(
            "🔗 Connetti Strava",
            auth_svc.get_link("https://scorerun.streamlit.app/"),
            type="primary",
            use_container_width=True
        )

st.divider()

# --- 7. PARAMETRI ATLETA ---
weight, hr_max, hr_rest, ftp = 70.0, 185, 50, 250
athlete_age = 40

if st.session_state.strava_token:
    athlete = st.session_state.strava_token["athlete"]
    athlete_age = athlete.get("age", 40)

    with st.expander("⚙️ Profilo & Parametri", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: weight = st.number_input("Peso (kg)", value=float(athlete.get("weight", 70)))
        with c2: hr_max = st.number_input("FC Max", value=185)
        with c3: hr_rest = st.number_input("FC Riposo", value=50)
        with c4: ftp = st.number_input("FTP", value=250)

# --- 8. MAIN ---
if not st.session_state.strava_token:
    st.markdown(
        "<h3 style='text-align:center;color:#666'>Connetti Strava per iniziare</h3>",
        unsafe_allow_html=True
    )
    st.stop()

# --- TOOLBAR ---
space_l, col_ctrl, space_r = st.columns([3, 2, 3])

with col_ctrl:
    time_options = {
        "30 Giorni": 30,
        "90 Giorni": 90,
        "12 Mesi": 365,
        "Storico": 3650
    }
    label = st.selectbox("Periodo", list(time_options.keys()), index=2)
    days_to_fetch = time_options[label]
    start_sync = st.button("🔄 Sync", type="primary", use_container_width=True)

# --- SYNC ---
if start_sync:
    eng = ScoreEngine()
    token = st.session_state.strava_token["access_token"]
    athlete_id = athlete.get("id", 0)

    acts = auth_svc.fetch_activities(token, days_back=days_to_fetch)
    existing_ids = {r["id"] for r in st.session_state.data}

    for s in acts:
        if s["id"] in existing_ids:
            continue

        streams = auth_svc.fetch_streams(token, s["id"])
        if not streams or "watts" not in streams or "heartrate" not in streams:
            continue

        dt = datetime.strptime(s["start_date_local"], "%Y-%m-%dT%H:%M:%SZ")
        latlng = s.get("start_latlng", [])

        t, h = (20.0, 50.0)
        if latlng:
            t, h = WeatherService.get_weather(
                latlng[0], latlng[1], dt.strftime("%Y-%m-%d"), dt.hour
            )

        m = RunMetrics(
            s.get("average_watts", 0),
            s.get("average_heartrate", 0),
            s.get("distance", 0),
            s.get("moving_time", 0),
            s.get("total_elevation_gain", 0),
            weight, hr_max, hr_rest, t, h
        )

        dec = eng.calculate_decoupling(
            streams["watts"]["data"],
            streams["heartrate"]["data"]
        )

        score, detail, wr_pct = eng.compute_score(m, dec)
        rank, _ = eng.get_rank(score)

        age_pct = eng.age_adjusted_percentile(score, athlete_age)

        run = {
            "id": s["id"],
            "Data": dt.strftime("%Y-%m-%d"),
            "Dist (km)": round(m.distance_meters / 1000, 2),
            "Power": int(m.avg_power),
            "HR": int(m.avg_hr),
            "Decoupling": round(dec * 100, 1),
            "SCORE": round(score, 2),
            "SCORE_DETAIL": detail,
            "WR_Pct": round(wr_pct, 1),
            "Age_Pct": age_pct,
            "Rank": rank,
            "Meteo": f"{t}°C",
            "raw_watts": streams["watts"]["data"],
            "raw_hr": streams["heartrate"]["data"]
        }

        db_svc.save_run(run, athlete_id)

    st.session_state.data = db_svc.get_history()
    st.success("Sincronizzazione completata")
    st.rerun()

# --- DASHBOARD ---
df = pd.DataFrame(st.session_state.data)
df["Data"] = pd.to_datetime(df["Data"])
df = df.sort_values("Data")

# Medie mobili
df["SCORE_MA_7"] = df["SCORE"].rolling(7, min_periods=1).mean()
df["SCORE_MA_28"] = df["SCORE"].rolling(28, min_periods=1).mean()

# Filtro periodo
cutoff = datetime.now() - timedelta(days=days_to_fetch)
df = df[df["Data"] > cutoff]

df = df.sort_values("Data", ascending=False)
current = df.iloc[0]

# Delta su MA7
prev_ma7 = df.iloc[1]["SCORE_MA_7"] if len(df) > 1 else current["SCORE_MA_7"]
delta = round(current["SCORE_MA_7"] - prev_ma7, 2)

trend = "Stabile →"
if delta > 0.5:
    trend = "In Crescita ↑"
elif delta < -0.5:
    trend = "In Calo ↓"

# --- HERO ---
c1, c2, c3 = st.columns([1, 2, 1])

with c2:
    st.markdown(
        f"""
        <div style="text-align:center;background:white;padding:25px;
        border-radius:20px;border:1px solid #eee">
        <div style="font-size:0.8rem;color:#888">SCORE ATTUALE</div>
        <div style="font-size:3.5rem;font-weight:800">{current['SCORE']}</div>
        <div>{current['Rank']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- KPI ---
k1, k2, k3, k4 = st.columns(4)

with k1: st.metric("Media Periodo", round(df["SCORE"].mean(), 2))
with k2: st.metric("Trend (MA7)", trend, f"{delta:+}")
with k3: st.metric("Percentile Età", f"{current['Age_Pct']}%")
with k4: st.metric("Decoupling", f"{current['Decoupling']}%")

# --- SPIEGA SCORE ---
with st.expander("🔍 Come nasce il tuo SCORE"):
    for k, v in current["SCORE_DETAIL"].items():
        st.progress(v / 100, text=f"{k.capitalize()}: {v}")

# --- TREND ---
render_trend_chart(df.head(90))

# --- STORICO ---
with st.expander("📂 Attività"):
    render_history_table(df)
