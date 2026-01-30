import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 1. CONFIG & VALIDATION ---
from config import Config

missing_secrets = Config.check_secrets()
if missing_secrets:
    st.error(f"❌ Segreti mancanti: {', '.join(missing_secrets)}")
    st.stop()

# --- 2. IMPORT MODULI ---
from engine.core import ScoreEngine, RunMetrics
from services.api import StravaService, WeatherService, AICoachService
from services.db import DatabaseService
from ui.style import apply_custom_style
from ui.legal import render_legal_section
from ui.visuals import render_history_table, render_trend_chart, render_scatter_chart, render_zones_chart
from ui.feedback import render_feedback_form

# --- 3. PAGE SETUP ---
st.set_page_config(page_title=Config.APP_TITLE, page_icon=Config.APP_ICON, layout="wide", initial_sidebar_state="collapsed")
apply_custom_style()

# --- 4. SERVIZI ---
strava_creds = Config.get_strava_creds()
supa_creds = Config.get_supabase_creds()
gemini_key = Config.get_gemini_key()

auth_svc = StravaService(strava_creds["client_id"], strava_creds["client_secret"])
db_svc = DatabaseService(supa_creds["url"], supa_creds["key"])

# --- 5. STATE ---
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "data" not in st.session_state: st.session_state.data = [] # Inizializza vuoto, caricherà dopo
if "demo_mode" not in st.session_state: st.session_state.demo_mode = False

# Callback Strava
if "code" in st.query_params and not st.session_state.strava_token:
    tk = auth_svc.get_token(st.query_params["code"])
    if tk: 
        st.session_state.strava_token = tk
        st.query_params.clear()
        st.rerun()

# =========================================================
# LOGICA
# =========================================================

# --- A. NON LOGGATO ---
if not st.session_state.strava_token:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, c_center, _ = st.columns([1, 2, 1])
    with c_center:
        st.markdown("<h1 style='text-align: center; color: #FFCF96;'>sCore Lab 4.1</h1>", unsafe_allow_html=True)
        st.info("Benvenuto nella nuova versione con Engine 4.1 (NumPy Powered)")
        
        redirect_url = "https://scorerun.streamlit.app/" 
        link_strava = auth_svc.get_link(redirect_url)
        st.link_button("🚀 Connetti Strava", link_strava, type="primary", use_container_width=True)
    render_legal_section()

