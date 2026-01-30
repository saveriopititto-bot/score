import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 1. CONFIG & VALIDATION (PRIMA DI TUTTO) ---
from config import Config

# Check iniziale dei segreti per evitare crash
missing_secrets = Config.check_secrets()
if missing_secrets:
    st.error(f"❌ Segreti mancanti: {', '.join(missing_secrets)}. Controlla `.streamlit/secrets.toml`.")
    st.stop()

# --- 2. IMPORT MODULI ---
from engine.core import ScoreEngine, RunMetrics
from services.api import StravaService, WeatherService, AICoachService
from services.db import DatabaseService
from ui.visuals import render_benchmark_chart, render_zones_chart, render_scatter_chart, render_history_table, render_trend_chart
from ui.style import apply_custom_style
from ui.legal import render_legal_section  # Importiamo il footer legale

# --- 3. PAGE SETUP ---
st.set_page_config(
    page_title=Config.APP_TITLE, 
    page_icon=Config.APP_ICON, 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Applica lo stile (Montserrat, Box Compatti, Colori #FFCF96)
apply_custom_style()

# --- 4. INIZIALIZZAZIONE SERVIZI ---
strava_creds = Config.get_strava_creds()
supa_creds = Config.get_supabase_creds()
gemini_key = Config.get_gemini_key()

auth_svc = StravaService(strava_creds["client_id"], strava_creds["client_secret"])
db_svc = DatabaseService(supa_creds["url"], supa_creds["key"])

# --- 5. GESTIONE STATO ---
if "strava_token" not in st.session_state: 
    st.session_state.strava_token = None
if "data" not in st.session_state: 
    st.session_state.data = db_svc.get_history()
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

# Callback Strava (Codice -> Token)
if "code" in st.query_params and not st.session_state.strava_token:
    tk = auth_svc.get_token(st.query_params["code"])
    if tk: 
        st.session_state.strava_token = tk
        st.query_params.clear()
        st.rerun()

# =========================================================
# LOGICA PRINCIPALE
# =========================================================

# --- CASO A: UTENTE NON LOGGATO (Landing Page Centrata) ---
if not st.session_state.strava_token:
    
    # Spaziatura verticale per centrare visivamente
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Layout a 3 colonne per centrare il contenuto
    c_left, c_center, c_right = st.columns([1, 2, 1])
    
    with c_center:
        # 1. LOGO GRANDE
        try:
            st.image("sCore.png", use_container_width=True)
        except:
            # Fallback se l'immagine non c'è ancora
            st.markdown("<h1 style='text-align: center; color: #FFCF96;'>sCore Lab</h1>", unsafe_allow_html=True)
        
        # 2. SLOGAN
        st.markdown("""
        <div style="text-align: center; margin-top: -10px; margin-bottom: 30px;">
            <h3 style="color: #6C5DD3; font-weight: 800; letter-spacing: -0.5px;">Corri. Analizza. Evolvi.</h3>
            <p style="color: #636E72; font-size: 1.1rem; line-height: 1.6;">
                Trasforma i tuoi dati Strava in insight scientifici.<br>
                Scopri il tuo vero potenziale con l'analisi SCORE 4.0 Pro.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. BOTTONI AZIONE
        # Sostituisci con il tuo URL finale quando pubblichi
        redirect_url = "https://scorerun.streamlit.app/" 
        link_strava = auth_svc.get_link(redirect_url)
        
        col_b1, col_b2 = st.columns([1, 1], gap="small")
        with col_b1:
            st.link_button("🚀 Connetti Strava", link_strava, type="primary", use_container_width=True)
        with col_b2:
            if st.button("👀 Demo Mode", use_container_width=True):
                st.session_state.demo_mode = True
                # Mock token per la demo
                st.session_state.strava_token = {
                    "access_token": "DEMO_TOKEN", 
                    "athlete": {"id": 12345, "firstname": "Mario", "lastname": "Rossi", "weight": 70.0}
                }
                st.rerun()

        # 4. FOOTER LEGALE (Expander discreto)
        st.markdown("<br><br>", unsafe_allow_html=True)
        render_legal_section()

# --- CASO B: UTENTE LOGGATO (Dashboard) ---
else:
    # --- 6. HEADER & PROFILE ---
    col_header, col_profile = st.columns([3, 1], gap="large")
    with col_header:
        # Logo piccolo per l'intestazione
        try:
            st.image("sCore.png", width=220) 
        except:
            st.title("sCore Lab")
            
        if st.session_state.get("demo_mode"):
            st.caption("🔴 DEMO MODE - Dati Simulati")

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
            # Pulizia cache zone
            if "strava_zones" in st.session_state:
                del st.session_state.strava_zones
            st.rerun()

    # --- 7. CONFIGURAZIONE ATLETA (Auto-Sync) ---
    weight = Config.DEFAULT_WEIGHT
    hr_max = Config.DEFAULT_HR_MAX
    hr_rest = Config.DEFAULT_HR_REST
    ftp = Config.DEFAULT_FTP
    age = Config.DEFAULT_AGE
    zones_data = None

    # Recupero dati da Strava Token
    if not st.session_state.demo_mode:
        token = st.session_state.strava_token["access_token"]
        
        # 1. Dati Base (Peso, FTP)
        strava_weight = ath.get('weight', 0)
        if strava_weight: weight = float(strava_weight)
        
        strava_ftp = ath.get('ftp', 0)
        if strava_ftp: ftp = int(strava_ftp)
        
        # Tentativo Età da birthdate
        birthdate = ath.get('birthdate')
        if birthdate:
            try:
                b_year = int(birthdate.split("-")[0])
                age = datetime.now().year - b_year
            except: pass

        # 2. Recupero Avanzato (FC Max da Zone) - Cachato
        if "strava_zones" not in st.session_state:
            with st.spinner("Sync dati biometrici..."):
                st.session_state.strava_zones = auth_svc.fetch_zones(token)
        
        zones_data = st.session_state.strava_zones
        
        if zones_data:
            hr_zones = zones_data.get("heart_rate", {}).get("zones", [])
            if hr_zones:
                extracted_max = hr_zones[-1].get("max")
                if extracted_max: hr_max = int(extracted_max)

    # UI Profilo
    with st.expander("⚙️ Profilo Atleta & Parametri Fisici", expanded=False):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: weight = st.number_input("Peso (kg)", value=float(weight), step=0.5, help="Da Strava")
        with c2: hr_max = st.number_input("FC Max", value=int(hr_max), help="Da Strava (Zone)")
        with c3: hr_rest = st.number_input("FC Riposo", value=int(hr_rest))
        with c4: ftp = st.number_input("FTP (W)", value=int(ftp))
        with c5: age = st.number_input("Età", value=int(age), help="Per calcolo percentile")
        
        if zones_data:
            st.caption(f"✅ Sync Strava attivo: Peso {weight}kg, FC Max {hr_max}bpm.")

    st.divider()

    # --- 8. TOOLBAR CENTRALE (Filtri e Sync) ---
    space_L, col_controls, space_R = st.columns([3, 2, 3])
    with col_controls:
        c_drop, c_btn = st.columns([2, 1], gap="small", vertical_alignment="bottom")
        
        with c_drop:
            time_options = {"30 Giorni": 30, "90 Giorni": 90, "12 Mesi": 365, "Storico": 3650}
            selected_label = st.selectbox("Periodo Analisi:", list(time_options.keys()), index=2)
            days_to_fetch = time_options[selected_label]

        with c_btn:
            start_sync = st.button("🔄 Sync", type="primary", use_container_width=True, disabled=st.session_state.demo_mode)

    # --- 9. ENGINE DI SINCRONIZZAZIONE ---
    if start_sync and not st.session_state.demo_mode:
        eng = ScoreEngine()
        athlete_id = ath.get("id", 0)
        token = st.session_state.strava_token["access_token"]
        
        with st.spinner(f"Analisi attività Strava ({selected_label})..."):
            activities_list = auth_svc.fetch_activities(token, days_back=days_to_fetch)
        
        if not activities_list:
            st.warning("Nessuna corsa trovata nel periodo.")
        else:
            st.toast(f"Trovate {len(activities_list)} attività. Elaborazione in corso...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            count_new = 0
            existing_ids = [r['id'] for r in st.session_state.data]
            
            # Loop di elaborazione
            for i, s in enumerate(activities_list):
                progress_bar.progress((i + 1) / len(activities_list))
                
                if s['id'] in existing_ids:
                    time.sleep(0.001)
                    continue
                
                status_text.caption(f"Analisi AI: {s['name']}")
                streams = auth_svc.fetch_streams(token, s['id'])
                
                if streams and 'watts' in streams and 'heartrate' in streams:
                    # Parsing Dati
                    dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                    lat_lng = s.get('start_latlng', [])
                    
                    # Meteo Storico
                    t, h = 20.0, 50.0
                    if lat_lng:
                        t, h = WeatherService.get_weather(lat_lng[0], lat_lng[1], dt.strftime("%Y-%m-%d"), dt.hour)

                    # Metriche & Engine
                    m = RunMetrics(s.get('average_watts', 0), s.get('average_heartrate', 0), s.get('distance', 0), s.get('moving_time', 0), s.get('total_elevation_gain', 0), weight, hr_max, hr_rest, t, h)
                    dec = eng.calculate_decoupling(streams['watts']['data'], streams['heartrate']['data'])
                    
                    # Calcolo Score & Dettagli
                    score, details, wcf, wr_p = eng.compute_score(m, dec)
                    rnk, _ = eng.get_rank(score)
                    
                    run_obj = {
                        "id": s['id'], "Data": dt.strftime("%Y-%m-%d"), 
                        "Dist (km)": round(m.distance_meters/1000, 2),
                        "Power": int(m.avg_power), "HR": int(m.avg_hr),
                        "Decoupling": round(dec*100, 1), "WCF": round(wcf, 2),
                        "SCORE": round(score, 2), "WR_Pct": round(wr_p, 1),
                        "Rank": rnk, "Meteo": f"{t}°C",
                        "SCORE_DETAIL": details,
                        "raw_watts": streams['watts']['data'], "raw_hr": streams['heartrate']['data']
                    }
                    
                    if db_svc.save_run(run_obj, athlete_id):
                        count_new += 1
                
                time.sleep(0.1) # Rispetto Rate Limit

            status_text.empty()
            progress_bar.empty()
            
            # Refresh dati
            st.session_state.data = db_svc.get_history()
            
            if count_new > 0:
                st.balloons()
                st.success(f"Archiviate {count_new} nuove attività!")
                time.sleep(1.5)
                st.rerun()
            else:
                st.info("Database già aggiornato.")

    # --- 10. DASHBOARD & VISUALIZZAZIONE ---
    if st.session_state.data:
        st.markdown("<br>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📊 Dashboard Pro", "🔬 Laboratorio Analisi"])
        
        # Preparazione DataFrame
        df = pd.DataFrame(st.session_state.data)
        df['Data'] = pd.to_datetime(df['Data'])
        
        # 1. Ordine Cronologico per Medie Mobili
        df = df.sort_values("Data", ascending=True)
        df["SCORE_MA_7"] = df["SCORE"].rolling(7, min_periods=1).mean()
        df["SCORE_MA_28"] = df["SCORE"].rolling(28, min_periods=1).mean()
        
        # 2. Ordine Inverso per Visualizzazione (Dal più recente)
        df = df.sort_values("Data", ascending=False)
        
        # 3. Filtro Temporale (Menu a tendina)
        if 'days_to_fetch' in locals():
            cutoff = datetime.now() - timedelta(days=days_to_fetch)
            df = df[df['Data'] > cutoff]
        
        if df.empty:
            st.warning("Nessuna corsa nel periodo selezionato.")
        else:
            # Calcoli KPI
            cur_run = df.iloc[0]
            cur_score = cur_run['SCORE']
            cur_ma7 = cur_run['SCORE_MA_7']
            
            # Trend intelligente
            if len(df) > 1:
                prev_ma7 = df.iloc[1]['SCORE_MA_7']
                delta_val = cur_ma7 - prev_ma7
            else:
                prev_ma7 = cur_ma7
                delta_val = 0
            
            if delta_val > 0.005: trend_lbl, trend_col = "In Crescita ↗", "normal"
            elif delta_val < -0.005: trend_lbl, trend_col = "In Calo ↘", "inverse"
            else: trend_lbl, trend_col = "Stabile →", "off"

            # Percentile Età
            eng = ScoreEngine()
            age_pct = eng.age_adjusted_percentile(cur_score, age)

            # --- TAB 1: DASHBOARD ---
            with t1:
                # HERO SECTION (3 Cerchi)
                c_prev, c_main, c_next = st.columns([1, 1.5, 1], gap="small")
                
                with c_prev:
                    st.markdown(f"""<div style="text-align:center; opacity:0.6"><small>TREND IERI</small><br><h1>{round(prev_ma7, 2)}</h1></div>""", unsafe_allow_html=True)
                
                with c_main:
                    clean_rank = cur_run['Rank'].split('/')[0].strip()
                    st.markdown(f"""
                    <div style="display: flex; justify-content: center;">
                        <div style="width: 170px; height: 170px; border-radius: 50%; border: 6px solid #CDFAD5; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                            <span style="color: #999; font-size: 0.7rem; font-weight: 700;">SCORE OGGI</span>
                            <span style="color: #4A4A4A; font-size: 3.2rem; font-weight: 800; line-height: 1;">{cur_score}</span>
                            <div style="background:#CDFAD5; color:#4A4A4A; padding:3px 12px; border-radius:20px; font-size:0.7rem; font-weight:700; margin-top:5px;">{clean_rank}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                
                with c_next:
                     st.markdown(f"""<div style="text-align:center; opacity:0.8"><small style="color:#6C5DD3">PERCENTILE (ETÀ)</small><br><h1 style="color:#6C5DD3">{age_pct}%</h1></div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # KPI 5 COLONNE
                k1, k2, k3, k4, k5 = st.columns(5)
                # (Stile gestito da apply_custom_style in ui/style.py)
                
                with k1: st.metric("Efficienza", f"{cur_run['Decoupling']}%", "Drift")
                with k2: st.metric("Potenza", f"{cur_run['Power']}w", f"{cur_run['Meteo']}")
                with k3: st.metric("Benchmark", f"{cur_run['WR_Pct']}%", "vs WR")
                with k4: st.metric("Media 28gg", f"{round(cur_run['SCORE_MA_28'], 2)}", "Solidità")
                with k5: st.metric("Trend (7gg)", trend_lbl, f"{delta_val:+.3f}", delta_color=trend_col)

                st.markdown("<br>", unsafe_allow_html=True)

                # SCORE SPIEGABILE
                with st.expander("🔍 Perché questo punteggio? (Breakdown)", expanded=True):
                    # Se il dettaglio esiste nel DB usalo, altrimenti ricalcola al volo
                    details = cur_run.get("SCORE_DETAIL")
                    if not details or not isinstance(details, dict):
                         # Fallback rapido
                         m_tmp = RunMetrics(cur_run['Power'], cur_run['HR'], cur_run['Dist (km)']*1000, 0, 0, weight, hr_max, hr_rest, 20, 50)
                         _, details, _, _ = eng.compute_score(m_tmp, cur_run['Decoupling']/100)

                    d1, d2, d3, d4 = st.columns(4)
                    with d1: st.metric("🚀 Potenza", f"+{details.get('Potenza', 0)}")
                    with d2: st.metric("🔋 Volume", f"+{details.get('Volume', 0)}")
                    with d3: st.metric("💓 Intensità", f"+{details.get('Intensità', 0)}")
                    with d4: st.metric("📉 Efficienza", f"{details.get('Malus Efficienza', 0)}")
                    st.caption("Nota: La somma di questi fattori costituisce il tuo Score base.")

                # STORICO
                with st.expander("📂 Archivio Attività", expanded=False):
                    render_history_table(df)

            # --- TAB 2: LABORATORIO ---
            with t2:
                st.markdown("### 🔬 Laboratorio Analisi")
                
                # Grafico Trend
                if len(df) > 1:
                    render_trend_chart(df.head(60)) # Mostriamo ultimi 60gg
                    st.divider()

                # Selettore Attività
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
                        if st.button("🔄 Rigenera"): # Reset feedback locale
                            pass # Richiederà ricaricamento pagina reale per ora
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
                    # Grafici Dettaglio
                    render_scatter_chart(run.get('raw_watts', []), run.get('raw_hr', []))
                    st.markdown("<br>", unsafe_allow_html=True)
                    zones_c = ScoreEngine().calculate_zones(run.get('raw_watts', []), ftp)
                    render_zones_chart(zones_c)
