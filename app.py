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
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. HERO SECTION (Logo 20% più grande, No Slogan, Strava sotto Logo)
    _, c_center, _ = st.columns([1, 2, 1])
    with c_center:
        # Contenitore centratura
        col_logo_L, col_logo_C, col_logo_R = st.columns([1, 1.5, 1])
        with col_logo_C:
             try: st.image("sCore.png", use_container_width=True) 
             except: st.markdown("<h1 style='text-align: center; color: #FFCF96;'>sCore Lab</h1>", unsafe_allow_html=True)
             
             # Bottone Strava sotto il LOGO (stessa dimensione visiva tramite colonne)
             redirect_url = "https://scorerun.streamlit.app/" 
             link_strava = auth_svc.get_link(redirect_url)
             st.link_button("Connetti Strava", link_strava, type="primary", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True) 

    # 2. IL MANIFESTO

    col_a, col_b, col_c = st.columns(3, gap="large")

    with col_a:
        st.markdown("""
        <div style="background-color: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 5px solid #FFCF96; height: 100%;">
            <h4 style="color: #444; text-transform: uppercase; letter-spacing: 1px;">CORRI</h4>
            <p style="font-size: 0.9rem; color: #555;">
                Non tutte le corse sono uguali.<br>
                SCORE non guarda solo velocità o distanza, ma <strong>come hai gestito lo sforzo</strong> nel tuo contesto attuale.
            </p>
            <p style="font-size: 0.9rem; font-weight: bold;">
                Un numero solo,<br>molte informazioni utili.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div style="background-color: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 5px solid #FF8080; height: 100%;">
            <h4 style="color: #444; text-transform: uppercase; letter-spacing: 1px;">ANALIZZA</h4>
            <p style="font-size: 0.9rem; color: #555;">
                Non è una gara, è un feedback. Nessun giudizio, solo un obiettivo: <strong>correre meglio la prossima volta</strong>.
            </p>
            <p style="font-size: 0.9rem;">
                Un punteggio alto = corsa controllata e sostenibile.<br>
                Un punteggio basso? 👉 <em>Solo un segnale, non un errore.</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_c:
        st.markdown("""
        <div style="background-color: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 5px solid #CDFAD5; height: 100%;">
            <h4 style="color: #444; text-transform: uppercase; letter-spacing: 1px;">EVOLVI</h4>
            <p style="font-size: 0.9rem; color: #555;">
                Il vero progresso non è spingere sempre, ma capire <strong>quando</strong> farlo.
                Usa SCORE per riconoscere i giorni buoni e quelli no.
            </p>
            <p style="font-size: 0.9rem; font-weight: bold;">
                Allenarsi bene non significa fare di più,<br>ma fare meglio.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # 3. FOOTER
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # PRO FOOTER
    render_legal_section()

# --- B. DASHBOARD (Loggato) ---
else:
    # 1. HEADER (Solo Logo e Logout)
    col_header, col_logout = st.columns([3, 1], gap="large")
    with col_header:
        try: st.image("sCore.png", width=220) 
        except: st.title("sCore Lab 4.1")
        if st.session_state.get("demo_mode"): st.caption("🔴 DEMO MODE")

    with col_logout:
        if st.button("Esci / Logout", key="logout_btn", use_container_width=True):
            st.session_state.strava_token = None
            st.session_state.demo_mode = False
            if "strava_zones" in st.session_state: del st.session_state.strava_zones
            st.rerun()

    # --- 3. TOP SECTION: CONTROLLI & PROFILO (2 COLONNE) ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_controls, col_athlete = st.columns([1, 1], gap="large")
    
    with col_controls:
        c_sync_drop, c_sync_btn = st.columns([2, 1], gap="small", vertical_alignment="bottom")
        with c_sync_drop:
            time_options = {"30 Giorni": 30, "90 Giorni": 90, "12 Mesi": 365, "Storico": 3650}
            selected_label = st.selectbox("Periodo Analisi:", list(time_options.keys()), index=2)
            days_to_fetch = time_options[selected_label]
        with c_sync_btn:
            start_sync = st.button("🔄 AGGIORNA", type="primary", use_container_width=True, disabled=st.session_state.demo_mode)

    with col_athlete:
        st.markdown(f"**Benvenuto, {athlete_name}**")
        st.caption(f"ID Atleta Strava: {ath.get('id', 'N/A')}")
        
        with st.expander("⚙️ Modifica profilo atleta", expanded=False):
            st.markdown("""<div style="background:#fafafa; padding:20px; border-radius:16px; border:1px solid #eee;">""", unsafe_allow_html=True)
            with st.form("athlete_settings"):
                c1, c2, c3 = st.columns(3, gap="medium")
                with c1:
                    new_weight = st.number_input("Peso (kg)", value=float(weight), step=0.5)
                    new_age = st.number_input("Età", value=int(age))
                with c2:
                    new_hr_max = st.number_input("FC Max", value=int(hr_max))
                    new_hr_rest = st.number_input("FC Riposo", value=int(hr_rest))
                with c3:
                    new_ftp = st.number_input("FTP (W)", value=int(ftp))
                    new_sex = st.selectbox("Sesso", ["M", "F"], index=0 if sex == "M" else 1)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("💾 Salva profilo"):
                    if not st.session_state.demo_mode:
                        payload = {"id": int(ath.get("id")), "firstname": str(ath.get("firstname", "")), "lastname": str(ath.get("lastname", "")), "weight": float(new_weight), "hr_max": int(new_hr_max), "hr_rest": int(new_hr_rest), "ftp": int(new_ftp), "age": int(new_age), "sex": str(new_sex), "updated_at": datetime.now().isoformat()}
                        success, msg = db_svc.save_athlete_profile(payload)
                        if success:
                            st.success("✅ Profilo salvato!"); time.sleep(1); st.rerun()
                        else: st.error(f"❌ Errore DB: {msg}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        if saved_profile: st.caption("✅ Profilo caricato dal database.")
        elif zones_data: st.caption(f"ℹ️ Dati stimati (FTP ~{ftp}W, Età {age}). Clicca Salva per confermare.")

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
                            "id": s['id'], "Data": dt.strftime("%Y-%m-%d"), "Dist (km)": round(m.distance_meters/1000, 2),
                            "Power": int(m.avg_power), "HR": int(m.avg_hr), "Decoupling": round(dec*100, 1), 
                            "SCORE": round(score, 2), "WCF": round(wcf, 2), "WR_Pct": round(wr_pct, 1),
                            "Rank": rnk, "Meteo": f"{t}°C", "SCORE_DETAIL": details,
                            "raw_watts": streams['watts']['data'], "raw_hr": streams['heartrate']['data']
                        }
                        if db_svc.save_run(run_obj, athlete_id): count_new += 1
                    time.sleep(0.1)
                
                if count_new > 0:
                    st.success(f"Archiviate {count_new} nuove attività!")
                    st.session_state.data = db_svc.get_history()
                    time.sleep(1); st.rerun()
                elif len(activities_list) > 0 and count_new == 0:
                     st.info("Database già aggiornato.")
            else:
                st.warning("Nessuna corsa trovata.")

    # --- VISUALIZZAZIONE DASHBOARD ---
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        if pd.api.types.is_datetime64_any_dtype(df['Data']) and df['Data'].dt.tz is not None:
             df['Data'] = df['Data'].dt.tz_localize(None)

        df = df.sort_values("Data", ascending=True)
        df["SCORE_MA_7"] = df["SCORE"].rolling(7, min_periods=1).mean()
        df["SCORE_MA_28"] = df["SCORE"].rolling(28, min_periods=1).mean()
        df = df.sort_values("Data", ascending=False)
        
        if 'days_to_fetch' in locals():
            cutoff = datetime.now() - timedelta(days=days_to_fetch)
            df = df[df['Data'] > cutoff]
        
        if df.empty:
            st.warning("Nessuna corsa nel periodo selezionato.")
        else:
            cur_run = df.iloc[0]
            cur_score, cur_ma7 = cur_run['SCORE'], cur_run['SCORE_MA_7']
            delta_val = (cur_ma7 - df.iloc[1]['SCORE_MA_7']) if len(df) > 1 else 0
            
            score_color = "#FFCF96" # Statico
            if delta_val > 0.005: score_color = "#CDFAD5" 
            elif delta_val < -0.005: score_color = "#FF8080" 

            wr_pct_val = cur_run.get('WR_Pct', 0.0)
            eng = ScoreEngine()

            st.divider()

            # --- MIDDLE SECTION: METRICHE PRINCIPALI ---
            st.markdown("""
            <style>
                .stat-circle { transition: all 0.3s ease; }
                .stat-circle:hover { transform: scale(1.05); box-shadow: 0 15px 35px rgba(0,0,0,0.15) !important; }
                .score-circle-svg circle.progress { fill: none; stroke: #CDFAD5; stroke-width: 6; stroke-dasharray: 0, 1000; transition: stroke-dasharray 1s ease-out; }
                .score-circle-container:hover circle.progress { stroke-dasharray: 800, 1000; stroke: #6C5DD3; }
                @media (max-width: 768px) {
                    .stat-circle { width: 110px !important; height: 110px !important; }
                    .score-circle-container { transform: scale(0.75); transform-origin: center top; margin-bottom: -50px; }
                }
            </style>
            """, unsafe_allow_html=True)

            c_pct, c_score, c_drift = st.columns([1, 2, 1], gap="small", vertical_alignment="center")
            
            with c_pct:
                pct_color = "#FF8080"
                if wr_pct_val > 75: pct_color = "#CDFAD5"
                elif wr_pct_val > 50: pct_color = "#F6FDC3"
                elif wr_pct_val > 25: pct_color = "#FFCF96"

                st.markdown(f"""
                <div style="display: flex; justify-content: center;">
                    <div class="stat-circle" style="width: 155px; height: 155px; border-radius: 50%; border: 5px solid {pct_color}; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 5px 20px rgba(0,0,0,0.05);">
                        <span style="color: #999; font-size: 0.70rem; font-weight: 700;">PERCENTILE</span>
                        <span style="color: {pct_color}; font-size: 2.5rem; font-weight: 800; line-height: 1;">{wr_pct_val}%</span>
                        <div style="background:{pct_color}22; color: #555; border: 1px solid {pct_color}; padding:2px 12px; border-radius:15px; font-size:0.65rem; font-weight:700; margin-top:5px;">RANKING</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            
            with c_score:
                clean_rank = cur_run['Rank'].split('/')[0].strip()
                st.markdown(f"""
                <div class="score-circle-container" style="display: flex; justify-content: center; cursor: pointer;">
                    <div style="position: relative; width: 230px; height: 230px;">
                        <svg class="score-circle-svg" width="230" height="230" style="position: absolute; top:0; left:0; transform: rotate(-90deg);">
                            <circle cx="115" cy="115" r="110" stroke="#eee" stroke-width="6" fill="white" />
                            <circle class="progress" cx="115" cy="115" r="110" style="stroke: {score_color} !important;" />
                        </svg>
                        <div style="position: absolute; top:0; left:0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 10;">
                            <span style="color: #999; font-size: 0.9rem; font-weight: 700; letter-spacing: 1px;">SCORE</span>
                            <span style="color: #2D3436; font-size: 5rem; font-weight: 800; line-height: 0.9;">{cur_score}</span>
                            <div style="background:{score_color}25; color:#555; border: 1px solid {score_color}; padding:4px 16px; border-radius:20px; font-size:0.8rem; font-weight: 700; margin-top: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">{clean_rank}</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

            with c_drift:
                dec_val = cur_run.get('Decoupling', 0.0)
                dec_color = "#10B981"; drift_cat = "ECCELLENTE"
                if dec_val > 10.0: dec_color = "#991B1B"; drift_cat = "CRITICO"
                elif dec_val > 5.0: dec_color = "#EF4444"; drift_cat = "ATTENZIONE"
                elif dec_val > 3.0: dec_color = "#F59E0B"; drift_cat = "BUONO"

                st.markdown(f"""
                <div style="display: flex; justify-content: center;">
                    <div class="stat-circle" style="width: 155px; height: 155px; border-radius: 50%; border: 5px solid {dec_color}; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 5px 20px rgba(0,0,0,0.05);">
                        <span style="color: #999; font-size: 0.70rem; font-weight: 700;">DRIFT</span>
                        <span style="color: {dec_color}; font-size: 2.5rem; font-weight: 800; line-height: 1;">{dec_val}%</span>
                        <div style="background:{dec_color}22; color: #555; border: 1px solid {dec_color}; padding:2px 12px; border-radius:15px; font-size:0.65rem; font-weight:700; margin-top:5px;">{drift_cat}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

            st.divider()

            # --- BOTTOM SECTION: GRAFICI (3 COLONNE) ---
            st.markdown("### 🔬 Analisi & Trend")
            col_g1, col_g2, col_g3 = st.columns(3, gap="medium")
            
            with col_g1:
                st.markdown("##### 📈 Trend SCORE")
                if len(df) > 1:
                    render_trend_chart(df.head(60))
            
            with col_g2:
                st.markdown("##### 📍 Power vs HR")
                opts = {r['id']: f"{r['Data'].strftime('%Y-%m-%d')} - {r['Dist (km)']}km" for i, r in df.iterrows()}
                sel = st.selectbox("Seleziona attività:", list(opts.keys()), format_func=lambda x: opts[x], key="sel_scatter")
                run_scatter = df[df['id'] == sel].iloc[0].to_dict()
                render_scatter_chart(run_scatter.get('raw_watts', []), run_scatter.get('raw_hr', []))
                st.caption(f"Drift: {run_scatter['Decoupling']}%")

            with col_g3:
                st.markdown("##### 📊 Zone Intensità")
                run_zones = df[df['id'] == sel].iloc[0].to_dict() # Usa la stessa attività
                zones_c = ScoreEngine().calculate_zones(run_zones.get('raw_watts', []), ftp)
                render_zones_chart(zones_c)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # --- SEZIONE DETTAGLI & ARCHIVIO ---
            c_break, c_arch = st.columns([1, 1], gap="large")
            with c_break:
                with st.expander("🔬 Perché questo punteggio? (Breakdown)", expanded=False):
                    details = cur_run.get("SCORE_DETAIL")
                    if not details or not isinstance(details, dict):
                         m_tmp = RunMetrics(cur_run['Power'], cur_run['HR'], cur_run['Dist (km)']*1000, 0, 0, weight, hr_max, hr_rest, 20, 50)
                         _, details, _, _ = eng.compute_score(m_tmp, cur_run['Decoupling']/100)
                    d1, d2 = st.columns(2)
                    with d1: st.metric("🚀 Potenza", f"+{details.get('Potenza', 0)}%")
                    with d2: st.metric("🔋 Volume", f"+{details.get('Volume', 0)}%")
                    d3, d4 = st.columns(2)
                    with d3: st.metric("💓 Intensità", f"+{details.get('Intensità', 0)}%")
                    with d4: st.metric("📉 Efficienza", f"{details.get('Malus Efficienza', 0)}")
            
            with c_arch:
                with st.expander("📂 Archivio Attività Completo", expanded=False):
                    render_history_table(df)

            st.divider()

            # --- D. FEEDBACK & LEGENDA ---
            c_feed, c_leg = st.columns([1, 1], gap="large")
            with c_feed:
                 with st.expander("🐞 Segnala un Bug / Idea", expanded=False):
                    render_feedback_form(db_svc, ath.get("id"), athlete_name)
            with c_leg:
                 with st.expander("ℹ️ Legenda Metriche", expanded=False):
                     st.markdown("""
                     **Efficienza (Drift):**
                     - <span style="color:#10B981">●</span> <3% Eccellente
                     - <span style="color:#F59E0B">●</span> 3-5% Buono
                     - <span style="color:#EF4444">●</span> >5% Attenzione
                     - <span style="color:#991B1B">●</span> >10% Critico
                     **Percentile:** Confronto con atleti della tua età.
                     """, unsafe_allow_html=True)
            
            render_legal_section()
