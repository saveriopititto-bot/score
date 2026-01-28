import google.generativeai as genai
import json
import requests
import time
from datetime import datetime, timedelta

class AICoachService:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API Key mancante")
        
        genai.configure(api_key=api_key)
        
        # Usiamo 'gemini-pro': è il modello più stabile e supportato ovunque.
        # Se in futuro vuoi usare flash, assicurati di avere google-generativeai aggiornato.
        self.model = genai.GenerativeModel('gemini-pro')

    def get_feedback(self, run_data, zones):
        """
        Genera un feedback testuale basato sui dati della corsa.
        """
        # Creiamo un prompt testuale pulito
        prompt = f"""
        Agisci come un allenatore di corsa d'élite (stile Jack Daniels o Joe Friel).
        Analizza questa sessione di allenamento e dammi un feedback breve, diretto e motivante (max 100 parole).
        Usa formattazione Markdown (grassetti, elenchi).

        DATI ATLETA:
        - Data: {run_data.get('Data')}
        - Distanza: {run_data.get('Dist (km)')} km
        - Tempo: {run_data.get('moving_time', 0) // 60} minuti
        - Passo Medio: {self._format_pace(run_data.get('moving_time', 0), run_data.get('Dist (km)'))} min/km
        - Potenza Media: {run_data.get('Power')} W
        - FC Media: {run_data.get('HR')} bpm
        - Disaccoppiamento Aerobico (Drift): {run_data.get('Decoupling')}% (Sopra il 5% indica fatica/inefficienza)
        - SCORE (Indice qualità): {run_data.get('SCORE')}
        - Livello: {run_data.get('Rank')}

        DISTRIBUZIONE ZONE (Importante):
        {json.dumps(zones, indent=2)}

        ANALISI RICHIESTA:
        1. Valuta se l'obiettivo (basato sulle zone) è stato centrato.
        2. Commenta il disaccoppiamento (è alto?).
        3. Dai un consiglio per la prossima volta.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ Errore del Coach AI: {str(e)}"

    def _format_pace(self, seconds, km):
        if km <= 0: return "0:00"
        pace_sec = seconds / km
        mins = int(pace_sec // 60)
        secs = int(pace_sec % 60)
        return f"{mins}:{secs:02d}"

# Servizio Meteo (Lasciamolo qui o in un file separato, ma per ora è comodo qui)
class WeatherService:
    @staticmethod
    def get_weather(lat, lon, date_str, hour):
        # Mock / Placeholder - Per ora restituisce dati standard
        # In futuro si può collegare a OpenMeteo API
        return 20.0, 50.0 # Temp, Humidity

# Servizio Strava (Scheletro per importazione)
class StravaService:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://www.strava.com/api/v3"
    
    def get_link(self, redirect_uri):
        return f"https://www.strava.com/oauth/authorize?client_id={self.client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope=activity:read_all"

    def get_token(self, code):
        res = requests.post("https://www.strava.com/oauth/token", data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code"
        })
        if res.status_code == 200:
            return res.json()
        return None

    def fetch_activities(self, token, days_back=365):
        """
        Scarica le attività degli ultimi X giorni (default 365).
        Gestisce la paginazione automatica.
        """
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Calcoliamo la data di partenza (Unix Timestamp)
        start_date = datetime.now() - timedelta(days=days_back)
        epoch_time = int(start_date.timestamp())
        
        all_activities = []
        page = 1
        keep_fetching = True
        
        # 2. Loop per scaricare la LISTA (Paginazione)
        while keep_fetching:
            # Scarichiamo 50 attività alla volta per pagina
            url = f"{self.base_url}/athlete/activities?after={epoch_time}&per_page=50&page={page}"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                break
                
            data = response.json()
            
            if not data: # Se la lista è vuota, abbiamo finito
                keep_fetching = False
            else:
                # Filtriamo solo le corse ('Run') subito per risparmiare tempo
                runs = [x for x in data if x['type'] == 'Run']
                all_activities.extend(runs)
                page += 1
                
        # 3. Ora scarichiamo i DETTAGLI (Streams) per ogni corsa trovata
        # Nota: Qui rischiamo il rate limit se ci sono >100 corse
        results = []
        
        # Per evitare blocchi totali, restituiamo una lista di oggetti "pronti da scaricare"
        # La fase di download pesante la faremo in app.py con la barra di progresso
        return all_activities

    def fetch_streams(self, token, activity_id):
        """
        Scarica i dati raw (Watt, HR) per una singola attività
        """
        headers = {"Authorization": f"Bearer {token}"}
        s_url = f"{self.base_url}/activities/{activity_id}/streams?keys=watts,heartrate&key_by_type=true"
        response = requests.get(s_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        return None
