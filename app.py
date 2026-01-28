import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. IMPORT MODULI (Standard & Locali) ---
from engine.core import ScoreEngine, RunMetrics
from services.api import StravaService, WeatherService, AICoachService
from services.db import DatabaseService
from ui.visuals import render_benchmark_chart, render_zones_chart, render_scatter_chart, render_history_table
from ui.style import apply_custom_style  # Importa lo stile Pastel

# --- 2. CONFIGURAZIONE PAGINA (Prima istruzione 'st.') ---
st.set_page_config(
    page_title="SCORE 4.0 Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. APPLICAZIONE STILE (Subito dopo la config) ---
apply_custom_style()

# --- 4. CONFIGURAZIONE SERVIZI & SECRETS ---
strava_conf = st.secrets.get("strava", {})
gemini_conf = st.secrets.get("gemini", {})
supa_conf = st.secrets.get("supabase", {})

# Inizializzazione Servizi
auth_svc = StravaService(strava_conf.get("client_id", ""), strava_conf.get("client_secret", ""))
db_svc = DatabaseService(supa_conf.get("url", ""), supa_conf.get("key", ""))

# --- 5. INIZIALIZZAZIONE STATO SESSIONE ---
if "strava_token" not in st.session_state: 
    st.session_state.strava_token = None

# Caricamento storico DB (se non presente)
if "data" not in st.session_state: 
    st.session_state.data = db_svc.get_history()

# --- 6. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    ai_key = st.text_input("Gemini API Key", value=gemini_conf.get("api_key", ""), type="password")
    
    if st.session_state.strava_token:
        st.success("✅ Strava Connesso")
        if st.button("Logout"): st.session_state.strava_token = None; st.rerun()
    elif strava_conf.get("client_id"):
        st.link_button("🔗 Login Strava", auth_svc.get_link("https://scorerun.streamlit.app/"), type="primary")

    st.divider()
    # Parametri Atleta
    st.subheader("👤 Profilo Atleta")
    weight = st.number_input("Peso (kg)", 70.0)
    hr_max = st.number_input("FC Max", 185)
    hr_rest = st.number_input("FC Riposo", 50)
    ftp = st.number_input("FTP (W)", 250, help="Functional Threshold Power per Zone Coggan")

# --- 7. AUTH CALLBACK (Gestione ritorno da Strava) ---
if "code" in st.query_params and not st.session_state.strava_token:
    tk = auth_svc.get_token(st.query_params["code"])
    if tk: 
        st.session_state.strava_token = tk
        st.query_params.clear()
        st.rerun()

# --- 8. MAIN LOGIC (Titolo e Analisi) ---
st.title("🏃‍♂️ SCORE 4.0 Lab")

# Sezione Download (Solo se connessi)
if st.session_state.strava_token:
    if st.button("🚀 Scarica Nuove da Strava", type="primary"):
        with st.spinner("Analisi e Salvataggio DB in corso..."):
            eng = ScoreEngine()
            athlete_id = st.session_state.strava_token.get("athlete", {}).get("id", 0)
            
            # Scarica da Strava
            raw = auth_svc.fetch_activities(st.session_state.strava_token["access_token"])
            
            count_new = 0
            for d in raw:
                s, str_ = d['summary'], d['streams']
                dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                lat_lng = s.get('start_latlng', [])
                
                # Meteo
                t, h = WeatherService.get_weather(lat_lng[0], lat_lng[1], dt.strftime("%Y-%m-%d"), dt.hour) if lat_lng else (20.0, 50.0)
                if not t: t, h = 20.0, 50.0

                # Metrics
                m = RunMetrics(s.get('average_watts', 0), s.get('average_heartrate', 0), s.get('distance', 0), s.get('moving_time', 0), s.get('total_elevation_gain', 0), weight, hr_max, hr_rest, t, h)
                
                # Calcoli Motore
                dec = eng.calculate_decoupling(str_['watts']['data'], str_['heartrate']['data'])
                score, wcf, wr_p = eng.compute_score(m, dec)
                rnk, _ = eng.get_rank(score)
                
                # Oggetto Dati
                run_obj = {
                    "id": s['id'], "Data": dt.strftime("%Y-%m-%d"), 
                    "Dist (km)": round(m.distance_meters/1000, 2),
                    "Power": int(m.avg_power), "HR": int(m.avg_hr),
                    "Decoupling": round(dec*100, 1), "WCF": round(wcf, 2),
                    "SCORE": round(score, 2), "WR_Pct": round(wr_p, 1),
                    "Rank": rnk, "Meteo": f"{t}°C",
                    "raw_watts": str_['watts']['data'], "raw_hr": str_['heartrate']['data']
                }
                
                # SALVATAGGIO SU SUPABASE
                if db_svc.save_run(run_obj, athlete_id):
                    count_new += 1
            
            # Ricarica dal DB
            st.session_state.data = db_svc.get_history()
            if count_new > 0:
                st.success(f"Analizzate e archiviate {count_new} nuove attività!")
            else:
                st.info("Nessuna nuova attività da salvare (già presenti nel DB).")

# --- 9. VISUALIZZAZIONE (Funziona anche Offline) ---
if st.session_state.data:
    t1, t2 = st.tabs(["📊 Dashboard Storica", "🔬 Lab Analisi"])
    df = pd.DataFrame(st.session_state.data)
    
    # TAB 1: OVERVIEW
    with t1:
        # KPI Rapidi Ultima Corsa
        last = df.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ultimo SCORE", f"{last['SCORE']}", delta=last['Rank'])
        c2.metric("Decoupling", f"{last['Decoupling']}%", delta_color="inverse")
        c3.metric("Meteo", last['Meteo'])
        c4.metric("Potenza", f"{last['Power']} W")
        
        st.divider()
        st.caption(f"Archivio Cloud: {len(df)} attività.")
        
        # Nuova Tabella "Styled"
        render_history_table(df)
        
        st.divider()
        render_benchmark_chart(df)
        
    # TAB 2: DEEP DIVE
    with t2:
        opts = {r['id']: f"{r['Data']} - {r['Dist (km)']}km ({r['Rank']})" for r in st.session_state.data}
        sel = st.selectbox("Seleziona Attività:", list(opts.keys()), format_func=lambda x: opts[x])
        run = next(r for r in st.session_state.data if r['id'] == sel)
        
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.subheader("🤖 Coach AI")
            if ai_key:
                if st.button("Analizza Sessione", type="secondary"):
                    with st.spinner("Il Coach sta studiando i dati..."):
                        coach = AICoachService(ai_key)
                        zones_calc = ScoreEngine.calculate_zones(run['raw_watts'], ftp)
                        feedback = coach.get_feedback(run, zones_calc)
                        st.markdown(feedback)
            else:
                st.warning("Inserisci Gemini API Key nella sidebar.")
            
            st.divider()
            st.metric("Disaccoppiamento", f"{run['Decoupling']}%", help="Drift cardiaco (>5% indica affaticamento)")
            st.metric("WR Benchmark", f"{run['WR_Pct']}%", help="% Velocità rispetto al Record del Mondo")
            
        with col_right:
            render_scatter_chart(run['raw_watts'], run['raw_hr'])
            st.subheader(f"🚦 Zone Potenza (FTP: {ftp}W)")
            render_zones_chart(ScoreEngine.calculate_zones(run['raw_watts'], ftp))

else:
    # Stato Iniziale Vuoto
    st.info("👋 Nessun dato in memoria. Connettiti a Strava dalla sidebar per iniziare.")
