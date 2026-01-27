import streamlit as st
import numpy as np
import pandas as pd
import requests
import altair as alt
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="SCORE 4.0 Pro",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. DOMAIN LAYER: ENTITIES & ENGINE
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
    """
    Motore di calcolo SCORE 4.0 con Benchmark Riegel (World Record).
    """
    W_REF_SPEC = 6.0        # W/kg Elite Reference
    ALPHA = 0.8             # Sensibilità deriva aerobica
    
    # Parametri Riegel calibrati su WR Maratona (~2h00m35s per 42195m)
    # Formula: T_ref = T_base * (Dist / Dist_base) ^ 1.06
    WR_BASE_DIST = 42195.0
    WR_BASE_TIME = 7235.0   # Secondi
    RIEGEL_EXP = 1.06

    @staticmethod
    def get_world_record_time(distance_meters: float) -> float:
        """Calcola il tempo teorico WR per una data distanza usando Riegel."""
        if distance_meters <= 0: return 1.0
        return ScoreEngine.WR_BASE_TIME * (distance_meters / ScoreEngine.WR_BASE_DIST) ** ScoreEngine.RIEGEL_EXP

    @staticmethod
    def calculate_decoupling(power_stream: list, hr_stream: list) -> float:
        """Calcola il disaccoppiamento aerobico (Pw:Hr)."""
        if not power_stream or not hr_stream or len(power_stream) != len(hr_stream):
            return 0.0
        
        half = len(power_stream) // 2
        if half < 60: return 0.0  # Troppo breve

        p1 = np.mean(power_stream[:half])
        h1 = np.mean(hr_stream[:half])
        p2 = np.mean(power_stream[half:])
        h2 = np.mean(hr_stream[half:])

        if h1 == 0 or h2 == 0: return 0.0

        ratio1 = p1 / h1
        ratio2 = p2 / h2
        
        # Decoupling = (Ratio1 - Ratio2) / Ratio1
        return (ratio1 - ratio2) / ratio1

    def compute_score(self, metrics: RunMetrics, decoupling: float) -> Tuple[float, float, float]:
        """
        Ritorna: (SCORE, WCF, WR_Percent)
        """
        # 1. Potenza Normalizzata (Correzione Ascesa)
        grade = metrics.ascent_meters / metrics.distance_meters if metrics.distance_meters > 0 else 0
        w_adj = metrics.avg_power * (1 + grade)

        # 2. Efficienza Normalizzata (vs 6.0 W/kg)
        w_spec = w_adj / metrics.weight_kg
        term_efficiency = w_spec / self.W_REF_SPEC

        # 3. Costo Cardiaco (HRR)
        hrr_percent = (metrics.avg_hr - metrics.hr_rest) / (metrics.hr_max - metrics.hr_rest)
        hrr_percent = max(0.05, hrr_percent) # Clamp minimo
        term_hrr = 1 / hrr_percent

        # 4. Weather Correction Factor (WCF)
        # Premia chi corre al caldo o con alta umidità
        term_weather = 1.0 + \
                       max(0, 0.012 * (metrics.temp_c - 20)) + \
                       max(0, 0.005 * (metrics.humidity - 60))

        # 5. Performance Factor Dinamico (vs World Record)
        t_wr_seconds = self.get_world_record_time(metrics.distance_meters)
        term_p = t_wr_seconds / max(1, metrics.duration_seconds)

        # 6. Stabilità Cardiovascolare
        t_hours = metrics.duration_seconds / 3600.0
        term_stability = np.exp(-self.ALPHA * abs(decoupling) / np.sqrt(max(0.1, t_hours)))

        # Formula Finale
        score = (term_efficiency * term_hrr * term_weather) * term_p * term_stability
        
        # Calcolo percentuale rispetto al WR (per statistiche)
        wr_percent = term_p * 100 

        return score, term_weather, wr_percent

    @staticmethod
    def get_rank(score: float) -> Tuple[str, str]:
        if score >= 4.0: return "🏆 Classe Mondiale", "success"
        if score >= 3.0: return "🥇 Livello Nazionale", "success"
        if score >= 2.0: return "🥈 Livello Regionale", "warning"
        if score >= 1.0: return "🥉 Runner Avanzato", "info"
        return "👟 Amatore / Recupero", "secondary"