# --- B. LOGGATO ---
else:
    # Caricamento dati iniziale (se vuoto)
    if not st.session_state.data:
        st.session_state.data = db_svc.get_history()

    # HEADER
    c1, c2 = st.columns([3, 1])
    with c1: st.title("sCore Lab")
    with c2:
        ath = st.session_state.strava_token.get("athlete", {})
        st.caption(f"Atleta: {ath.get('firstname', '')}")
        if st.button("Logout"):
            st.session_state.strava_token = None
            st.rerun()

    # --- CONFIGURAZIONE ATLETA ---
    weight, hr_max, hr_rest, ftp, age = Config.DEFAULT_WEIGHT, Config.DEFAULT_HR_MAX, Config.DEFAULT_HR_REST, Config.DEFAULT_FTP, Config.DEFAULT_AGE
    zones_data = None
    saved_profile = None

    if not st.session_state.demo_mode:
        token = st.session_state.strava_token["access_token"]
        athlete_id = ath.get("id")
        saved_profile = db_svc.get_athlete_profile(athlete_id)
        
        if saved_profile:
            weight = saved_profile.get('weight', weight)
            hr_max = saved_profile.get('hr_max', hr_max)
            hr_rest = saved_profile.get('hr_rest', hr_rest)
            ftp = saved_profile.get('ftp', ftp)
            age = saved_profile.get('age', age)
        else:
            # Logica fallback Strava (semplificata per brevità, quella di prima era ok)
            s_weight = ath.get('weight', 0)
            if s_weight: weight = float(s_weight)
            if "strava_zones" not in st.session_state: st.session_state.strava_zones = auth_svc.fetch_zones(token)
            zones_data = st.session_state.strava_zones

    with st.expander("⚙️ Profilo Atleta", expanded=False):
        with st.form("athlete_settings"):
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: new_weight = st.number_input("Peso", value=float(weight))
            with c2: new_hr_max = st.number_input("FC Max", value=int(hr_max))
            with c3: new_hr_rest = st.number_input("FC Riposo", value=int(hr_rest))
            with c4: new_ftp = st.number_input("FTP", value=int(ftp))
            with c5: new_age = st.number_input("Età", value=int(age))
            
            if st.form_submit_button("💾 Salva"):
                payload = {"id": ath.get("id"), "firstname": ath.get("firstname"), "lastname": ath.get("lastname"), "weight": new_weight, "hr_max": new_hr_max, "hr_rest": new_hr_rest, "ftp": new_ftp, "age": new_age, "updated_at": datetime.now().isoformat()}
                if db_svc.save_athlete_profile(payload)[0]:
                    st.success("Salvato!")
                    time.sleep(1)
                    st.rerun()

    st.divider()

    # --- SYNC BUTTON ---
    c_filt, c_btn = st.columns([3, 1])
    with c_filt:
        days = st.selectbox("Analizza ultimi:", [30, 90, 365], index=1)
    with c_btn:
        start_sync = st.button("🔄 AGGIORNA DASHBOARD", type="primary", use_container_width=True)

    # --- ENGINE LOOP ---
    if start_sync:
        eng = ScoreEngine()
        token = st.session_state.strava_token["access_token"]
        athlete_id = ath.get("id")

        with st.spinner("Analisi in corso (Motore 4.1)..."):
            activities = auth_svc.fetch_activities(token, days_back=days)
            
            if activities:
                # Recuperiamo gli ID già presenti per non rifarli tutti, 
                # MA se la tabella è stata svuotata (Step 1), existing_ids sarà vuoto -> Ricarica tutto. Bene!
                existing_ids = [r['id'] for r in st.session_state.data]
                
                bar = st.progress(0)
                new_count = 0
                
                for i, s in enumerate(activities):
                    bar.progress((i + 1) / len(activities))
                    
                    # Logica di update: Se abbiamo cambiato la matematica, vogliamo FORZARE l'aggiornamento
                    # Quindi commentiamo il check "if exists continue" per ora, o svuotiamo il DB prima.
                    # Dato che allo Step 1 abbiamo fatto DROP TABLE, existing_ids è vuoto.
                    
                    streams = auth_svc.fetch_streams(token, s['id'])
                    if streams and 'watts' in streams and 'heartrate' in streams:
                        dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                        # Meteo mock o reale
                        t, h = 20.0, 50.0 
                        
                        m = RunMetrics(s.get('average_watts', 0), s.get('average_heartrate', 0), s.get('distance', 0), s.get('moving_time', 0), s.get('total_elevation_gain', 0), weight, hr_max, hr_rest, t, h)
                        dec = eng.calculate_decoupling(streams['watts']['data'], streams['heartrate']['data'])
                        
                        # CHIAMATA AL NUOVO MOTORE 4.1
                        score, details, wcf, wr_pct = eng.compute_score(m, dec)
                        rnk, _ = eng.get_rank(score)
                        
                        run_obj = {
                            "id": s['id'], "Data": dt.strftime("%Y-%m-%d"), 
                            "Dist (km)": round(m.distance_meters/1000, 2),
                            "Power": int(m.avg_power), "HR": int(m.avg_hr),
                            "Decoupling": round(dec*100, 1), 
                            "SCORE": round(score, 2), 
                            "WCF": round(wcf, 2),       # <--- Ecco i dati nuovi
                            "WR_Pct": round(wr_pct, 1), # <--- Ecco i dati nuovi
                            "Rank": rnk, "Meteo": f"{t}°C",
                            "SCORE_DETAIL": details,
                            "raw_watts": streams['watts']['data'], "raw_hr": streams['heartrate']['data']
                        }
                        
                        if db_svc.save_run(run_obj, athlete_id):
                            new_count += 1
                    time.sleep(0.1)
                
                if new_count > 0:
                    st.success(f"Aggiornate {new_count} attività!")
                    st.session_state.data = db_svc.get_history() # Ricarica dal DB fresco
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Nessuna attività trovata su Strava.")

    # --- VISUALS ---
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        
        # Selettore temporale DataFrame
        df['Data'] = pd.to_datetime(df['Data'])
        df = df.sort_values("Data", ascending=False)
        
        # KPI DI OGGI
        if not df.empty:
            last = df.iloc[0]
            
            # DASHBOARD
            st.markdown("### 📊 Dashboard Pro")
            
            k1, k2, k3, k4 = st.columns(4)
            with k1: st.metric("SCORE", last['SCORE'], last['Rank'])
            with k2: st.metric("WCF (Meteo)", last.get('WCF', 'N/A'))
            with k3: st.metric("WR %", f"{last.get('WR_Pct', 0)}%")
            with k4: st.metric("Drift", f"{last['Decoupling']}%")
            
            with st.expander("🔍 Dettagli Score"):
                st.json(last.get('SCORE_DETAIL', {}))

            st.markdown("### 📈 Storico")
            render_history_table(df)
            
            st.markdown("### 🔬 Trend")
            render_trend_chart(df)
            
    else:
        st.info("👋 Ciao! Non hai ancora dati. Clicca su 'AGGIORNA DASHBOARD' per importare le corse.")

    # FEEDBACK & FOOTER
    st.markdown("<br>", unsafe_allow_html=True)
    render_feedback_form(db_svc, ath.get("id"), ath.get("firstname"))
    render_legal_section()
