import streamlit as st
import numpy as np
import pandas as pd
import requests
import altair as alt
import google.generativeai as genai
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="SCORE 4.0 Pro Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. DOMAIN LAYER
# ==========================================

@dataclass
class RunMetrics:
    avg_power: float
    avg_hr: float
    distance_meters: float
    duration_seconds: int
    ascent_meters: float
    weight_kg: float
    hr_max: int
    hr_rest: int
    temp_c: float
    humidity: float

class ScoreEngine:
    W_REF_SPEC = 6.0        
    ALPHA = 0.8             
    WR_BASE_DIST = 42195.0
    WR_BASE_TIME = 7235.0   
    RIEGEL_EXP = 1.06

    @staticmethod
    def get_world_record_time(distance_meters: float) -> float:
        if distance_meters <= 0: return 1.0
        return ScoreEngine.WR_BASE_TIME * (distance_meters / ScoreEngine.WR_BASE_DIST) ** ScoreEngine.RIEGEL_EXP

    @staticmethod
    def calculate_decoupling(power_stream: list, hr_stream: list) -> float:
        if not power_stream or not hr_stream or len(power_stream) != len(hr_stream): return 0.0
        half = len(power_stream) // 2
        if half < 60: return 0.0
        p1, h1 = np.mean(power_stream[:half]), np.mean(hr_stream[:half])
        p2, h2 = np.mean(power_stream[half:]), np.mean(hr_stream[half:])
        if h1 == 0 or h2 == 0: return 0.0
        return (p1/h1 - p2/h2) / (p1/h1)

    def compute_score(self, metrics: RunMetrics, decoupling: float) -> Tuple[float, float, float]:
        grade = metrics.ascent_meters / metrics.distance_meters if metrics.distance_meters > 0 else 0
        w_adj = metrics.avg_power * (1 + grade)
        w_spec = w_adj / metrics.weight_kg
        term_efficiency = w_spec / self.W_REF_SPEC
        hrr_percent = max(0.05, (metrics.avg_hr - metrics.hr_rest) / (metrics.hr_max - metrics.hr_rest))
        term_hrr = 1 / hrr_percent
        term_weather = 1.0 + max(0, 0.012 * (metrics.temp_c - 20)) + max(0, 0.005 * (metrics.humidity - 60))
        t_wr = self.get_world_record_time(metrics.distance_meters)
        term_p = t_wr / max(1, metrics.duration_seconds)
        t_hours = metrics.duration_seconds / 3600.0
        term_stability = np.exp(-self.ALPHA * abs(decoupling) / np.sqrt(max(0.1, t_hours)))
        
        score = (term_efficiency * term_hrr * term_weather) * term_p * term_stability
        return score, term_weather, term_p * 100

    @staticmethod
    def get_rank(score: float) -> Tuple[str, str]:
        if score >= 4.0: return "🏆 Classe Mondiale", "success"
        if score >= 3.0: return "🥇 Livello Nazionale", "success"
        if score >= 2.0: return "🥈 Livello Regionale", "warning"
        if score >= 1.0: return "🥉 Runner Avanzato", "info"
        return "👟 Amatore / Recupero", "secondary"

# ==========================================
# 2. INFRASTRUCTURE LAYER (AI & APIs)
# ==========================================

