import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 1. IMPORT MODULI ---
from engine.core import ScoreEngine, RunMetrics
from services.api import StravaService, WeatherService, AICoachService
from services.db import DatabaseService
from ui.visuals import render_benchmark_chart, render_zones_chart, render_scatter_chart, render_history_table, render_trend_chart
from ui.style import apply_custom_style

# --- 2. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="SCORE 4.0",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 3. APPLICAZIONE STILE ---
apply_custom_style()

# --- 4. CONFIGURAZIONE SERVIZI & SECRETS ---
strava_conf = st.secrets.get("strava", {})
gemini_conf = st.secrets.get("gemini", {})
supa_conf = st.secrets.get("supabase", {})

# Inizializzazione Servizi
auth_svc = StravaService(strava_conf.get("client_id", ""), strava_conf.get("client_secret", ""))
db_svc = DatabaseService(supa_conf.get("url", ""), supa_conf.get("key", ""))

# --- 5. GESTIONE STATO & AUTH ---
if "strava_token" not in st.session_state: 
    st.session_state.strava_token = None
if "data" not in st.session_state: 
    st.session_state.data = db_svc.get_history()

# CALLBACK STRAVA
if "code" in st.query_params and not st.session_state.strava_token:
    tk = auth_svc.get_token(st.query_params["code"])
    if tk: 
        st.session_state.strava_token = tk
        st.query_params.clear()
        st.rerun()

# --- 6. HEADER & NAVIGAZIONE ---
col_header, col_profile = st.columns([3, 1], gap="large")

with col_header:
    st.title("🏃‍♂️ SCORE 4.0 Lab")

with col_profile:
    if st.session_state.strava_token:
        athlete = st.session_state.strava_token.get("athlete", {})
        athlete_name = f"{athlete.get('firstname', 'Atleta')} {athlete.get('lastname', '')}"
        
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
        st.link_button("🔗 Connetti Strava", auth_svc.get_link("https://scorerun.streamlit.app/"), type="primary", use_container_width=True)

# --- 7. CONFIGURAZIONE ATLETA ---
weight, hr_max, hr_rest, ftp = 70.0, 185, 50, 250

