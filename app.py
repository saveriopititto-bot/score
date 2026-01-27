import streamlit as st
import pandas as pd
from datetime import datetime

# Import Moduli Locali
from engine.core import ScoreEngine, RunMetrics
from services.api import StravaService, WeatherService, AICoachService
from ui.visuals import render_benchmark_chart, render_zones_chart, render_scatter_chart

st.set_page_config(page_title="SCORE 4.0 Lab", page_icon="🧬", layout="wide")

# --- INIT SESSION ---
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "data" not in st.session_state: st.session_state.data = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    c_id = st.text_input("Client ID", value=st.secrets.get("strava", {}).get("client_id", ""))
    c_sec = st.text_input("Client Secret", value=st.secrets.get("strava", {}).get("client_secret", ""), type="password")
    ai_key = st.text_input("Gemini API Key", value=st.secrets.get("gemini", {}).get("api_key", ""), type="password")
    
    auth = StravaService(c_id, c_sec)
    
    if st.session_state.strava_token:
        st.success("✅ Connesso")
        if st.button("Logout"): st.session_state.strava_token = None; st.rerun()
    elif c_id and c_sec:
        st.link_button("🔗 Login Strava", auth.get_link("https://scorerun.streamlit.app/"), type="primary")

    st.divider()
    weight = st.number_input("Peso (kg)", 70.0)
    hr_max = st.number_input("FC Max", 185)
    hr_rest = st.number_input("FC Riposo", 50)
    ftp = st.number_input("FTP (W)", 250)

# --- AUTH CALLBACK ---
if "code" in st.query_params and not st.session_state.strava_token:
    tk = auth.get_token(st.query_params["code"])
    if tk: st.session_state.strava_token = tk; st.query_params.clear(); st.rerun()

# --- MAIN LOGIC ---
st.title("🏃‍♂️ SCORE 4.0 Lab (Modular)")

if st.session_state.strava_token:
    if st.button("🚀 Analizza", type="primary"):
        with st.spinner("Elaborazione..."):
            eng = ScoreEngine()
            raw = auth.fetch_activities(st.session_state.strava_token["access_token"])
            processed = []
            
            for d in raw:
                s, str_ = d['summary'], d['streams']
                dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                lat_lng = s.get('start_latlng', [])
                
                # Meteo
                t, h = WeatherService.get_weather(lat_lng[0], lat_lng[1], dt.strftime("%Y-%m-%d"), dt.hour) if lat_lng else (20.0, 50.0)
                if not t: t, h = 20.0, 50.0

                # Metrics
                m = RunMetrics(s.get('average_watts', 0), s.get('average_heartrate', 0), s.get('distance', 0), s.get('moving_time', 0), s.get('total_elevation_gain', 0), weight, hr_max, hr_rest, t, h)
                
                # Calcoli
                dec = eng.calculate_decoupling(str_['watts']['data'], str_['heartrate']['data'])
                score, wcf, wr_p = eng.compute_score(m, dec)
                rnk, _ = eng.get_rank(score)
                
                processed.append({
                    "id": s['id'], "Data": dt.strftime("%Y-%m-%d"), 
                    "Dist (km)": round(m.distance_meters/1000, 2),
                    "Power": int(m.avg_power), "HR": int(m.avg_hr),
                    "Decoupling": round(dec*100, 1), "WCF": round(wcf, 2),
                    "SCORE": round(score, 2), "WR_Pct": round(wr_p, 1),
                    "Rank": rnk, "Meteo": f"{t}°C",
                    "raw_watts": str_['watts']['data'], "raw_hr": str_['heartrate']['data']
                })
            st.session_state.data = processed
            st.rerun()

    if st.session_state.data:
        t1, t2 = st.tabs(["📊 Dashboard", "🔬 Deep Dive"])
        df = pd.DataFrame(st.session_state.data)
        
        with t1:
            st.dataframe(df.drop(columns=['id', 'raw_watts', 'raw_hr']), use_container_width=True, hide_index=True)
            render_benchmark_chart(df)
            
        with t2:
            opts = {r['id']: f"{r['Data']} - {r['Dist (km)']}km" for r in st.session_state.data}
            sel = st.selectbox("Seleziona:", list(opts.keys()), format_func=lambda x: opts[x])
            run = next(r for r in st.session_state.data if r['id'] == sel)
            
            c1, c2 = st.columns([1, 2])
            with c1:
                if st.button("Coach AI"):
                    coach = AICoachService(ai_key)
                    st.markdown(coach.get_feedback(run))
                st.metric("Decoupling", f"{run['Decoupling']}%")
                
            with c2:
                render_scatter_chart(run['raw_watts'], run['raw_hr'])
                st.subheader("Zone")
                render_zones_chart(ScoreEngine.calculate_zones(run['raw_watts'], ftp))
else:
    st.info("Connettiti a Strava.")
