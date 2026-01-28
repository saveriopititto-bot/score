import streamlit as st
import pandas as pd
import time
from datetime import datetime

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
    # Sezione Azioni (Download)
    col_act_1, col_act_2 = st.columns([1.5, 3.5]) # Ho allargato un po' la colonna sinistra per il menu
    with col_act_1:
        # 1. MENU A TENDINA (Nuovo!)
        time_options = {
            "Ultimi 30 Giorni": 30,
            "Ultimi 90 Giorni": 90,
            "Ultimi 12 Mesi": 365,
            "Ultimi 5 Anni": 365*5,
            "Tutto lo Storico": 365*20
        }
        
        # Selectbox che salva la scelta
        selected_label = st.selectbox(
            "Periodo da analizzare:", 
            options=list(time_options.keys()), 
            index=2 # Default: 12 Mesi
        )
        
        days_to_fetch = time_options[selected_label]

        # 2. PULSANTE DINAMICO
        if st.button(f"🚀 Scarica {selected_label}", type="primary", use_container_width=True):
            
            eng = ScoreEngine()
            athlete_id = st.session_state.strava_token.get("athlete", {}).get("id", 0)
            token = st.session_state.strava_token["access_token"]
            
            # Usiamo la variabile scelta dall'utente (days_to_fetch)
            with st.spinner(f"Recupero elenco attività ({selected_label})..."):
                activities_list = auth_svc.fetch_activities(token, days_back=days_to_fetch)
            
            if not activities_list:
                st.warning(f"Nessuna corsa trovata negli {selected_label}.")
            else:
                st.info(f"Trovate {len(activities_list)} corse. Inizio download dettagli...")
                
                # BARRA DI PROGRESSO
                progress_bar = st.progress(0)
                status_text = st.empty()
                count_new = 0
                
                # Recuperiamo gli ID già salvati per non scaricarli due volte
                existing_ids = [r['id'] for r in st.session_state.data]
                
                # Ciclo su ogni attività trovata
                for i, s in enumerate(activities_list):
                    # Aggiorniamo la barra
                    progress = (i + 1) / len(activities_list)
                    progress_bar.progress(progress)
                    status_text.text(f"Analisi corsa {i+1}/{len(activities_list)}: {s['name']}")
                    
                    # SE ESISTE GIÀ, SALTA!
                    if s['id'] in existing_ids:
                        # Se stiamo scaricando "Tutto lo storico", questa parte sarà velocissima
                        time.sleep(0.005) 
                        continue 

                    # Scarichiamo gli STREAMS
                    streams = auth_svc.fetch_streams(token, s['id'])
                    
                    if streams and 'watts' in streams and 'heartrate' in streams:
                        dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                        lat_lng = s.get('start_latlng', [])
                        
                        # Meteo
                        t, h = WeatherService.get_weather(lat_lng[0], lat_lng[1], dt.strftime("%Y-%m-%d"), dt.hour) if lat_lng else (20.0, 50.0)
                        if not t: t, h = 20.0, 50.0

                        # Metrics
                        m = RunMetrics(s.get('average_watts', 0), s.get('average_heartrate', 0), s.get('distance', 0), s.get('moving_time', 0), s.get('total_elevation_gain', 0), weight, hr_max, hr_rest, t, h)
                        
                        # Calcoli
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
                    
                    # Pausa tattica
                    time.sleep(0.1)
                
                # Fine Processo
                status_text.empty()
                progress_bar.empty()
                
                # Ricarichiamo i dati aggiornati
                st.session_state.data = db_svc.get_history()
                
                if count_new > 0: 
                    st.balloons()
                    st.success(f"✅ Completato! Archiviate {count_new} nuove attività.")
                    time.sleep(2)
                    st.rerun()
                else: 
                    st.info("Il database è già aggiornato.")
    # --- DASHBOARD & LAB ---
    if st.session_state.data:
        st.markdown("<br>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📊 Dashboard", "🔬 Laboratorio Analisi"])
        df = pd.DataFrame(st.session_state.data)
        
        # TAB 1: DASHBOARD
        with t1:
            last = df.iloc[0]
            
            # HERO (Score Cerchio)
            empty_L, c_score, empty_R = st.columns([1, 2, 1])
            with c_score:
                raw_rank = last['Rank']
                clean_rank = raw_rank.split('/')[0].strip()
                score_val = last['SCORE']
                
                html_circle = f"""
<div style="display: flex; justify-content: center; margin-bottom: 10px;">
    <div style="width: 180px; height: 180px; border-radius: 50%; border: 6px solid #CDFAD5; background-color: white; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 10px 25px rgba(0,0,0,0.05); transition: transform 0.3s ease; cursor: default;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
        <span style="color: #999; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;">SCORE</span>
        <span style="color: #4A4A4A; font-size: 3.5rem; font-weight: 800; line-height: 1;">{score_val}</span>
        <div style="background-color: #CDFAD5; color: #4A4A4A; padding: 4px 15px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; margin-top: 5px;">
            {clean_rank}
        </div>
    </div>
</div>
"""
                st.markdown(html_circle, unsafe_allow_html=True)

            # KPI
            sp1, k1, k2, k3, sp2 = st.columns([1.5, 1, 1, 1, 1.5], gap="small")
            st.markdown("""<style>div[data-testid="stMetric"] { text-align: center; align-items: center; justify-content: center; } div[data-testid="stMetricLabel"] { justify-content: center; }</style>""", unsafe_allow_html=True)
            with k1: st.metric("Efficienza", f"{last['Decoupling']}%", "Drift")
            with k2: st.metric("Potenza", f"{last['Power']}w", f"{last['Meteo']}")
            with k3: st.metric("Benchmark", f"{last['WR_Pct']}%", "vs WR")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # NUOVO: GRAFICO TREND
            if len(df) > 1:
                render_trend_chart(df.head(30)) # Mostra ultimi 30 allenamenti
                st.markdown("<br>", unsafe_allow_html=True)

            # MAIN CONTENT
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
                    <div style="background-color: white; padding: 15px; border-radius: 20px; margin-bottom: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); display: flex; justify-content: space-between; align-items: center; border: 1px solid white; transition: transform 0.2s;" onmouseover="this.style.transform='translateX(5px)'" onmouseout="this.style.transform='translateX(0)'">
                        <div><div style="font-weight:bold; color:#4A4A4A; font-size:0.9rem;">{row['Data']}</div><div style="font-size:0.75rem; color:#999; margin-top:3px;">{row['Dist (km)']} km • {row['Power']} W</div></div>
                        <div style="background-color: {score_color}; color: white; padding: 5px 12px; border-radius: 12px; font-weight: bold; font-size: 0.85rem;">{row['SCORE']}</div>
                    </div>""", unsafe_allow_html=True)

        # TAB 2: LAB (Con Cache AI)
        with t2:
            opts = {r['id']: f"{r['Data']} - {r['Dist (km)']}km" for r in st.session_state.data}
            sel = st.selectbox("Seleziona Analisi:", list(opts.keys()), format_func=lambda x: opts[x])
            run = next(r for r in st.session_state.data if r['id'] == sel)
            
            col_ai, col_charts = st.columns([1, 2], gap="medium")
            
            with col_ai:
                st.markdown("##### 🤖 Coach AI")
                
                # LOGICA CACHE AI
                existing_feedback = run.get('ai_feedback')
                
                if existing_feedback:
                    st.success("✅ Analisi recuperata dall'archivio")
                    st.markdown(existing_feedback)
                    # Tasto per rigenerare se proprio serve
                    if st.button("🔄 Rigenera Analisi"):
                        existing_feedback = None # Reset temporaneo per forzare il ricalcolo sotto
                
                if not existing_feedback:
                    ai_key = gemini_conf.get("api_key")
                    if ai_key:
                        if st.button("✨ Genera Analisi AI", type="primary"):
                            with st.spinner("L'AI sta studiando la tua corsa..."):
                                coach = AICoachService(ai_key)
                                zones_calc = ScoreEngine.calculate_zones(run['raw_watts'], ftp)
                                feedback = coach.get_feedback(run, zones_calc)
                                
                                st.markdown(feedback)
                                
                                # Salvataggio Cache
                                if db_svc.update_ai_feedback(run['id'], feedback):
                                    st.toast("Analisi salvata nel database!")
                                    # Aggiorniamo lo stato locale
                                    run['ai_feedback'] = feedback
                    else:
                        st.warning("⚠️ Gemini API Key mancante.")

                st.markdown("<br>", unsafe_allow_html=True)
                st.metric("Decoupling", f"{run['Decoupling']}%")
                
            with col_charts:
                render_scatter_chart(run['raw_watts'], run['raw_hr'])
                st.markdown("<br>", unsafe_allow_html=True)
                render_zones_chart(ScoreEngine.calculate_zones(run['raw_watts'], ftp))

    else:
        # Questo else ora è allineato correttamente con "if st.session_state.data"
        st.info("👆 Connetti Strava per iniziare.")