if st.session_state.strava_token:
    athlete = st.session_state.strava_token.get("athlete", {})
    strava_weight = athlete.get('weight', 0)
    default_w = float(strava_weight) if strava_weight > 0 else 70.0
    
    with st.expander("⚙️ Profilo & Parametri Fisici", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: weight = st.number_input("Peso (kg)", value=default_w)
        with c2: hr_max = st.number_input("FC Max", value=185)
        with c3: hr_rest = st.number_input("FC Riposo", value=50)
        with c4: ftp = st.number_input("FTP (W)", value=250)

st.divider()

# --- 8. LOGICA PRINCIPALE ---

# CASO A: UTENTE NON LOGGATO
if not st.session_state.strava_token:
    st.markdown("""
    <div style="text-align: center; padding: 50px 20px;">
        <h2 style="color: #4A4A4A;">Analisi Performance Avanzata</h2>
        <p style="color: #888; font-size: 1.1rem;">
            Collega il tuo account Strava per importare le attività e calcolare il tuo SCORE.<br>
            Nessuna configurazione richiesta.
        </p>
    </div>
    """, unsafe_allow_html=True)

# CASO B: UTENTE LOGGATO
else:
    # --- 1. TOOLBAR CENTRATA & COMPATTA ---
    space_L, col_controls, space_R = st.columns([3, 2, 3])
    
    with col_controls:
        c_drop, c_btn = st.columns([2, 1], gap="small", vertical_alignment="bottom")
        
        with c_drop:
            time_options = {
                "30 Giorni": 30,
                "90 Giorni": 90,
                "12 Mesi": 365,
                "5 Anni": 365*5,
                "Storico": 365*20
            }
            selected_label = st.selectbox(
                "Periodo:", 
                options=list(time_options.keys()), 
                index=2, # Default 12 Mesi
                label_visibility="visible"
            )
            days_to_fetch = time_options[selected_label]

        with c_btn:
            start_sync = st.button("🔄 Sync", type="primary", use_container_width=True, help="Scarica o aggiorna dati")

    # --- 2. LOGICA DI DOWNLOAD ---
    if start_sync:
        eng = ScoreEngine()
        athlete_id = st.session_state.strava_token.get("athlete", {}).get("id", 0)
        token = st.session_state.strava_token["access_token"]
        
        with st.spinner(f"Sincronizzazione Strava ({selected_label})..."):
            activities_list = auth_svc.fetch_activities(token, days_back=days_to_fetch)
        
        if not activities_list:
            st.warning(f"Nessuna corsa trovata negli ultimi {days_to_fetch} giorni.")
        else:
            st.toast(f"Trovate {len(activities_list)} attività. Elaborazione...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            count_new = 0
            existing_ids = [r['id'] for r in st.session_state.data]
            
            for i, s in enumerate(activities_list):
                progress_bar.progress((i + 1) / len(activities_list))
                status_text.caption(f"Elaborazione: {s['name']}")
                
                if s['id'] in existing_ids:
                    time.sleep(0.005) 
                    continue 

                streams = auth_svc.fetch_streams(token, s['id'])
                
                if streams and 'watts' in streams and 'heartrate' in streams:
                    dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                    lat_lng = s.get('start_latlng', [])
                    t, h = WeatherService.get_weather(lat_lng[0], lat_lng[1], dt.strftime("%Y-%m-%d"), dt.hour) if lat_lng else (20.0, 50.0)
                    if not t: t, h = 20.0, 50.0

                    m = RunMetrics(s.get('average_watts', 0), s.get('average_heartrate', 0), s.get('distance', 0), s.get('moving_time', 0), s.get('total_elevation_gain', 0), weight, hr_max, hr_rest, t, h)
                    dec = eng.calculate_decoupling(streams['watts']['data'], streams['heartrate']['data'])
                    score, wcf, wr_p = eng.compute_score(m, dec)
                    rnk, _ = eng.get_rank(score)
                    
                    run_obj = {
                        "id": s['id'], "Data": dt.strftime("%Y-%m-%d"), 
                        "Dist (km)": round(m.distance_meters/1000, 2),
                        "Power": int(m.avg_power), "HR": int(m.avg_hr),
                        "Decoupling": round(dec*100, 1), "WCF": round(wcf, 2),
                        "SCORE": round(score, 2), "WR_Pct": round(wr_p, 1),
                        "Rank": rnk, "Meteo": f"{t}°C",
                        "raw_watts": streams['watts']['data'], "raw_hr": streams['heartrate']['data']
                    }
                    
                    if db_svc.save_run(run_obj, athlete_id):
                        count_new += 1
                time.sleep(0.1) 
            
            status_text.empty()
            progress_bar.empty()
            st.session_state.data = db_svc.get_history()
            
            if count_new > 0: 
                st.balloons()
                st.success(f"Archiviate {count_new} nuove attività!")
                time.sleep(1.5)
                st.rerun()
            else: 
                st.info("Tutto aggiornato.")

    # --- 3. DASHBOARD & LAB ---
    if st.session_state.data:
        st.markdown("<br>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📊 Dashboard", "🔬 Laboratorio Analisi"])
        
        # --- PREPARAZIONE & FILTRO DATI ---
        df = pd.DataFrame(st.session_state.data)
        df['Data'] = pd.to_datetime(df['Data'])
        df = df.sort_values(by='Data', ascending=False)
        
        # APPLICA IL FILTRO SELEZIONATO NEL MENU
        # Questo assicura che le medie e i kpi riflettano il periodo scelto
        if 'days_to_fetch' in locals():
            cutoff = datetime.now() - timedelta(days=days_to_fetch)
            df = df[df['Data'] > cutoff]
        
        if df.empty:
            st.warning(f"Nessuna corsa trovata nel periodo selezionato ({selected_label}). Clicca Sync per scaricarle.")
        else:
            # Calcoli Dashboard su Dati Filtrati
            current_run = df.iloc[0]
            current_score = current_run['SCORE']
            
            if len(df) > 1:
                prev_run = df.iloc[1]
                prev_score = prev_run['SCORE']
            else:
                prev_score = current_score
                
            expected_score = round(df.head(3)['SCORE'].mean(), 2)

            diff = current_score - prev_score
            if diff > 0: trend_label = "In Crescita"
            elif diff < 0: trend_label = "In Calo"
            else: trend_label = "Stabile"
            
            # Calcolo Media Periodo
            avg_period_score = round(df['SCORE'].mean(), 2)
            run_count = len(df)

            # TAB 1
            with t1:
                # Hero Section
                c_prev, c_main, c_next = st.columns([1, 1.5, 1], gap="small")
                
                with c_prev:
                    st.markdown(f"""
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; opacity: 0.7;">
                        <div style="font-size: 0.8rem; font-weight: bold; color: #888; margin-bottom: 5px;">PRECEDENTE</div>
                        <div style="width: 100px; height: 100px; border-radius: 50%; border: 4px solid #ddd; background: white; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; font-weight: 700; color: #888; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                            {prev_score}
                        </div>
                    </div>""", unsafe_allow_html=True)

                with c_main:
                    clean_rank = current_run['Rank'].split('/')[0].strip()
                    st.markdown(f"""
                    <div style="display: flex; justify-content: center;">
                        <div style="width: 170px; height: 170px; border-radius: 50%; border: 6px solid #CDFAD5; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1); z-index: 10; position: relative;">
                            <span style="color: #999; font-size: 0.75rem; font-weight: 700; letter-spacing: 1px;">SCORE ATTUALE</span>
                            <span style="color: #4A4A4A; font-size: 3.2rem; font-weight: 800; line-height: 1;">{current_score}</span>
                            <div style="background-color: #CDFAD5; color: #4A4A4A; padding: 3px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; margin-top: 5px;">{clean_rank}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                with c_next:
                     st.markdown(f"""
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; opacity: 0.7;">
                        <div style="font-size: 0.8rem; font-weight: bold; color: #6C5DD3; margin-bottom: 5px;">ATTESO</div>
                        <div style="width: 100px; height: 100px; border-radius: 50%; border: 4px dashed #6C5DD3; background: white; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; font-weight: 700; color: #6C5DD3; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                            {expected_score}
                        </div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # KPI Boxes (5 Colonne)
                k1, k2, k3, k4, k5 = st.columns(5, gap="small")
                st.markdown("""
                <style>
                div[data-testid="stMetric"] { 
                    text-align: center; 
                    align-items: center; 
                    justify-content: center; 
                    background-color: white; 
                    border-radius: 10px; 
                    padding: 10px; 
                    border: 1px solid #eee; 
                    box-shadow: 0 2px 5px rgba(0,0,0,0.02);
                    min-height: 100px;
                } 
                div[data-testid="stMetricLabel"] { justify-content: center; }
                </style>
                """, unsafe_allow_html=True)
                
                with k1: st.metric("Efficienza", f"{current_run['Decoupling']}%", "Drift")
                with k2: st.metric("Potenza", f"{current_run['Power']}w", f"{current_run['Meteo']}")
                with k3: st.metric("Benchmark", f"{current_run['WR_Pct']}%", "vs WR")
                with k4: st.metric("Media Periodo", f"{avg_period_score}", f"Su {run_count} corse")
                with k5: st.metric("Trend", trend_label, f"{diff:+.2f}")
                    
                st.markdown("<br>", unsafe_allow_html=True)

                # Lista Nascosta
                with st.expander("📂 Attività Analizzate", expanded=False):
                    render_history_table(df)

            # TAB 2
            with t2:
                st.markdown("### 🔬 Laboratorio Analisi")
                
                if len(df) > 1:
                    render_trend_chart(df.head(30))
                    st.divider()

                opts = {r['id']: f"{r['Data'].strftime('%Y-%m-%d')} - {r['Dist (km)']}km" for i, r in df.iterrows()}
                sel = st.selectbox("Seleziona Attività Specifica:", list(opts.keys()), format_func=lambda x: opts[x])
                
                run = df[df['id'] == sel].iloc[0].to_dict()
                
                col_ai, col_charts = st.columns([1, 2], gap="medium")
                
                with col_ai:
                    st.markdown("##### 🤖 Coach AI")
                    existing_feedback = run.get('ai_feedback')
                    
                    if existing_feedback:
                        st.success("✅ Analisi recuperata")
                        st.markdown(existing_feedback)
                        if st.button("🔄 Rigenera"):
                            existing_feedback = None 
                    
                    if not existing_feedback:
                        ai_key = gemini_conf.get("api_key")
                        if ai_key:
                            if st.button("✨ Genera Analisi AI", type="primary"):
                                with st.spinner("Analisi in corso..."):
                                    coach = AICoachService(ai_key)
                                    zones_calc = ScoreEngine.calculate_zones(run['raw_watts'], ftp)
                                    feedback = coach.get_feedback(run, zones_calc)
                                    st.markdown(feedback)
                                    db_svc.update_ai_feedback(run['id'], feedback)
                        else:
                            st.warning("⚠️ Manca API Key")

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.metric("Decoupling", f"{run['Decoupling']}%")
                    
                with col_charts:
                    render_scatter_chart(run['raw_watts'], run['raw_hr'])
                    st.markdown("<br>", unsafe_allow_html=True)
                    render_zones_chart(ScoreEngine.calculate_zones(run['raw_watts'], ftp))
