import streamlit as st
import numpy as np
import pandas as pd
import requests
import altair as alt
import google.generativeai as genai
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="SCORE 4.0 Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. DOMAIN LAYER (Logica di Business)
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
    """Motore di calcolo SCORE 4.0, Riegel Benchmark e Zone Coggan"""
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

    @staticmethod
    def calculate_zones(watts_stream: list, ftp: int) -> List[Dict]:
        """Calcola la distribuzione % nelle zone di Coggan basate sulla FTP"""
        if not watts_stream or ftp <= 0: return []
        
        # Definizione Zone Coggan (Limite superiore, Colore)
        zones_def = [
            {"name": "Z1 Recupero", "limit": 0.55 * ftp, "color": "#bdc3c7"}, # Grigio
            {"name": "Z2 Fondo Lento", "limit": 0.75 * ftp, "color": "#3498db"}, # Blu
            {"name": "Z3 Tempo", "limit": 0.90 * ftp, "color": "#2ecc71"}, # Verde
            {"name": "Z4 Soglia", "limit": 1.05 * ftp, "color": "#f1c40f"}, # Giallo
            {"name": "Z5 VO2Max", "limit": 1.20 * ftp, "color": "#e67e22"}, # Arancione
            {"name": "Z6 Anaerobico", "limit": 9999, "color": "#e74c3c"}  # Rosso
        ]
        
        counts = [0] * len(zones_def)
        total_samples = len(watts_stream)
        
        # Assegnazione sample alle zone
        for w in watts_stream:
            for i, z in enumerate(zones_def):
                if w <= z["limit"]:
                    counts[i] += 1
                    break
        
        # Preparazione dati per grafico
        result = []
        for i, z in enumerate(zones_def):
            pct = (counts[i] / total_samples) * 100
            minutes = round((counts[i]) / 60, 1) # Assumendo 1 sample al secondo
            if pct > 0.1: # Escludiamo zone vuote per pulizia grafico
                result.append({
                    "Zone": z["name"],
                    "Percent": pct,
                    "Color": z["color"],
                    "Minutes": minutes
                })
        return result

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
        Sei un allenatore di atletica leggera d'élite. Analizza questa sessione di corsa (SCORE 4.0).
        
        DATI:
        - Distanza: {metrics_dict['Dist (km)']} km
        - Potenza: {metrics_dict['Power']} W
        - HR: {metrics_dict['HR']} bpm
        - Disaccoppiamento: {metrics_dict['Decoupling']}% (positivo alto >5% = deriva)
        - SCORE: {metrics_dict['SCORE']} (<1 Amatore, >4 Mondiale)
        - WR Percent: {metrics_dict['WR_Pct']}%
        - Meteo: {metrics_dict['Meteo']}
        
        RICHIESTA (Markdown, breve):
        1. 🧠 **Analisi**: Valuta efficienza e resistenza (disaccoppiamento).
        2. 🔋 **Gestione**: Ha tenuto bene?
        3. 🎯 **Consiglio**: Un allenamento specifico da fare.
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
            prog_bar = st.progress(0, text="Scaricamento dati...")
            for i, a in enumerate(acts):
                if a.get('type') == 'Run':
                    streams = requests.get(f"{self.API_URL}/activities/{a['id']}/streams", headers={'Authorization': f'Bearer {token}'}, params={'keys': 'watts,heartrate,time', 'key_by_type': 'true'}).json()
                    if 'watts' in streams and 'heartrate' in streams:
                        data.append({'summary': a, 'streams': streams})
                prog_bar.progress((i + 1) / limit)
            prog_bar.empty()
            return data
        except: return []

# ==========================================
# 3. PRESENTATION LAYER (UI)
# ==========================================
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "analyzed_data" not in st.session_state: st.session_state.analyzed_data = []

with st.sidebar:
    st.header("⚙️ Configurazione")
    c_id = st.text_input("Client ID", value=st.secrets.get("strava", {}).get("client_id", ""))
    c_sec = st.text_input("Client Secret", value=st.secrets.get("strava", {}).get("client_secret", ""), type="password")
    ai_key = st.text_input("Gemini API Key", value=st.secrets.get("gemini", {}).get("api_key", ""), type="password")
    
    auth_svc = StravaService(c_id, c_sec)
    
    st.divider()
    
    if st.session_state.strava_token:
        st.success("✅ Strava Connesso")
        if st.button("Logout", use_container_width=True): st.session_state.strava_token = None; st.rerun()
    elif c_id and c_sec:
        # --- URL PRODUZIONE AGGIORNATO ---
        redirect = "https://scorerun.streamlit.app/" 
        st.link_button("🔗 Login Strava", auth_svc.get_auth_link(redirect), type="primary", use_container_width=True)
    else:
        st.info("Inserisci le credenziali per connetterti.")

    st.divider()
    st.header("👤 Atleta")
    weight = st.number_input("Peso (kg)", 70.0, step=0.5)
    hr_max = st.number_input("FC Max", 185)
    hr_rest = st.number_input("FC Riposo", 50)
    # --- NUOVO INPUT FTP ---
    ftp = st.number_input("FTP (W)", value=250, step=5, help="Functional Threshold Power per calcolo Zone")