# ==========================================
# 2. INFRASTRUCTURE LAYER: SERVICES
# ==========================================

class WeatherService:
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    @staticmethod
    @st.cache_data(ttl=86400, show_spinner=False)
    def get_historical_weather(lat: float, lon: float, date_str: str, hour: int) -> Tuple[Optional[float], Optional[float]]:
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": date_str,
                "end_date": date_str,
                "hourly": "temperature_2m,relative_humidity_2m",
                "timezone": "auto"
            }
            res = requests.get(WeatherService.BASE_URL, params=params)
            res.raise_for_status()
            data = res.json()
            idx = min(hour, 23)
            temp = data['hourly']['temperature_2m'][idx]
            hum = data['hourly']['relative_humidity_2m'][idx]
            return temp, hum
        except Exception as e:
            return None, None

class StravaService:
    AUTH_URL = "https://www.strava.com/oauth/authorize"
    TOKEN_URL = "https://www.strava.com/oauth/token"
    API_URL = "https://www.strava.com/api/v3"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_link(self, redirect_uri: str) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "approval_prompt": "force",
            "scope": "activity:read_all,profile:read_all"
        }
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}?{query}"

    def exchange_code_for_token(self, code: str) -> dict:
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        try:
            res = requests.post(self.TOKEN_URL, data=payload)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            st.error(f"Errore Auth: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> str:
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        try:
            res = requests.post(self.TOKEN_URL, data=payload)
            res.raise_for_status()
            return res.json().get("access_token")
        except Exception:
            return None

    def get_activities(self, access_token: str, limit: int = 5) -> list:
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            # 1. Fetch Summary
            act_res = requests.get(
                f"{self.API_URL}/athlete/activities", 
                headers=headers, 
                params={'per_page': limit}
            )
            if act_res.status_code == 401: return None # Token scaduto
            
            activities = act_res.json()
            full_data = []
            
            # Progress Bar
            prog_bar = st.progress(0, text="Scaricamento flussi dati...")
            
            for i, act in enumerate(activities):
                # Filtro: Solo corse con misuratore di potenza (o stima Strava)
                if act.get('type') == 'Run': # Opzionale: and act.get('device_watts', False):
                    act_id = act['id']
                    streams = requests.get(
                        f"{self.API_URL}/activities/{act_id}/streams",
                        headers=headers,
                        params={'keys': 'watts,heartrate', 'key_by_type': 'true'}
                    ).json()
                    
                    if 'watts' in streams and 'heartrate' in streams:
                        full_data.append({'summary': act, 'streams': streams})
                
                prog_bar.progress((i + 1) / limit)
            
            prog_bar.empty()
            return full_data
        except Exception as e:
            st.error(f"Errore API Strava: {e}")
            return []

# ==========================================
# 3. PRESENTATION LAYER: UI & LOGIC
# ==========================================

# Gestione Session State
if "strava_token" not in st.session_state:
    st.session_state.strava_token = None

st.title("🏃‍♂️ SCORE 4.0 Analysis")
st.markdown("Metrics for Bio-Mechanical Efficiency & Competitive Ranking")

# --- SIDEBAR: CONFIGURAZIONE & AUTH ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    
    # Credenziali (Caricamento sicuro o Manuale)
    # Hint: Usa .streamlit/secrets.toml in produzione
    def_cid = st.secrets.get("strava", {}).get("client_id", "")
    def_csec = st.secrets.get("strava", {}).get("client_secret", "")
    
    c_id = st.text_input("Client ID", value=def_cid)
    c_sec = st.text_input("Client Secret", value=def_csec, type="password")
    
    auth_svc = StravaService(c_id, c_sec)
    
    st.divider()
    
    # Gestione Connessione
    if st.session_state.strava_token:
        st.success("✅ Strava Connesso")
        if st.button("Disconnetti", use_container_width=True):
            st.session_state.strava_token = None
            st.rerun()
    else:
        st.info("Connetti il tuo account per analizzare le attività.")
        if c_id and c_sec:
            redirect_uri = "https://scorerun.streamlit.app/" 
            link = auth_svc.get_authorization_link(redirect_uri)
            st.link_button("🔗 Connetti a Strava", link, type="primary", use_container_width=True)
        else:
            st.warning("Inserisci le credenziali Strava.")

    st.divider()
    st.header("👤 Profilo Atleta")
    weight = st.number_input("Peso (kg)", 70.0, step=0.5)
    hr_max = st.number_input("FC Max", 185)
    hr_rest = st.number_input("FC Riposo", 50)

# --- MAIN: AUTH CALLBACK HANDLER ---
# Gestisce il ritorno da Strava (es. localhost:8501/?code=...)
if "code" in st.query_params and not st.session_state.strava_token:
    code = st.query_params["code"]
    with st.spinner("Autenticazione in corso..."):
        tokens = auth_svc.exchange_code_for_token(code)
        if tokens:
            st.session_state.strava_token = tokens
            st.success("Login effettuato!")
            st.query_params.clear() # Pulisce l'URL
            st.rerun()
        else:
            st.error("Login fallito.")

# --- MAIN: ANALISI DATI ---
if st.session_state.strava_token:
    if st.button("🚀 Analizza le mie corse", type="primary"):
        weather_svc = WeatherService()
        engine = ScoreEngine()
        
        # 1. Fetch Dati
        token_dict = st.session_state.strava_token
        access_token = token_dict["access_token"]
        
        raw_data = auth_svc.get_activities(access_token, limit=10)
        
        # Gestione Token Scaduto
        if raw_data is None: 
            new_access = auth_svc.refresh_access_token(token_dict["refresh_token"])
            if new_access:
                st.session_state.strava_token["access_token"] = new_access
                raw_data = auth_svc.get_activities(new_access, limit=10)
            else:
                st.error("Sessione scaduta. Riconnettiti.")
                st.stop()

        results = []
        
        # 2. Elaborazione
        if raw_data:
            for d in raw_data:
                summary = d['summary']
                streams = d['streams']
                
                # Parsing Date/Time
                start_date = summary['start_date_local']
                dt_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
                date_str = dt_obj.strftime("%Y-%m-%d")
                
                # Meteo Logic
                lat_lng = summary.get('start_latlng', [])
                temp, hum = 20.0, 50.0 # Defaults
                source_weather = "Default"
                
                if lat_lng:
                    api_t, api_h = weather_svc.get_historical_weather(lat_lng[0], lat_lng[1], date_str, dt_obj.hour)
                    if api_t is not None:
                        temp, hum = api_t, api_h
                        source_weather = "API 🌤"

                # Costruzione Metriche
                metrics = RunMetrics(
                    avg_power=summary.get('average_watts', 0),
                    avg_hr=summary.get('average_heartrate', 0),
                    distance_meters=summary.get('distance', 0),
                    duration_seconds=summary.get('moving_time', 0),
                    ascent_meters=summary.get('total_elevation_gain', 0),
                    weight_kg=weight,
                    hr_max=hr_max,
                    hr_rest=hr_rest,
                    temp_c=temp,
                    humidity=hum
                )
                
                # Calcolo Motore
                decoupling = engine.calculate_decoupling(streams['watts']['data'], streams['heartrate']['data'])
                score, wcf, wr_pct = engine.compute_score(metrics, decoupling)
                rank_lbl, rank_col = engine.get_rank(score)
                
                results.append({
                    "Data": date_str,
                    "Dist (km)": float(f"{metrics.distance_meters/1000:.2f}"),
                    "Dist_Raw": metrics.distance_meters, # Nascosto, per calcoli
                    "Speed_kmh": (metrics.distance_meters/1000) / (metrics.duration_seconds/3600),
                    "Power": int(metrics.avg_power),
                    "HR": int(metrics.avg_hr),
                    "Decoupling": float(f"{decoupling*100:.1f}"),
                    "WCF": float(f"{wcf:.2f}"),
                    "SCORE": float(f"{score:.2f}"),
                    "WR_Pct": float(f"{wr_pct:.1f}"),
                    "Rank": rank_lbl
                })

        # 3. Visualizzazione
        if results:
            df = pd.DataFrame(results).sort_values(by="Data", ascending=False)
            
            # --- KPI ULTIMA CORSA ---
            last = df.iloc[0]
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ultimo SCORE", f"{last['SCORE']}", delta=last['Rank'].split(" ")[0])
            c2.metric("Livello WR", f"{last['WR_Pct']}%", help="% Velocità rispetto al Record del Mondo")
            c3.metric("WCF (Meteo)", f"{last['WCF']}x", help="Bonus meteo applicato")
            c4.metric("Disaccoppiamento", f"{last['Decoupling']}%", delta_color="inverse")

            # --- ANALISI COMPARATIVA (RIEGEL) ---
            st.markdown("### 🌍 Analisi Benchmark vs World Record")
            
            median_wr = df['WR_Pct'].median()
            st.caption(f"La tua mediana globale è il **{median_wr:.1f}%** del passo World Record.")

            # Creazione Grafico Curva WR
            x_vals = np.linspace(1000, 50000, 100) # Da 1km a 50km
            # Calcolo velocità WR (km/h) per ogni distanza
            y_wr_kmh = [(d/1000) / (engine.get_world_record_time(d)/3600) for d in x_vals]
            
            # DataFrame Curva WR
            wr_df = pd.DataFrame({
                'Dist (km)': x_vals/1000,
                'Speed (km/h)': y_wr_kmh,
                'Tipo': 'World Record 🌍'
            })
            
            # DataFrame Utente
            user_df = df[['Dist (km)', 'Speed_kmh']].copy()
            user_df['Tipo'] = 'Le tue Corse 🏃'
            user_df.rename(columns={'Speed_kmh': 'Speed (km/h)'}, inplace=True)
            
            # Merge per Altair
            chart_data = pd.concat([wr_df, user_df], ignore_index=True)
            
            # Grafico
            chart = alt.Chart(chart_data).mark_line(point=True).encode(
                x=alt.X('Dist (km)', scale=alt.Scale(domain=[0, 50])),
                y=alt.Y('Speed (km/h)', scale=alt.Scale(zero=False)),
                color=alt.Color('Tipo', scale=alt.Scale(domain=['World Record 🌍', 'Le tue Corse 🏃'], range=['#FF4B4B', '#1F77B4'])),
                tooltip=['Dist (km)', 'Speed (km/h)', 'Tipo']
            ).properties(height=350, title="Curva Fatiga/Velocità").interactive()
            
            st.altair_chart(chart, use_container_width=True)

            # --- TABELLA DATI ---
            st.markdown("### 📝 Storico Dettagliato")
            st.dataframe(
                df[['Data', 'Dist (km)', 'Power', 'HR', 'Decoupling', 'WCF', 'WR_Pct', 'SCORE', 'Rank']],
                use_container_width=True,
                hide_index=True
            )
            
        else:
            st.warning("Nessuna corsa valida trovata (verifica che ci siano dati di Potenza e FC).")

else:
    # Landing Page State
    st.markdown("""
    <div style='text-align: center; margin-top: 50px;'>
        <h2>Benvenuto in SCORE 4.0</h2>
        <p>Connetti il tuo account Strava per accedere all'analisi professionale.</p>
    </div>
    """, unsafe_allow_html=True)
