import streamlit as st
import numpy as np
import pandas as pd
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Tuple

# ==========================================
# 1. DOMAIN LAYER: SCORE 4.0 ENGINE
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
    REF_PACE_SEC_KM = 153.0 
    ALPHA = 0.8            

    @staticmethod
    def calculate_decoupling(power_stream, hr_stream):
        if not power_stream or not hr_stream or len(power_stream) != len(hr_stream):
            return 0.0
        
        half = len(power_stream) // 2
        if half < 60: return 0.0 

        p1 = np.mean(power_stream[:half])
        h1 = np.mean(hr_stream[:half])
        p2 = np.mean(power_stream[half:])
        h2 = np.mean(hr_stream[half:])

        if h1 == 0 or h2 == 0: return 0.0

        ratio1 = p1 / h1
        ratio2 = p2 / h2
        
        return (ratio1 - ratio2) / ratio1

    def compute_score(self, metrics: RunMetrics, decoupling: float):
        # 1. Potenza Normalizzata (Ascesa)
        grade = metrics.ascent_meters / metrics.distance_meters if metrics.distance_meters > 0 else 0
        w_adj = metrics.avg_power * (1 + grade)

        # 2. Efficienza Normalizzata
        w_spec = w_adj / metrics.weight_kg
        term_efficiency = w_spec / self.W_REF_SPEC

        # 3. Costo Cardiaco (HRR)
        hrr_percent = (metrics.avg_hr - metrics.hr_rest) / (metrics.hr_max - metrics.hr_rest)
        hrr_percent = max(0.05, hrr_percent) 
        term_hrr = 1 / hrr_percent

        # 4. Weather Correction Factor (WCF)
        # Nota: WCF premia chi corre al caldo o con alta umidità
        term_weather = 1.0 + \
                       max(0, 0.012 * (metrics.temp_c - 20)) + \
                       max(0, 0.005 * (metrics.humidity - 60))

        # 5. Performance Factor (P)
        t_ref_seconds = (metrics.distance_meters / 1000.0) * self.REF_PACE_SEC_KM
        term_p = t_ref_seconds / max(1, metrics.duration_seconds)

        # 6. Stabilità Cardiovascolare
        t_hours = metrics.duration_seconds / 3600.0
        term_stability = np.exp(-self.ALPHA * abs(decoupling) / np.sqrt(max(0.1, t_hours)))

        score = (term_efficiency * term_hrr * term_weather) * term_p * term_stability
        
        return score, term_weather

    @staticmethod
    def get_rank(score):
        if score >= 4.0: return "🏆 Classe Mondiale", "success"
        if score >= 3.0: return "🥇 Livello Nazionale", "success"
        if score >= 2.0: return "🥈 Livello Regionale", "warning"
        if score >= 1.0: return "🥉 Runner Avanzato", "info"
        return "👟 Amatore / Recupero", "secondary"

# ==========================================
# 2. INFRASTRUCTURE LAYER: SERVICES
# ==========================================

