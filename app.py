import streamlit as st
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="SCORE Run Analyzer",
    layout="centered"
)

# --- MOTORE DI CALCOLO ---
class ScoreAnalyzer:
    def __init__(self, weight=70.0):
        self.WEIGHT = weight
        self.W_REF_SPEC = 6.0       
        self.BPM_REST = 60.0        
        self.REF_PACE = 153.0       
        self.ALPHA = 0.8            

    def analyze(self, data, source_type="file"):
        try:
            hr_samples = []
            power_samples = []
            distance = 0
            duration = 0
            ascent = 0
            hr_max = 185
            date_str = datetime.now().isoformat()

            # --- LOGICA DI PARSING ---
            if source_type == "strava":
                streams = data.get('streams', {})
                summary = data.get('summary', {})
                
                distance = summary.get('distance', 0)
                duration = summary.get('moving_time', 0)
                ascent = summary.get('total_elevation_gain', 0)
                date_str = summary.get('start_date', date_str)
                
                if 'heartrate' in streams and 'watts' in streams:
                    hr_samples = streams['heartrate']['data']
                    power_samples = streams['watts']['data']
                else:
                    return None 
                    
            else:
                # Parsing File JSON
                header = data.get('DeviceLog', {}).get('Header', {})
                distance = header.get('Distance', 0)
                duration = header.get('Duration', 0)
                ascent = header.get('Ascent', 0)
                hr_max = header.get('HrMax', 185)
                date_str = header.get('DateTime', date_str)
                
                samples = data.get('DeviceLog', {}).get('Samples', [])
                for s in samples:
                    h = s.get('HR', s.get('HeartRate'))
                    p = s.get('Power')
                    if h is not None and p is not None:
                        if h < 10: h *= 60 
                        hr_samples.append(h)
                        power_samples.append(p)

            if not hr_samples or not power_samples:
                return None

            # --- CALCOLO SCORE ---
            avg_hr = np.mean(hr_samples)
            avg_power = np.mean(power_samples)
            
            # Decoupling
            half = len(power_samples) // 2
            if half > 10:
                p1 = np.mean(power_samples[:half])
                h1 = np.mean(hr_samples[:half])
                p2 = np.mean(power_samples[half:])
                h2 = np.mean(hr_samples[half:])
                ratio1 = p1/h1 if h1>0 else 0
                ratio2 = p2/h2 if h2>0 else 0
                decoupling = (ratio1 - ratio2) / ratio1
            else:
                decoupling = 0.05

            grade = ascent / distance if distance > 0 else 0
            w_adj = avg_power * (1 + grade)
            w_spec = w_adj / self.WEIGHT
            efficiency_term = w_spec / self.W_REF_SPEC
            
            hrr_percent = (avg_hr - self.BPM_REST) / (hr_max - self.BPM_REST)
            hrr_percent = max(0.01, hrr_percent)
            hrr_term = 1 / hrr_percent
            wcf = 1.0 
            t_ref = (distance / 1000.0) * self.REF_PACE
            p_factor = t_ref / duration
            t_hours = duration / 3600.0
            stability = np.exp(-self.ALPHA * abs(decoupling) / np.sqrt(max(0.1, t_hours)))
            
            final_score = (efficiency_term * hrr_term * wcf) * p_factor * stability

            return {
                "date": pd.to_datetime(date_str).replace(tzinfo=None),
                "score": final_score,
                "distance_km": distance / 1000.0,
                "duration_min": duration / 60.0,
                "decoupling": decoupling
            }
        except Exception as e:
            return None

# --- FUNZIONI STRAVA API ---
def get_strava_activities(client_id, client_secret, refresh_token, limit=5):
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    try:
        res = requests.post(auth_url, data=payload)
        if res.status_code != 200:
            st.error(f"Errore Auth Strava: {res.text}")
            return []
            
        access_token = res.json()['access_token']
        header = {'Authorization': f'Bearer {access_token}'}
        
        act_url = "https://www.strava.com/api/v3/athlete/activities"
        activities = requests.get(act_url, headers=header, params={'per_page': limit}).json()
        
        full_data = []
        my_bar = st.progress(0, text="Scaricamento dati da Strava...")
        
        for i, act in enumerate(activities):
            act_id = act['id']
            stream_url = f"https://www.strava.com/api/v3/activities/{act_id}/streams"
            streams = requests.get(stream_url, headers=header, params={'keys': 'watts,heartrate', 'key_by_type': 'true'}).json()
            
            full_data.append({
                "summary": act,
                "streams": streams
            })
            my_bar.progress((i + 1) / limit)
            
        my_bar.empty()
        return full_data
    except Exception as e:
        st.error(f"Errore connessione: {e}")
        return []

# --- INTERFACCIA ---
st.title("🏃‍♂️ SCORE Run Analyzer")

# Inizializza le variabili per evitare NameError
client_id = None
client_secret = None
refresh_token = None
run_strava = False # Variabile pulsante

with st.sidebar:
    st.header("Impostazioni")
    weight = st.number_input("Peso (kg)", 70.0)
    analyzer = ScoreAnalyzer(weight=weight)
    
    st.divider()
    st.subheader("🔌 Connessione Strava")
    
    # 1. Tenta di caricare dai Secrets
    if 'strava' in st.secrets:
        client_id = st.secrets['strava']['client_id']
        client_secret = st.secrets['strava']['client_secret']
        refresh_token = st.secrets['strava']['refresh_token']
        st.success("🔒 Chiavi caricate dai Secrets!")
    else:
        # 2. Altrimenti chiedi input manuale
        client_id = st.text_input("Client ID")
        client_secret = st.text_input("Client Secret", type="password")
        refresh_token = st.text_input("Refresh Token", type="password")
    
    # IL PULSANTE È QUI (Sempre visibile)
    run_strava = st.button("Scarica da Strava")

# Main Logic
results = []

# A. FLUSSO STRAVA
if run_strava:
    if client_id and refresh_token:
        strava_data = get_strava_activities(client_id, client_secret, refresh_token)
        if strava_data:
            for d in strava_data:
                res = analyzer.analyze(d, source_type="strava")
                if res: results.append(res)
    else:
        st.error("Mancano le chiavi Strava (Client ID o Token).")

# B. FLUSSO FILE MANUALE
uploaded_files = st.file_uploader("Oppure carica file JSON", accept_multiple_files=True)
if uploaded_files:
    for f in uploaded_files:
        content = json.load(f)
        res = analyzer.analyze(content, source_type="file")
        if res: results.append(res)

# VISUALIZZAZIONE RISULTATI
if results:
    df = pd.DataFrame(results).sort_values(by='date')
    
    # Ultima Corsa
    last = df.iloc[-1]
    st.divider()
    st.subheader(f"Ultima Analisi: {last['date'].strftime('%d %b %Y')}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("SCORE 4.0", f"{last['score']:.2f}")
    with col2:
        st.caption("Feedback Rapido")
        if last['score'] < 0.25: st.info("🛠 Recupero / Base")
        elif last['score'] < 0.5: st.success("📈 Mantenimento")
        elif last['score'] < 1.0: st.warning("🚀 Performance Alta")
        else: st.error("🏆 Élite")

    # Grafico
    st.subheader("Trend Temporale")
    if len(df) > 1:
        st.line_chart(df.set_index('date')['score'])
    else:
        st.info("Carica più attività per vedere il grafico del trend.")
    
    with st.expander("Vedi Dati Grezzi"):
        st.dataframe(df)
else:
    if not run_strava:
        st.info("👈 Usa la barra laterale per connetterti a Strava o carica un file JSON qui sopra.")
