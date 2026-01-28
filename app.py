import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. IMPORT MODULI ---
from engine.core import ScoreEngine, RunMetrics
from services.api import StravaService, WeatherService, AICoachService
from services.db import DatabaseService
from ui.visuals import render_benchmark_chart, render_zones_chart, render_scatter_chart, render_history_table
from ui.style import apply_custom_style

# --- 2. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="SCORE 4.0",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed" # Sidebar nascosta di default
)

# --- 3. APPLICAZIONE STILE ---
apply_custom_style()

# --- 4. CONFIGURAZIONE SERVIZI & SECRETS ---
strava_conf = st.secrets.get("strava", {})
gemini_conf = st.secrets.get("gemini", {}) # La key viene letta qui
supa_conf = st.secrets.get("supabase", {})

# Inizializzazione Servizi
auth_svc = StravaService(strava_conf.get("client_id", ""), strava_conf.get("client_secret", ""))
db_svc = DatabaseService(supa_conf.get("url", ""), supa_conf.get("key", ""))

# --- 5. GESTIONE STATO & AUTH ---
if "strava_token" not in st.session_state: 
    st.session_state.strava_token = None
if "data" not in st.session_state: 
    st.session_state.data = db_svc.get_history()

# GESTIONE CALLBACK STRAVA (Ritorno dal login)
if "code" in st.query_params and not st.session_state.strava_token:
    tk = auth_svc.get_token(st.query_params["code"])
    if tk: 
        st.session_state.strava_token = tk
        st.query_params.clear() # Pulisce l'URL
        st.rerun()

# --- 6. HEADER & NAVIGAZIONE (Senza Sidebar) ---
# Usiamo le colonne per creare un Header con Titolo a Sx e Profilo a Dx
col_header, col_profile = st.columns([3, 1], gap="large")

with col_header:
    st.title("sCore")