class WeatherService:
    """Gestisce il recupero dati meteo storici da Open-Meteo Archive API"""
    
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    @staticmethod
    @st.cache_data(ttl=86400, show_spinner=False) # Cache 24h
    def get_historical_weather(lat: float, lon: float, date_str: str, hour: int) -> Tuple[Optional[float], Optional[float]]:
        """
        Recupera Temp e Umidità per una specifica coordinata e ora passata.
        date_str format: 'YYYY-MM-DD'
        """
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": date_str,
                "end_date": date_str,
                "hourly": "temperature_2m,relative_humidity_2m",
                "timezone": "auto"
            }
            
            response = requests.get(WeatherService.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # L'API restituisce un array di 24 ore. Prendiamo l'indice dell'ora della corsa.
            # Se l'ora è fuori range (es. 24), clampiamo a 23.
            idx = min(hour, 23)
            
            temp = data['hourly']['temperature_2m'][idx]
            hum = data['hourly']['relative_humidity_2m'][idx]
            
            return temp, hum
        except Exception as e:
            # Silenzioso: se fallisce il meteo, non vogliamo bloccare l'app
            print(f"Weather API Error: {e}") 
            return None, None

class StravaService:
    BASE_URL = "https://www.strava.com/api/v3"

    def __init__(self, client_id, client_secret, refresh_token):
        self.auth = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        self.access_token = None

    def authenticate(self):
        try:
            res = requests.post("https://www.strava.com/oauth/token", data=self.auth)
            res.raise_for_status()
            self.access_token = res.json()['access_token']
            return True
        except Exception:
            return False

    def get_activities(self, limit=5):
        if not self.access_token: return []
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        try:
            activities = requests.get(
                f"{self.BASE_URL}/athlete/activities", 
                headers=headers, 
                params={'per_page': limit}
            ).json()
            
            full_data = []
            prog_bar = st.progress(0, text="Analisi flussi e meteo...")
            
            for i, act in enumerate(activities):
                if act.get('type') == 'Run' and act.get('device_watts', False):
                    act_id = act['id']
                    # Stream di base
                    streams = requests.get(
                        f"{self.BASE_URL}/activities/{act_id}/streams",
                        headers=headers,
                        params={'keys': 'watts,heartrate', 'key_by_type': 'true'}
                    ).json()
                    
                    if 'watts' in streams and 'heartrate' in streams:
                        full_data.append({'summary': act, 'streams': streams})
                
                prog_bar.progress((i + 1) / limit)
            
            prog_bar.empty()
            return full_data
        except Exception as e:
            st.error(f"Errore Fetch Dati: {e}")
            return []

# ==========================================
# 3. PRESENTATION LAYER: STREAMLIT APP
# ==========================================

st.set_page_config(page_title="SCORE 4.0 Pro", layout="wide")

st.title("🏃‍♂️ SCORE 4.0 Competitive Index")
st.markdown("Algoritmo con correzione climatica automatica (Open-Meteo API).")

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Profilo Atleta")
    weight = st.number_input("Peso (kg)", value=70.0, step=0.5)
    hr_max = st.number_input("FC Max", value=185, step=1)
    hr_rest = st.number_input("FC Riposo", value=50, step=1)
    
    st.divider()
    st.header("🔗 Connessione")
    
    # Auto-load secrets se presenti
    def_cid = st.secrets.get("strava", {}).get("client_id", "")
    def_csec = st.secrets.get("strava", {}).get("client_secret", "")
    def_rtok = st.secrets.get("strava", {}).get("refresh_token", "")

    c_id = st.text_input("Client ID", value=def_cid)
    c_sec = st.text_input("Client Secret", type="password", value=def_csec)
    r_tok = st.text_input("Refresh Token", type="password", value=def_rtok)
    
    do_analysis = st.button("🚀 Analizza Corse", type="primary")

# --- MAIN LOGIC ---
if do_analysis and c_id and r_tok:
    strava_svc = StravaService(c_id, c_sec, r_tok)
    weather_svc = WeatherService()
    engine = ScoreEngine()
    
    if strava_svc.authenticate():
        raw_data = strava_svc.get_activities(limit=10)
        results = []
        
        for d in raw_data:
            summary = d['summary']
            streams = d['streams']
            
            # 1. Parsing Data e Ora
            start_date_local = summary['start_date_local'] # es. "2023-10-27T10:00:00Z"
            dt_obj = datetime.strptime(start_date_local, "%Y-%m-%dT%H:%M:%SZ")
            date_str = dt_obj.strftime("%Y-%m-%d")
            hour = dt_obj.hour
            
            # 2. Logica Meteo Avanzata
            lat_lng = summary.get('start_latlng', [])
            
            final_temp = 20.0 # Fallback
            final_hum = 50.0  # Fallback
            source_weather = "Default"

            if lat_lng and len(lat_lng) == 2:
                lat, lon = lat_lng[0], lat_lng[1]
                # Chiamata API Meteo (Cachata)
                api_temp, api_hum = weather_svc.get_historical_weather(lat, lon, date_str, hour)
                
                if api_temp is not None:
                    final_temp = api_temp
                    final_hum = api_hum
                    source_weather = "API 🌤"
            
            # 3. Costruzione Metriche
            metrics = RunMetrics(
                avg_power=summary.get('average_watts', 0),
                avg_hr=summary.get('average_heartrate', 0),
                distance_meters=summary.get('distance', 0),
                duration_seconds=summary.get('moving_time', 0),
                ascent_meters=summary.get('total_elevation_gain', 0),
                weight_kg=weight,
                hr_max=hr_max,
                hr_rest=hr_rest,
                temp_c=final_temp,
                humidity=final_hum
            )
            
            # 4. Calcoli Motore
            decoupling = engine.calculate_decoupling(streams['watts']['data'], streams['heartrate']['data'])
            score_val, wcf_val = engine.compute_score(metrics, decoupling)
            rank_label, rank_color = engine.get_rank(score_val)
            
            results.append({
                "Data": date_str,
                "Dist (km)": f"{metrics.distance_meters/1000:.1f}",
                "Power (W)": f"{metrics.avg_power:.0f}",
                "Meteo": f"{final_temp:.1f}°C / {final_hum:.0f}% ({source_weather})",
                "WCF": f"{wcf_val:.2f}x",
                "Decoupling": f"{decoupling*100:.1f}%",
                "SCORE": score_val, # Tengo numerico per ordinamento
                "Rank": rank_label
            })
            
        if results:
            df = pd.DataFrame(results)
            
            # KPI Ultima Corsa
            last_run = df.iloc[0]
            st.divider()
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ultimo SCORE", f"{last_run['SCORE']:.2f}")
            c2.metric("Livello", last_run['Rank'].split(" ")[1])
            c3.metric("WCF (Meteo)", last_run['WCF'], help="Moltiplicatore bonus per condizioni avverse")
            c4.metric("Dati Meteo", last_run['Meteo'])

            # Grafico
            st.subheader("Storico Analisi")
            chart_df = df.sort_values(by="Data")
            st.line_chart(chart_df.set_index('Data')[['SCORE']])
            
            # Tabella formattata
            st.dataframe(
                df.style.format({"SCORE": "{:.2f}"}), 
                use_container_width=True,
                hide_index=True
            )
            
        else:
            st.warning("Nessuna attività con dati di Potenza+FC trovata.")
    else:
        st.error("Impossibile autenticarsi con Strava.")
