import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 1. CONFIG & VALIDATION ---
from config import Config
import logging

# Setup Logging
logger = Config.setup_logging()
logger.info("Starting sCore App...")

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
st.set_page_config(
    page_title=Config.APP_TITLE, 
    page_icon=Config.APP_ICON, 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

apply_custom_style()

# --- 4. SERVIZI ---
strava_creds = Config.get_strava_creds()
supa_creds = Config.get_supabase_creds()
gemini_key = Config.get_gemini_key()

auth_svc = StravaService(strava_creds["client_id"], strava_creds["client_secret"])
db_svc = DatabaseService(supa_creds["url"], supa_creds["key"])

# --- 5. STATE ---
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "data" not in st.session_state: st.session_state.data = db_svc.get_history()
if "demo_mode" not in st.session_state: st.session_state.demo_mode = False

# Callback Strava
if "code" in st.query_params and not st.session_state.strava_token:
    tk = auth_svc.get_token(st.query_params["code"])
    if tk: 
        st.session_state.strava_token = tk
        st.query_params.clear()
        st.rerun()

# =========================================================
# LOGICA PRINCIPALE
# =========================================================

# --- A. LANDING PAGE (Non Loggato) ---
if not st.session_state.strava_token:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, c_center, _ = st.columns([1, 2, 1])
    with c_center:
        try: st.image("sCore.png", use_container_width=True)
        except: st.markdown("<h1 style='text-align: center; color: #FFCF96;'>sCore Lab</h1>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; margin-top: -10px; margin-bottom: 30px;">
            <h3 style="color: #6C5DD3; font-weight: 800; letter-spacing: -0.5px;">Corri. Analizza. Evolvi.</h3>
            <p style="color: #636E72; font-size: 1.1rem; line-height: 1.6;">
                Nuovo Engine 4.1: Analisi NumPy Powered.<br>
                Scopri il tuo vero potenziale.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # URL APP
        redirect_url = "https://scorerun.streamlit.app/" 
        link_strava = auth_svc.get_link(redirect_url)
        
        c1, c2 = st.columns([1, 1], gap="small")
        with c1: st.link_button("🚀 Connetti Strava", link_strava, type="primary", use_container_width=True)
        with c2: 
            if st.button("👀 Demo Mode", use_container_width=True):
                st.session_state.demo_mode = True
                st.session_state.strava_token = {"access_token": "DEMO", "athlete": {"id": 123, "firstname": "Demo", "lastname": "User"}}
                st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    render_legal_section()

# --- B. DASHBOARD (Loggato) ---
else:
    # HEADER
    col_header, col_profile = st.columns([3, 1], gap="large")
    with col_header:
        try: st.image("sCore.png", width=220) 
        except: st.title("sCore Lab 4.1")
        if st.session_state.get("demo_mode"): st.caption("🔴 DEMO MODE")

    with col_profile:
        ath = st.session_state.strava_token.get("athlete", {})
        athlete_name = f"{ath.get('firstname', 'Atleta')} {ath.get('lastname', '')}"
        
        st.markdown(f"""
        <div style="text-align: right; background: white; padding: 8px 15px; border-radius: 12px; border: 1px solid #eee;">
            <small style="color: #888;">Profilo Attivo</small><br>
            <strong>{athlete_name}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Esci / Logout", key="logout_btn", use_container_width=True):
            st.session_state.strava_token = None
            st.session_state.demo_mode = False
            if "strava_zones" in st.session_state: del st.session_state.strava_zones
            st.rerun()

    # --- CONFIGURAZIONE ATLETA (Smart Sync) ---
    weight, hr_max, hr_rest, ftp, age, sex = Config.DEFAULT_WEIGHT, Config.DEFAULT_HR_MAX, Config.DEFAULT_HR_REST, Config.DEFAULT_FTP, Config.DEFAULT_AGE, "M"
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
            sex = saved_profile.get('sex', sex)
        else:
            s_weight = ath.get('weight', 0)
            if s_weight: weight = float(s_weight)
            s_ftp = ath.get('ftp', 0) 
            if s_ftp: ftp = int(s_ftp)
            
            # Strava returns 'M', 'F' or None usually
            s_sex = ath.get('sex')
            if s_sex in ['M', 'F']: sex = s_sex 
            
            birthdate = ath.get('birthdate')
            if birthdate:
                try:
                    b_year = int(str(birthdate).split("-")[0])
                    curr_year = datetime.now().year
                    calc_age = curr_year - b_year
                    if 10 < calc_age < 100: age = calc_age
                except: pass

            if "strava_zones" not in st.session_state:
                st.session_state.strava_zones = auth_svc.fetch_zones(token)
            zones_data = st.session_state.strava_zones
            
            if zones_data:
                hr_zones = zones_data.get("heart_rate", {}).get("zones", [])
                if hr_zones:
                    extracted_max = hr_zones[-1].get("max")
                    if extracted_max and extracted_max > 0: hr_max = int(extracted_max)
                    else: 
                        if age > 0: hr_max = int(208 - (0.7 * age))
                
                if ftp == Config.DEFAULT_FTP: 
                    pwr_zones = zones_data.get("power", {}).get("zones", [])
                    if len(pwr_zones) > 1:
                        z2_max = pwr_zones[1].get("max") 
                        if z2_max and z2_max > 0: ftp = int(z2_max / 0.75)

    with st.expander("⚙️ Profilo Atleta & Parametri Fisici", expanded=False):
        with st.form("athlete_settings"):
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1: new_weight = st.number_input("Peso (kg)", value=float(weight), step=0.5)
            with c2: new_hr_max = st.number_input("FC Max", value=int(hr_max))
            with c3: new_hr_rest = st.number_input("FC Riposo", value=int(hr_rest))
            with c4: new_ftp = st.number_input("FTP (W)", value=int(ftp))
            with c5: new_age = st.number_input("Età", value=int(age))
            with c6: new_sex = st.selectbox("Sesso", ["M", "F"], index=0 if sex == "M" else 1)
            
            if st.form_submit_button("💾 Salva Profilo"):
                if not st.session_state.demo_mode:
                    payload = {
                        "id": int(ath.get("id")),
                        "firstname": str(ath.get("firstname", "")),
                        "lastname": str(ath.get("lastname", "")),
                        "weight": float(new_weight),
                        "hr_max": int(new_hr_max),
                        "hr_rest": int(new_hr_rest),
                        "ftp": int(new_ftp),
                        "age": int(new_age),
                        "sex": str(new_sex),
                        "updated_at": datetime.now().isoformat()
                    }
                    success, msg = db_svc.save_athlete_profile(payload)
                    if success:
                        st.success("✅ Profilo salvato!")
                        weight, hr_max, hr_rest, ftp, age, sex = new_weight, new_hr_max, new_hr_rest, new_ftp, new_age, new_sex
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Errore DB: {msg}")

        if zones_data and not saved_profile:
            st.caption(f"ℹ️ Dati stimati (FTP ~{ftp}W, Età {age}). Clicca Salva per confermare.")
        elif saved_profile:
            st.caption("✅ Profilo caricato dal database.")

    st.divider()

    # --- SYNC TOOLBAR ---
    space_L, col_controls, space_R = st.columns([3, 2, 3])
    with col_controls:
        c_drop, c_btn = st.columns([2, 1], gap="small", vertical_alignment="bottom")
        with c_drop:
            time_options = {"30 Giorni": 30, "90 Giorni": 90, "12 Mesi": 365, "Storico": 3650}
            selected_label = st.selectbox("Periodo Analisi:", list(time_options.keys()), index=2)
            days_to_fetch = time_options[selected_label]
        with c_btn:
            start_sync = st.button("🔄 AGGIORNA", type="primary", use_container_width=True, disabled=st.session_state.demo_mode)

    # --- ENGINE (Sync Logic) ---
    if start_sync and not st.session_state.demo_mode:
        eng = ScoreEngine()
        token = st.session_state.strava_token["access_token"]
        athlete_id = ath.get("id")

        with st.spinner(f"Analisi attività Strava con Engine 4.1..."):
            activities_list = auth_svc.fetch_activities(token, days_back=days_to_fetch)
            
            if activities_list:
                existing_ids = [r['id'] for r in st.session_state.data]
                count_new = 0
                bar = st.progress(0)
                
                for i, s in enumerate(activities_list):
                    bar.progress((i + 1) / len(activities_list))
                    
                    if s['id'] in existing_ids: continue 

                    streams = auth_svc.fetch_streams(token, s['id'])
                    if streams and 'watts' in streams and 'heartrate' in streams:
                        dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                        t, h = 20.0, 50.0 
                        if s.get('start_latlng'):
                             t, h = WeatherService.get_weather(s['start_latlng'][0], s['start_latlng'][1], dt.strftime("%Y-%m-%d"), dt.hour)

                        m = RunMetrics(s.get('average_watts', 0), s.get('average_heartrate', 0), s.get('distance', 0), s.get('moving_time', 0), s.get('total_elevation_gain', 0), weight, hr_max, hr_rest, t, h, age, sex)
                        dec = eng.calculate_decoupling(streams['watts']['data'], streams['heartrate']['data'])
                        
                        score, details, wcf, wr_pct = eng.compute_score(m, dec)
                        rnk, _ = eng.get_rank(score)
                        
                        run_obj = {
                            "id": s['id'], "Data": dt.strftime("%Y-%m-%d"), 
                            "Dist (km)": round(m.distance_meters/1000, 2),
                            "Power": int(m.avg_power), "HR": int(m.avg_hr),
                            "Decoupling": round(dec*100, 1), 
                            "SCORE": round(score, 2), 
                            "WCF": round(wcf, 2), 
                            "WR_Pct": round(wr_pct, 1),
                            "Rank": rnk, "Meteo": f"{t}°C",
                            "SCORE_DETAIL": details,
                            "raw_watts": streams['watts']['data'], "raw_hr": streams['heartrate']['data']
                        }
                        if db_svc.save_run(run_obj, athlete_id): count_new += 1
                    time.sleep(0.1)
                
                if count_new > 0:
                    st.success(f"Archiviate {count_new} nuove attività!")
                    st.session_state.data = db_svc.get_history()
                    time.sleep(1)
                    st.rerun()
                elif len(activities_list) > 0 and count_new == 0:
                     st.info("Database già aggiornato.")
            else:
                st.warning("Nessuna corsa trovata.")

    # --- VISUALIZZAZIONE DASHBOARD (FIX TIMEZONE QUI) ---
    if st.session_state.data:
        st.markdown("<br>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📊 Dashboard Pro", "🔬 Laboratorio Analisi"])
        
        df = pd.DataFrame(st.session_state.data)
        
        # --- FIX IMPORTANTE PER DATETIME ---
        # 1. Convertiamo in datetime, gestendo errori
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        
        # 2. Rimuoviamo il fuso orario (timezone naive) per poterlo confrontare con datetime.now()
        if pd.api.types.is_datetime64_any_dtype(df['Data']):
             if df['Data'].dt.tz is not None:
                 df['Data'] = df['Data'].dt.tz_localize(None)

        df = df.sort_values("Data", ascending=True)
        df["SCORE_MA_7"] = df["SCORE"].rolling(7, min_periods=1).mean()
        df["SCORE_MA_28"] = df["SCORE"].rolling(28, min_periods=1).mean()
        df = df.sort_values("Data", ascending=False)
        
        # Filtro Data (Ora Funziona Sicuro)
        if 'days_to_fetch' in locals():
            cutoff = datetime.now() - timedelta(days=days_to_fetch)
            df = df[df['Data'] > cutoff]
        
        if df.empty:
            st.warning("Nessuna corsa nel periodo selezionato.")
        else:
            cur_run = df.iloc[0]
            cur_score = cur_run['SCORE']
            cur_ma7 = cur_run['SCORE_MA_7']
            
            if len(df) > 1:
                prev_ma7 = df.iloc[1]['SCORE_MA_7']
                delta_val = cur_ma7 - prev_ma7
            else:
                prev_ma7 = cur_ma7
                delta_val = 0
            
            if delta_val > 0.005: trend_lbl, trend_col = "In Crescita ↗", "normal"
            elif delta_val < -0.005: trend_lbl, trend_col = "In Calo ↘", "inverse"
            else: trend_lbl, trend_col = "Stabile →", "off"

            eng = ScoreEngine()
            age_pct = eng.age_adjusted_percentile(cur_score, age)

            # === TAB 1: DASHBOARD ===
            with t1:
                # INJECT CUSTOM CSS FOR ANIMATIONS
                st.markdown("""
                <style>
                    /* Base Circle Style */
                    .stat-circle {
                        transition: all 0.3s ease;
                    }
                    .stat-circle:hover {
                        transform: scale(1.05);
                        box-shadow: 0 15px 35px rgba(0,0,0,0.15) !important;
                    }
                    
                    /* SVG Animation for Central Circle */
                    .score-circle-svg circle.progress {
                        fill: none;
                        stroke: #CDFAD5;
                        stroke-width: 6;
                        stroke-dasharray: 0, 1000;
                        transition: stroke-dasharray 1s ease-out;
                    }
                    .score-circle-container:hover circle.progress {
                        stroke-dasharray: 800, 1000; /* Approximate circumference */
                        stroke: #6C5DD3; /* Color change on hover */
                    }
                </style>
                """, unsafe_allow_html=True)

                # Layout: Atteso (Text) | Score Oggi (Big Circle) | Trend/Ieri (Circle)
                # Aumentiamo lo spazio centrale per il cerchio più grande
                c_exp, c_today, c_trend = st.columns([1, 2, 1], gap="small", vertical_alignment="center")
                
                with c_exp:
                    exp_score = round(cur_run['SCORE_MA_28'], 2)
                    st.markdown(f"""
                    <div style="display: flex; justify-content: center;">
                        <div class="stat-circle" style="width: 140px; height: 140px; border-radius: 50%; border: 4px solid #FFCF96; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 5px 20px rgba(0,0,0,0.05);">
                            <span style="color: #999; font-size: 0.65rem; font-weight: 700;">ATTESO</span>
                            <span style="color: #FF8080; font-size: 2.2rem; font-weight: 800; line-height: 1;">{exp_score}</span>
                            <div style="background:#FFCF9640; color:#FF8080; padding:2px 10px; border-radius:15px; font-size:0.6rem; font-weight:700; margin-top:3px;">BASELINE</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                
                with c_today:
                    # Central Circle: +50% bigger (apx 220px vs 140px)
                    # Using SVG to allow "border filling" animation
                    clean_rank = cur_run['Rank'].split('/')[0].strip()
                    clean_rank_key = clean_rank.split(' ')[0].upper() # Estrae "ELITE", "PRO", etc.
                    
                    # Colore Dinamico
                    rank_color = Config.RANK_COLORS.get(clean_rank_key, "#CDFAD5") # Fallback Green
                    
                    st.markdown(f"""
                    <div class="score-circle-container" style="display: flex; justify-content: center; cursor: pointer;">
                        <div style="position: relative; width: 230px; height: 230px;">
                            <svg class="score-circle-svg" width="230" height="230" style="position: absolute; top:0; left:0; transform: rotate(-90deg);">
                                <circle cx="115" cy="115" r="110" stroke="#eee" stroke-width="6" fill="white" />
                                <circle class="progress" cx="115" cy="115" r="110" style="stroke: {rank_color} !important;" />
                            </svg>
                            <div style="position: absolute; top:0; left:0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 10;">
                                <span style="color: #999; font-size: 0.9rem; font-weight: 700; letter-spacing: 1px;">OGGI</span>
                                <span style="color: #2D3436; font-size: 5rem; font-weight: 800; line-height: 0.9;">{cur_score}</span>
                                <div style="background:{rank_color}25; color:{rank_color}; border: 1px solid {rank_color}; padding:4px 16px; border-radius:20px; font-size:0.8rem; font-weight: 700; margin-top: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">{clean_rank}</div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                with c_trend:
                    dec_val = cur_run.get('Decoupling', 0.0)
                    dec_color = "#10B981" # Green
                    if dec_val > 5.0: dec_color = "#EF4444" # Red
                    elif dec_val > 3.0: dec_color = "#F59E0B" # Amber

                    st.markdown(f"""
                    <div style="display: flex; justify-content: center;">
                        <div class="stat-circle" style="width: 140px; height: 140px; border-radius: 50%; border: 4px solid #F3F4F6; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 5px 20px rgba(0,0,0,0.05);">
                            <span style="color: #999; font-size: 0.65rem; font-weight: 700;">EFFICIENCY</span>
                            <span style="color: {dec_color}; font-size: 2.2rem; font-weight: 800; line-height: 1;">{dec_val}%</span>
                            <div style="background:{dec_color}22; color:{dec_color}; padding:2px 10px; border-radius:15px; font-size:0.6rem; font-weight:700; margin-top:3px;">DRIFT</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                
                details = cur_run.get("SCORE_DETAIL") or {}
                
                k1, k2, k3, k4, k5, k6 = st.columns(6)

                with k1: st.metric("Efficienza", f"{cur_run['Decoupling']}%", "Drift")
                with k2: st.metric("Potenza", f"{cur_run['Power']}w", f"{cur_run['Meteo']}")
                with k3: st.metric("Target", f"{details.get('Target', 'N/A')}", "Tempo Rif.")
                with k4: st.metric("WCF Meteo", f"{cur_run.get('WCF', 1.0)}", "Factor")
                with k5: st.metric("Trend (7gg)", trend_lbl, f"{delta_val:+.3f}", delta_color=trend_col)
                with k6: st.metric("Percentile", f"{cur_run.get('WR_Pct', 0)}%", "Reale")

                st.markdown("<br>", unsafe_allow_html=True)
                
                with st.expander("🔍 Perché questo punteggio? (Breakdown)", expanded=True):
                    details = cur_run.get("SCORE_DETAIL")
                    if not details or not isinstance(details, dict):
                         m_tmp = RunMetrics(cur_run['Power'], cur_run['HR'], cur_run['Dist (km)']*1000, 0, 0, weight, hr_max, hr_rest, 20, 50)
                         _, details, _, _ = eng.compute_score(m_tmp, cur_run['Decoupling']/100)
                    
                    d1, d2, d3, d4 = st.columns(4)
                    with d1: st.metric("🚀 Potenza", f"+{details.get('Potenza', 0)}")
                    with d2: st.metric("🔋 Volume", f"+{details.get('Volume', 0)}")
                    with d3: st.metric("💓 Intensità", f"+{details.get('Intensità', 0)}")
                    with d4: st.metric("📉 Efficienza", f"{details.get('Malus Efficienza', 0)}")

                with st.expander("📂 Archivio Attività", expanded=False):
                    render_history_table(df)

            # === TAB 2: LABORATORIO ===
            with t2:
                st.markdown("### 🔬 Laboratorio Analisi")
                if len(df) > 1:
                    render_trend_chart(df.head(60))
                    st.divider()

                opts = {r['id']: f"{r['Data'].strftime('%Y-%m-%d')} - {r['Dist (km)']}km" for i, r in df.iterrows()}
                sel = st.selectbox("Analizza nel dettaglio:", list(opts.keys()), format_func=lambda x: opts[x])
                run = df[df['id'] == sel].iloc[0].to_dict()
                
                c_ai, c_ch = st.columns([1, 2], gap="medium")
                with c_ai:
                    st.markdown("##### 🤖 Coach AI")
                    existing_feedback = run.get('ai_feedback')
                    if existing_feedback:
                        st.success("Analisi recuperata")
                        st.markdown(existing_feedback)
                        if st.button("🔄 Rigenera"): pass 
                    else:
                        if gemini_key:
                            if st.button("✨ Genera Analisi AI", type="primary"):
                                with st.spinner("Il Coach sta studiando i tuoi dati..."):
                                    coach = AICoachService(gemini_key)
                                    zones_calc = ScoreEngine().calculate_zones(run.get('raw_watts', []), ftp)
                                    feedback = coach.get_feedback(run, zones_calc)
                                    st.markdown(feedback)
                                    if not st.session_state.demo_mode:
                                        db_svc.update_ai_feedback(run['id'], feedback)
                        else:
                            st.info("AI Key non configurata.")
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.metric("Disaccoppiamento (Drift)", f"{run['Decoupling']}%")

                with c_ch:
                    render_scatter_chart(run.get('raw_watts', []), run.get('raw_hr', []))
                    st.markdown("<br>", unsafe_allow_html=True)
                    zones_c = ScoreEngine().calculate_zones(run.get('raw_watts', []), ftp)
                    render_zones_chart(zones_c)
            
            # FOOTER
            st.markdown("<br>", unsafe_allow_html=True)
            u_id = ath.get("id")
            u_name = f"{ath.get('firstname', '')} {ath.get('lastname', '')}"
            render_feedback_form(db_svc, u_id, u_name)
            
            st.markdown("<br>", unsafe_allow_html=True)
            render_legal_section()
