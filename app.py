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
        
        # --- PREPARAZIONE DATI ---
        df = pd.DataFrame(st.session_state.data)
        df['Data'] = pd.to_datetime(df['Data'])
        df = df.sort_values(by='Data', ascending=False) # Ordine: [Oggi, Ieri, L'altro ieri...]
        
        # Calcolo Valori per i 3 Cerchi
        current_run = df.iloc[0]
        current_score = current_run['SCORE']
        
        # PASSATO (Previous)
        if len(df) > 1:
            prev_run = df.iloc[1]
            prev_score = prev_run['SCORE']
        else:
            prev_score = current_score # Fallback se è la prima corsa
            
        # FUTURO (Expected / Form) - Media delle ultime 3 corse
        expected_score = round(df.head(3)['SCORE'].mean(), 2)

        # CALCOLO TREND (Per la freccia)
        diff = current_score - prev_score
        if diff > 0:
            trend_arrow = "↗"
            trend_color = "#4CAF50" # Verde
            trend_label = "In Crescita"
        elif diff < 0:
            trend_arrow = "↘"
            trend_color = "#FF5252" # Rosso
            trend_label = "In Calo"
        else:
            trend_arrow = "→"
            trend_color = "#999"
            trend_label = "Stabile"

        # --- TAB 1: BENTO DASHBOARD ---
        with t1:
            
            # 1. HERO SECTION: TRE CERCHI (Passato - Presente - Futuro)
            # Layout: Colonna piccola, Colonna Grande, Colonna Piccola
            c_prev, c_main, c_next = st.columns([1, 1.5, 1], gap="small")
            
            # --- CERCHIO SINISTRA (Passato) ---
            with c_prev:
                st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; opacity: 0.7;">
                    <div style="font-size: 0.8rem; font-weight: bold; color: #888; margin-bottom: 5px;">PRECEDENTE</div>
                    <div style="
                        width: 100px; height: 100px; border-radius: 50%;
                        border: 4px solid #ddd; background: white;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 1.8rem; font-weight: 700; color: #888;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                    ">
                        {prev_score}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # --- CERCHIO CENTRALE (Presente / Totale) ---
            with c_main:
                raw_rank = current_run['Rank']
                clean_rank = raw_rank.split('/')[0].strip()
                
                st.markdown(f"""
                <div style="display: flex; justify-content: center;">
                    <div style="
                        width: 170px; height: 170px; border-radius: 50%;
                        border: 6px solid #CDFAD5; background: white;
                        display: flex; flex-direction: column; align-items: center; justify-content: center;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        z-index: 10; position: relative;
                    ">
                        <span style="color: #999; font-size: 0.75rem; font-weight: 700; letter-spacing: 1px;">SCORE ATTUALE</span>
                        <span style="color: #4A4A4A; font-size: 3.2rem; font-weight: 800; line-height: 1;">{current_score}</span>
                        <div style="background-color: #CDFAD5; color: #4A4A4A; padding: 3px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; margin-top: 5px;">
                            {clean_rank}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # --- CERCHIO DESTRA (Futuro / Atteso) ---
            with c_next:
                 st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; opacity: 0.7;">
                    <div style="font-size: 0.8rem; font-weight: bold; color: #6C5DD3; margin-bottom: 5px;">ATTESO</div>
                    <div style="
                        width: 100px; height: 100px; border-radius: 50%;
                        border: 4px dashed #6C5DD3; background: white;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 1.8rem; font-weight: 700; color: #6C5DD3;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                    ">
                        {expected_score}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 2. KPI BOXES (Con Trend aggiunto)
            # Usiamo 4 colonne ora
            k1, k2, k3, k4 = st.columns(4, gap="small")
            
            # CSS per centrare testo metriche
            st.markdown("""<style>div[data-testid="stMetric"] { text-align: center; align-items: center; justify-content: center; } div[data-testid="stMetricLabel"] { justify-content: center; }</style>""", unsafe_allow_html=True)
            
            with k1: st.metric("Efficienza", f"{current_run['Decoupling']}%", "Drift")
            with k2: st.metric("Potenza", f"{current_run['Power']}w", f"{current_run['Meteo']}")
            with k3: st.metric("Benchmark", f"{current_run['WR_Pct']}%", "vs WR")
            
            # KPI TREND PERSONALIZZATO
            with k4:
                st.markdown(f"""
                <div style="
                    background-color: white; border: 1px solid #eee; border-radius: 10px; padding: 10px;
                    display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90px;
                ">
                    <span style="font-size: 0.8rem; color: #888;">Trend</span>
                    <span style="font-size: 1.8rem; color: {trend_color}; font-weight: bold;">{trend_arrow}</span>
                    <span style="font-size: 0.7rem; color: {trend_color}; font-weight: 600;">{trend_label}</span>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)

            # 3. LISTA RECENTI (Full Width ora che il grafico è sparito)
            # Layout: Lista a sinistra (più grande) e Dettagli testuali a destra? 
            # Oppure Lista centrata. Facciamo Lista Centrata per pulizia.
            st.markdown("##### 🗃 Ultime Attività")
            render_history_table(df)

        # --- TAB 2: LAB (Con Grafico Trend Spostato Qui) ---
        with t2:
            st.markdown("### 🔬 Laboratorio Analisi")
            
            # 1. GRAFICO TREND (Spostato qui)
            if len(df) > 1:
                render_trend_chart(df.head(30))
                st.divider()

            # 2. SELETTORE ATTIVITÀ E ANALISI
            opts = {r['id']: f"{r['Data'].strftime('%Y-%m-%d')} - {r['Dist (km)']}km" for i, r in df.iterrows()}
            # Nota: iterrows su df ordinato per data, quindi la lista nel menu è ordinata
            
            sel = st.selectbox("Seleziona Attività Specifica:", list(opts.keys()), format_func=lambda x: opts[x])
            
            # Recuperiamo la run selezionata dal DataFrame (più veloce che loopare st.session_state)
            run = df[df['id'] == sel].iloc[0].to_dict() # Convertiamo in dict per compatibilità con le funzioni esistenti
            
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
                                # Non aggiorniamo df locale perché è una copia, ma al prossimo rerun si vedrà
                    else:
                        st.warning("⚠️ Manca API Key")

                st.markdown("<br>", unsafe_allow_html=True)
                st.metric("Decoupling", f"{run['Decoupling']}%")
                
            with col_charts:
                render_scatter_chart(run['raw_watts'], run['raw_hr'])
                st.markdown("<br>", unsafe_allow_html=True)
                render_zones_chart(ScoreEngine.calculate_zones(run['raw_watts'], ftp))

    else:
        # Questo else ora è allineato correttamente con "if st.session_state.data"
        st.info("👆 Connetti Strava per iniziare.")