# OAUTH CALLBACK
if "code" in st.query_params and not st.session_state.strava_token:
    with st.spinner("Autenticazione..."):
        tk = auth_svc.exchange_token(st.query_params["code"])
        if tk: st.session_state.strava_token = tk; st.query_params.clear(); st.rerun()

st.title("🏃‍♂️ SCORE 4.0 Lab")

if st.session_state.strava_token:
    if st.button("🚀 Scarica e Analizza", type="primary", use_container_width=True):
        with st.spinner("Elaborazione algoritmi SCORE..."):
            weather_svc = WeatherService()
            engine = ScoreEngine()
            raw = auth_svc.get_activities(st.session_state.strava_token["access_token"], 10)
            
            processed = []
            for d in raw:
                s, str_ = d['summary'], d['streams']
                dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                lat_lng = s.get('start_latlng', [])
                temp, hum, source_w = 20.0, 50.0, "Def"
                
                if lat_lng:
                    api_t, api_h = weather_svc.get_historical_weather(lat_lng[0], lat_lng[1], dt.strftime("%Y-%m-%d"), dt.hour)
                    if api_t: temp, hum, source_w = api_t, api_h, "API"
                
                mets = RunMetrics(s.get('average_watts', 0), s.get('average_heartrate', 0), s.get('distance', 0), s.get('moving_time', 0), s.get('total_elevation_gain', 0), weight, hr_max, hr_rest, temp, hum)
                dec = engine.calculate_decoupling(str_['watts']['data'], str_['heartrate']['data'])
                score, wcf, wr_p = engine.compute_score(mets, dec)
                rnk_lbl, _ = engine.get_rank(score)
                
                processed.append({
                    "id": s['id'],
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
                    "raw_watts": str_['watts']['data'],
                    "raw_hr": str_['heartrate']['data']
                })
            st.session_state.analyzed_data = processed
            st.rerun()

    # --- TAB VISUALIZATION ---
    if st.session_state.analyzed_data:
        tab1, tab2 = st.tabs(["📊 Dashboard", "🔬 Deep Dive & Zone"])
        
        df = pd.DataFrame(st.session_state.analyzed_data)

        # TAB 1
        with tab1:
            st.dataframe(df.drop(columns=['id', 'raw_watts', 'raw_hr']), use_container_width=True, hide_index=True)
            st.subheader("Benchmark Mondiale (Riegel)")
            chart = alt.Chart(df).mark_circle(size=120).encode(
                x=alt.X('Dist (km)', scale=alt.Scale(zero=False)),
                y=alt.Y('WR_Pct', title='% Velocità Record Mondo'),
                color=alt.Color('WR_Pct', scale=alt.Scale(scheme='magma')),
                tooltip=['Data', 'SCORE', 'WR_Pct']
            ).interactive()
            st.altair_chart(chart, use_container_width=True)

        # TAB 2
        with tab2:
            run_opts = {r['id']: f"{r['Data']} - {r['Dist (km)']}km" for r in st.session_state.analyzed_data}
            sel_id = st.selectbox("Seleziona Attività:", list(run_opts.keys()), format_func=lambda x: run_opts[x])
            sel_run = next(r for r in st.session_state.analyzed_data if r['id'] == sel_id)
            
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.subheader("🤖 Coach AI")
                if ai_key:
                    if st.button("Analizza Sessione"):
                        with st.spinner("Analisi in corso..."):
                            coach = AICoachService(ai_key)
                            st.markdown(coach.get_coach_feedback(sel_run))
                else: st.warning("Serve API Key Gemini.")
                
                st.divider()
                st.metric("Disaccoppiamento", f"{sel_run['Decoupling']}%", delta_color="inverse")

            with col_right:
                engine = ScoreEngine()
                
                # 1. Scatter HR/Power
                st.subheader("Efficienza Aerobica")
                min_len = min(len(sel_run['raw_watts']), len(sel_run['raw_hr']))
                dd = pd.DataFrame({'Watts': sel_run['raw_watts'][:min_len], 'HR': sel_run['raw_hr'][:min_len], 'Time': range(min_len)})
                
                scat = alt.Chart(dd).mark_circle(opacity=0.3).encode(
                    x='Watts', y=alt.Y('HR', scale=alt.Scale(zero=False)), 
                    color=alt.Color('Time', title='Tempo', scale=alt.Scale(scheme='plasma'))
                ).properties(height=250).interactive()
                st.altair_chart(scat, use_container_width=True)
                
                # 2. Zone Distribuzione (NUOVO)
                st.subheader(f"🚦 Distribuzione Zone (FTP: {ftp}W)")
                zones_data = engine.calculate_zones(sel_run['raw_watts'], ftp)
                
                if zones_data:
                    z_df = pd.DataFrame(zones_data)
                    bars = alt.Chart(z_df).mark_bar().encode(
                        x=alt.X('Percent', title='% Tempo'),
                        y=alt.Y('Zone', sort=None),
                        color=alt.Color('Color', scale=None),
                        tooltip=['Zone', 'Percent', 'Minutes']
                    ).properties(height=250)
                    
                    text = bars.mark_text(dx=3, align='left').encode(text=alt.Text('Percent', format='.1f'))
                    st.altair_chart(bars + text, use_container_width=True)
                else:
                    st.info("Dati potenza insufficienti o FTP a 0.")

else:
    st.info("👈 Effettua il Login Strava dalla sidebar.")