with col_profile:
    # SEZIONE LOGIN / PROFILO IN ALTO A DESTRA
    if st.session_state.strava_token:
        # Recuperiamo dati atleta da Strava
        athlete = st.session_state.strava_token.get("athlete", {})
        athlete_name = f"{athlete.get('firstname', 'Atleta')} {athlete.get('lastname', '')}"
        
        # Box profilo minimal
        st.markdown(f"""
        <div style="text-align: right; background: white; padding: 10px; border-radius: 15px; border: 1px solid #eee;">
            <small style="color: #888;">Benvenuto,</small><br>
            <strong>{athlete_name}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Logout", key="logout_btn", use_container_width=True):
            st.session_state.strava_token = None
            st.rerun()
    elif strava_conf.get("client_id"):
        # Pulsante Login Strava Grande
        st.link_button("🔗 Connetti Strava", auth_svc.get_link("https://scorerun.streamlit.app/"), type="primary", use_container_width=True)

# --- 7. CONFIGURAZIONE ATLETA (Nascosta in Expander) ---
# Solo se loggato mostriamo le impostazioni, altrimenti nulla
weight, hr_max, hr_rest, ftp = 70.0, 185, 50, 250 # Defaults

if st.session_state.strava_token:
    athlete = st.session_state.strava_token.get("athlete", {})
    
    # Cerchiamo di prendere il peso da Strava, altrimenti default 70
    strava_weight = athlete.get('weight', 0)
    default_w = float(strava_weight) if strava_weight > 0 else 70.0
    
    with st.expander("⚙️ Profilo & Parametri Fisici", expanded=False):
        c_set1, c_set2, c_set3, c_set4 = st.columns(4)
        with c_set1:
            weight = st.number_input("Peso (kg)", value=default_w, help="Preso da Strava se disponibile")
        with c_set2:
            hr_max = st.number_input("FC Max", value=185)
        with c_set3:
            hr_rest = st.number_input("FC Riposo", value=50)
        with c_set4:
            ftp = st.number_input("FTP (W)", value=250, help="Functional Threshold Power")

# --- 8. LOGICA PRINCIPALE ---
st.divider()

# CASO A: UTENTE NON LOGGATO
if not st.session_state.strava_token:
    # Hero Section di benvenuto
    st.markdown("""
    <div style="text-align: center; padding: 50px 20px;">
        <h2 style="color: #4A4A4A;">Analisi Performance Avanzata</h2>
        <p style="color: #888; font-size: 1.1rem;">
            Collega il tuo account Strava per importare le attività e calcolare il tuo SCORE.<br>
            Nessuna configurazione richiesta.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostriamo dati demo o vuoto? Meglio vuoto pulito.
    if st.session_state.data:
        st.info("💡 Ci sono dati storici in memoria. Effettua il login per aggiornarli.")
        render_history_table(pd.DataFrame(st.session_state.data).head(3))

# CASO B: UTENTE LOGGATO
else:
    # Sezione Azioni (Download)
    col_act_1, col_act_2 = st.columns([1, 4])
    with col_act_1:
        if st.button("🚀 Sincronizza Strava", type="primary", use_container_width=True):
            with st.spinner("Analisi nuove attività in corso..."):
                eng = ScoreEngine()
                athlete_id = st.session_state.strava_token.get("athlete", {}).get("id", 0)
                
                # Fetch
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
                    
                    # Calcoli
                    dec = eng.calculate_decoupling(str_['watts']['data'], str_['heartrate']['data'])
                    score, wcf, wr_p = eng.compute_score(m, dec)
                    rnk, _ = eng.get_rank(score)
                    
                    run_obj = {
                        "id": s['id'], "Data": dt.strftime("%Y-%m-%d"), 
                        "Dist (km)": round(m.distance_meters/1000, 2),
                        "Power": int(m.avg_power), "HR": int(m.avg_hr),
                        "Decoupling": round(dec*100, 1), "WCF": round(wcf, 2),
                        "SCORE": round(score, 2), "WR_Pct": round(wr_p, 1),
                        "Rank": rnk, "Meteo": f"{t}°C",
                        "raw_watts": str_['watts']['data'], "raw_hr": str_['heartrate']['data']
                    }
                    
                    if db_svc.save_run(run_obj, athlete_id):
                        count_new += 1
                
                st.session_state.data = db_svc.get_history()
                if count_new > 0: st.toast(f"✅ Archiviate {count_new} nuove attività!")
                else: st.toast("Nessuna nuova attività trovata.")

    # DASHBOARD
    if st.session_state.data:
        st.markdown("<br>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📊 Dashboard", "🔬 Laboratorio Analisi"])
        df = pd.DataFrame(st.session_state.data)
        
        # --- TAB 1: BENTO DASHBOARD ---
        with t1:
            last = df.iloc[0]
            
            # KPI Cards
            k1, k2, k3, k4 = st.columns(4, gap="medium")
            with k1: st.metric("SCORE Index", f"{last['SCORE']}", f"{last['Rank']}")
            with k2: st.metric("Efficienza", f"{last['Decoupling']}%", "Drift Rate")
            with k3: st.metric("Potenza", f"{last['Power']}w", f"{last['Meteo']}")
            with k4: st.metric("Benchmark", f"{last['WR_Pct']}%", "vs World Rec")
                
            st.markdown("<br>", unsafe_allow_html=True)

            # Griglia Grafico + Lista
            c_main, c_side = st.columns([2.2, 1], gap="medium")
            
            with c_main:
                render_benchmark_chart(df)
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### 🗃 Archivio Attività")
                render_history_table(df)
                
            with c_side:
                st.markdown("##### 📅 Recenti")
                mini_df = df.head(4)
                for i, row in mini_df.iterrows():
                    score_color = "#FF8080" if row['SCORE'] >= 3 else "#FFCF96"
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 20px; margin-bottom: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); display: flex; justify-content: space-between; align-items: center; border: 1px solid white;">
                        <div>
                            <div style="font-weight:bold; color:#4A4A4A; font-size:0.9rem;">{row['Data']}</div>
                            <div style="font-size:0.75rem; color:#999; margin-top:3px;">{row['Dist (km)']} km • {row['Power']} W</div>
                        </div>
                        <div style="background-color: {score_color}; color: white; padding: 5px 12px; border-radius: 12px; font-weight: bold; font-size: 0.85rem;">{row['SCORE']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # --- TAB 2: LAB ---
        with t2:
            opts = {r['id']: f"{r['Data']} - {r['Dist (km)']}km" for r in st.session_state.data}
            sel = st.selectbox("Seleziona Analisi:", list(opts.keys()), format_func=lambda x: opts[x])
            run = next(r for r in st.session_state.data if r['id'] == sel)
            
            col_ai, col_charts = st.columns([1, 2], gap="medium")
            
            with col_ai:
                st.markdown("##### 🤖 Coach AI")
                ai_key = gemini_conf.get("api_key") # PRESA DAI SECRETS
                
                if ai_key:
                    if st.button("Genera Analisi", type="primary"):
                        with st.spinner("Analisi in corso..."):
                            coach = AICoachService(ai_key)
                            zones_calc = ScoreEngine.calculate_zones(run['raw_watts'], ftp)
                            st.markdown(coach.get_feedback(run, zones_calc))
                else:
                    st.warning("⚠️ Gemini API Key mancante nei secrets.")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.metric("Decoupling", f"{run['Decoupling']}%")
                
            with col_charts:
                render_scatter_chart(run['raw_watts'], run['raw_hr'])
                st.markdown("<br>", unsafe_allow_html=True)
                render_zones_chart(ScoreEngine.calculate_zones(run['raw_watts'], ftp))
    else:
        st.info("👆 Connetti Strava per iniziare.")
