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

# --- 9. VISUALIZZAZIONE ---
if st.session_state.data:
    # Creiamo spaziature verticali pulite
    st.markdown("<br>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["Dashboard", "Analysis Lab"])
    df = pd.DataFrame(st.session_state.data)
    
    # --- TAB 1: BENTO DASHBOARD ---
    with t1:
        last = df.iloc[0]
        
        # RIGA 1: KPI CARDS (4 Colonne)
        k1, k2, k3, k4 = st.columns(4, gap="medium")
        
        with k1:
            st.metric("SCORE Index", f"{last['SCORE']}", f"{last['Rank']}")
        with k2:
            st.metric("Efficienza", f"{last['Decoupling']}%", "Drift Rate") # Badge Mint
        with k3:
            st.metric("Potenza", f"{last['Power']}w", f"{last['Meteo']}")
        with k4:
            st.metric("Benchmark", f"{last['WR_Pct']}%", "vs World Rec")
            
        st.markdown("<br>", unsafe_allow_html=True)

        # RIGA 2: GRIGLIA ASIMMETRICA (Grafico + Lista Recenti)
        c_main, c_side = st.columns([2.2, 1], gap="medium")
        
        with c_main:
            # Card Bianca Grande (Grafico)
            render_benchmark_chart(df)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 🗃 Archivio Attività")
            render_history_table(df)
            
        with c_side:
            st.markdown("##### 📅 Recenti")
            
            # Creiamo una lista di "Mini Card" stile widget per le ultime 4 corse
            mini_df = df.head(4)
            for i, row in mini_df.iterrows():
                # Colore SCORE dinamico (Salmon se alto, Peach se medio)
                score_color = "#FF8080" if row['SCORE'] >= 3 else "#FFCF96"
                
                # HTML INJECTION PER STILE WIDGET
                st.markdown(f"""
                <div style="
                    background-color: white;
                    padding: 15px;
                    border-radius: 20px;
                    margin-bottom: 12px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.03);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border: 1px solid white;
                    transition: transform 0.2s;
                " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                    <div>
                        <div style="font-weight:bold; color:#4A4A4A; font-size:0.9rem;">{row['Data']}</div>
                        <div style="font-size:0.75rem; color:#999; margin-top:3px;">
                            {row['Dist (km)']} km • {row['Power']} W
                        </div>
                    </div>
                    <div style="
                        background-color: {score_color};
                        color: white;
                        padding: 5px 12px;
                        border-radius: 12px;
                        font-weight: bold;
                        font-size: 0.85rem;
                    ">
                        {row['SCORE']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- TAB 2: LAB (Manteniamo struttura a colonne) ---
    with t2:
        # ... (Logica selezione corsa esistente) ...
        # (Usa lo stesso codice di prima per il Tab 2, si adatterà automaticamente al CSS)
        opts = {r['id']: f"{r['Data']} - {r['Dist (km)']}km" for r in st.session_state.data}
        sel = st.selectbox("Seleziona Analisi:", list(opts.keys()), format_func=lambda x: opts[x])
        run = next(r for r in st.session_state.data if r['id'] == sel)
        
        col_ai, col_charts = st.columns([1, 2], gap="medium")
        
        with col_ai:
            st.markdown("##### 🤖 AI Coach")
            if ai_key:
                if st.button("Genera Analisi", type="primary"):
                    with st.spinner("Elaborazione..."):
                        coach = AICoachService(ai_key)
                        zones_calc = ScoreEngine.calculate_zones(run['raw_watts'], ftp)
                        st.markdown(coach.get_feedback(run, zones_calc))
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.metric("Decoupling", f"{run['Decoupling']}%")
            
        with col_charts:
            render_scatter_chart(run['raw_watts'], run['raw_hr'])
            st.markdown("<br>", unsafe_allow_html=True)
            render_zones_chart(ScoreEngine.calculate_zones(run['raw_watts'], ftp))
            
else:
    # Stato Iniziale Vuoto
    st.info("👋 Nessun dato in memoria. Connettiti a Strava dalla sidebar per iniziare.")