class AICoachService:
    """Gestisce l'integrazione con Google Gemini per l'analisi qualitativa"""
    def __init__(self, api_key):
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def get_coach_feedback(self, metrics_dict):
        if not self.model:
            return "⚠️ Chiave API Gemini mancante. Aggiungila ai Secrets per attivare il Coach."
        
        prompt = f"""
        Sei un allenatore di atletica leggera d'élite, esperto in fisiologia e analisi dati.
        Analizza questa sessione di corsa basandoti sulle metriche SCORE 4.0.
        
        DATI SESSIONE:
        - Distanza: {metrics_dict['Dist (km)']} km
        - Potenza Media: {metrics_dict['Power']} W
        - Battito Medio: {metrics_dict['HR']} bpm
        - Disaccoppiamento (Deriva Aerobica): {metrics_dict['Decoupling']}% (sopra 5% indica fatica/scarso fondo)
        - SCORE 4.0: {metrics_dict['SCORE']} (Scala: <1 Amatore, 1-2 Avanzato, 2-3 Regionale, 3-4 Nazionale, >4 Mondiale)
        - WR Percent: {metrics_dict['WR_Pct']}% (Rispetto al Record del Mondo)
        - Meteo: {metrics_dict['Meteo']} (WCF Factor: {metrics_dict['WCF']})
        
        RICHIESTA:
        Fornisci un feedback tecnico strutturato in 3 punti brevi:
        1. 🧠 **Analisi**: Cosa dice il disaccoppiamento sulla resistenza dell'atleta? Lo SCORE è coerente con il livello?
        2. 🔋 **Gestione**: Ha gestito bene la potenza rispetto al meteo?
        3. 🎯 **Consiglio**: Un singolo allenamento specifico per migliorare il punto debole rilevato.
        
        Tono: Professionale, sintetico, motivante ma severo sui dati. Usa formattazione Markdown.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Errore AI Coach: {e}"

class WeatherService:
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_historical_weather(lat, lon, date_str, hour):
        try:
            params = {"latitude": lat, "longitude": lon, "start_date": date_str, "end_date": date_str, "hourly": "temperature_2m,relative_humidity_2m"}
            res = requests.get(WeatherService.BASE_URL, params=params).json()
            idx = min(hour, 23)
            return res['hourly']['temperature_2m'][idx], res['hourly']['relative_humidity_2m'][idx]
        except: return None, None

class StravaService:
    AUTH_URL = "https://www.strava.com/oauth/authorize"
    TOKEN_URL = "https://www.strava.com/oauth/token"
    API_URL = "https://www.strava.com/api/v3"
    
    def __init__(self, cid, csec): self.cid, self.csec = cid, csec
    
    def get_auth_link(self, redirect_uri):
        return f"{self.AUTH_URL}?client_id={self.cid}&response_type=code&redirect_uri={redirect_uri}&scope=activity:read_all"
    
    def exchange_token(self, code):
        res = requests.post(self.TOKEN_URL, data={"client_id": self.cid, "client_secret": self.csec, "code": code, "grant_type": "authorization_code"})
        return res.json() if res.status_code == 200 else None
        
    def get_activities(self, token, limit=5):
        try:
            acts = requests.get(f"{self.API_URL}/athlete/activities", headers={'Authorization': f'Bearer {token}'}, params={'per_page': limit}).json()
            data = []
            for a in acts:
                if a.get('type') == 'Run':
                    streams = requests.get(f"{self.API_URL}/activities/{a['id']}/streams", headers={'Authorization': f'Bearer {token}'}, params={'keys': 'watts,heartrate,time', 'key_by_type': 'true'}).json()
                    if 'watts' in streams and 'heartrate' in streams:
                        data.append({'summary': a, 'streams': streams})
            return data
        except: return []

# ==========================================
# 3. PRESENTATION LAYER
# ==========================================
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "analyzed_data" not in st.session_state: st.session_state.analyzed_data = []

with st.sidebar:
    st.header("⚙️ Config")
    c_id = st.text_input("Client ID", value=st.secrets.get("strava", {}).get("client_id", ""))
    c_sec = st.text_input("Client Secret", value=st.secrets.get("strava", {}).get("client_secret", ""), type="password")
    
    # AI Key
    ai_key = st.text_input("Gemini API Key", value=st.secrets.get("gemini", {}).get("api_key", ""), type="password")
    
    auth_svc = StravaService(c_id, c_sec)
    
    if st.session_state.strava_token:
        st.success("✅ Connesso")
        if st.button("Logout"): st.session_state.strava_token = None; st.rerun()
    elif c_id and c_sec:
        # URL https://scorerun.streamlit.app/
        redirect = "https://scorerun.streamlit.app/" 
        st.link_button("🔗 Login Strava", auth_svc.get_auth_link(redirect), type="primary")

    st.divider()
    weight = st.number_input("Peso (kg)", 70.0)
    hr_max = st.number_input("FC Max", 185)
    hr_rest = st.number_input("FC Riposo", 50)

# OAUTH CALLBACK
if "code" in st.query_params and not st.session_state.strava_token:
    tk = auth_svc.exchange_token(st.query_params["code"])
    if tk: st.session_state.strava_token = tk; st.query_params.clear(); st.rerun()

st.title("🏃‍♂️ SCORE 4.0 Lab")

if st.session_state.strava_token:
    if st.button("🚀 Scarica e Analizza", type="primary"):
        with st.spinner("Analisi bio-meccanica in corso..."):
            weather_svc = WeatherService()
            engine = ScoreEngine()
            raw = auth_svc.get_activities(st.session_state.strava_token["access_token"], 10)
            
            processed = []
            for d in raw:
                s, str_ = d['summary'], d['streams']
                dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                lat_lng = s.get('start_latlng', [])
                temp, hum = 20.0, 50.0
                source_w = "Def"
                
                if lat_lng:
                    api_t, api_h = weather_svc.get_historical_weather(lat_lng[0], lat_lng[1], dt.strftime("%Y-%m-%d"), dt.hour)
                    if api_t: temp, hum, source_w = api_t, api_h, "API"
                
                mets = RunMetrics(s.get('average_watts', 0), s.get('average_heartrate', 0), s.get('distance', 0), s.get('moving_time', 0), s.get('total_elevation_gain', 0), weight, hr_max, hr_rest, temp, hum)
                dec = engine.calculate_decoupling(str_['watts']['data'], str_['heartrate']['data'])
                score, wcf, wr_p = engine.compute_score(mets, dec)
                rnk_lbl, _ = engine.get_rank(score)
                
                processed.append({
                    "id": s['id'], # ID per selezione
                    "Data": dt.strftime("%Y-%m-%d"),
                    "Dist (km)": round(mets.distance_meters/1000, 2),
                    "Power": int(mets.avg_power),
                    "HR": int(mets.avg_hr),
                    "Decoupling": round(dec*100, 1),
                    "WCF": round(wcf, 2),
                    "SCORE": round(score, 2),
                    "WR_Pct": round(wr_p, 1),
                    "Rank": rnk_lbl,
                    "Meteo": f"{temp}°C ({source_w})",
                    # Salviamo i dati grezzi per Deep Dive (Opzione C)
                    "raw_watts": str_['watts']['data'],
                    "raw_hr": str_['heartrate']['data'],
                    "raw_time": str_.get('time', {}).get('data', [])
                })
            st.session_state.analyzed_data = processed
            st.rerun()

    # --- VISUALIZZAZIONE A TAB ---
    if st.session_state.analyzed_data:
        tab1, tab2 = st.tabs(["📊 Dashboard Generale", "🔬 Deep Dive & AI Coach"])
        
        df = pd.DataFrame(st.session_state.analyzed_data)

        # TAB 1: OVERVIEW
        with tab1:
            st.dataframe(df.drop(columns=['id', 'raw_watts', 'raw_hr', 'raw_time']), use_container_width=True, hide_index=True)
            
            # Grafico WR Benchmark
            base = alt.Chart(df).encode(x='Dist (km)')
            pts = base.mark_circle(size=100).encode(y='WR_Pct', tooltip=['Data', 'SCORE'])
            line = base.mark_line().encode(y='WR_Pct')
            st.altair_chart((pts + line).interactive(), use_container_width=True)

        # TAB 2: DEEP DIVE + AI
        with tab2:
            # Select Box per scegliere la corsa
            run_options = {r['id']: f"{r['Data']} - {r['Dist (km)']}km" for r in st.session_state.analyzed_data}
            sel_id = st.selectbox("Seleziona Corsa da analizzare:", list(run_options.keys()), format_func=lambda x: run_options[x])
            
            # Recupera dati corsa selezionata
            sel_run = next(r for r in st.session_state.analyzed_data if r['id'] == sel_id)
            
            col_ai, col_charts = st.columns([1, 2])
            
            with col_ai:
                st.subheader("🤖 Coach Corner")
                if ai_key:
                    if st.button("Chiedi al Coach", type="primary"):
                        coach = AICoachService(ai_key)
                        with st.spinner("Il coach sta studiando i dati..."):
                            feedback = coach.get_coach_feedback(sel_run)
                            st.markdown(feedback)
                else:
                    st.info("Inserisci la Gemini API Key nella sidebar per attivare il coach.")
                
                st.divider()
                st.metric("Disaccoppiamento (Pw:Hr)", f"{sel_run['Decoupling']}%", 
                          help="Positivo alto (>5%) = perdita efficienza aerobica. Negativo = scarsa forma o partenza troppo forte.")

            with col_charts:
                st.subheader("📈 Analisi Avanzata")
                
                # Creiamo DF per i grafici di dettaglio
                # Assumiamo che le lunghezze delle liste siano uguali (controllato nel motore)
                min_len = min(len(sel_run['raw_watts']), len(sel_run['raw_hr']))
                detail_df = pd.DataFrame({
                    'Time': range(min_len), # O usa raw_time se disponibile
                    'Watts': sel_run['raw_watts'][:min_len],
                    'HR': sel_run['raw_hr'][:min_len]
                })

                # 1. Distribuzione Potenza
                hist = alt.Chart(detail_df).mark_bar().encode(
                    alt.X("Watts", bin=alt.Bin(maxbins=20)),
                    y='count()',
                    color=alt.value("#1f77b4")
                ).properties(title="Distribuzione Potenza (W)", height=200)
                st.altair_chart(hist, use_container_width=True)
                
                # 2. Scatter HR vs Power
                scatter = alt.Chart(detail_df).mark_circle(size=10, opacity=0.3).encode(
                    x=alt.X('Watts', title='Potenza (W)'),
                    y=alt.Y('HR', title='Frequenza Cardiaca (bpm)'),
                    color=alt.Color('Time', title='Progressione Tempo', scale=alt.Scale(scheme='plasma'))
                ).properties(title="Correlazione HR vs Power (Colore = Tempo)", height=300).interactive()
                st.altair_chart(scatter, use_container_width=True)

else:
    st.info("👈 Connettiti a Strava per iniziare.")
