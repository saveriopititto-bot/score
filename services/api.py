import google.generativeai as genai
import json
import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from config import Config

# Setup Logger
logger = logging.getLogger("sCore.API")

class AICoachService:
    def __init__(self, api_key: str):
        if not api_key:
            # Non bloccante se manca la chiave, ma il metodo fallirà elegantemente
            self.model = None
            logger.warning("Gemini API Key missing")
            return
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def get_feedback(self, run_data: Dict[str, Any], zones: Dict[str, float]) -> str:
        if not self.model: return "⚠️ API Key Gemini mancante."
        
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
            logger.error(f"Gemini API Error: {e}")
            return f"⚠️ Errore del Coach AI: {str(e)}"

    def _format_pace(self, seconds: float, km: float) -> str:
        if km <= 0: return "0:00"
        pace_sec = seconds / km
        mins = int(pace_sec // 60)
        secs = int(pace_sec % 60)
        return f"{mins}:{secs:02d}"

class WeatherService:
    BASE_URL = Config.OPEN_METEO_URL

    @staticmethod
    def get_weather(lat: float, lon: float, date_str: str, hour: int) -> Tuple[float, float]:
        """
        Recupera Meteo REALE storico da Open-Meteo.
        """
        try:
            # Open-Meteo richiede start_date e end_date
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": date_str,
                "end_date": date_str,
                "hourly": "temperature_2m,relative_humidity_2m"
            }
            res = requests.get(WeatherService.BASE_URL, params=params, timeout=5)
            
            if res.status_code == 200:
                data = res.json()
                if "hourly" in data:
                    # Troviamo l'indice dell'ora richiesta (0-23)
                    idx = min(hour, 23)
                    temp = data["hourly"]["temperature_2m"][idx]
                    hum = data["hourly"]["relative_humidity_2m"][idx]
                    return float(temp), float(hum)
            
            # Fallback in caso di risposta strana
            logger.warning(f"Weather API returned {res.status_code}")
            return 20.0, 50.0
            
        except Exception as e:
            logger.error(f"WeatherService Error: {e}")
            return 20.0, 50.0 # Fallback Safe


class StravaService:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = Config.STRAVA_BASE_URL
    
    def get_link(self, redirect_uri: str) -> str:
        # NOTA: Aggiunto 'profile:read_all' per leggere Peso e Zone Cardiache
        scope = "activity:read_all,profile:read_all"
        return f"https://www.strava.com/oauth/authorize?client_id={self.client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope={scope}"

    def fetch_all_activities_simple(self, token, per_page=50, max_pages=20):
        """
        Fetch robusto: prende TUTTE le attività disponibili tramite paginazione.
        Non usa days_back (Strava non è affidabile su filtri temporali).
        """
        headers = {"Authorization": f"Bearer {token}"}
        all_activities = []

        for page in range(1, max_pages + 1):
            res = requests.get(
                f"{self.base_url}/athlete/activities",
                headers=headers,
                params={
                    "per_page": per_page,
                    "page": page
                },
                timeout=20
            )
            # Safe parsing
            if res.status_code != 200:
                logger.error(f"Strava API Error (Simple Fetch): {res.text}")
                break
                
            acts = res.json()

            if not acts:
                break

            all_activities.extend(acts)
            
            # Simple rate limit prevention
            time.sleep(0.5)

        return all_activities

    def get_token(self, code: str) -> Optional[Dict[str, Any]]:
        try:
            res = requests.post("https://www.strava.com/oauth/token", data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code"
            }, timeout=10)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            logger.error(f"Strava Token Error: {e}")
            pass
        return None

    def _request_with_retry(self, method: str, url: str, headers: Dict[str, str]=None, params: Dict[str, Any]=None, max_retries: int=3) -> Optional[Any]:
        """Wrapper con gestione Rate Limit e Retries"""
        for i in range(max_retries):
            try:
                res = requests.request(method, url, headers=headers, params=params, timeout=10)
                
                if res.status_code == 200:
                    # Capture Rate Limit Headers (Dev Console)
                    try:
                        import streamlit as st
                        if "X-ReadRec-Usage" in res.headers:
                            if "rate_limit_headers" not in st.session_state: st.session_state.rate_limit_headers = {}
                            st.session_state.rate_limit_headers = dict(res.headers)
                    except: 
                        pass
                        
                    return res.json()
                
                if res.status_code == 429:
                    # Rate Limit
                    logger.warning(f"Strava Rate Limit Hit! Waiting... (Attempt {i+1})")
                    time.sleep(10 * (i+1)) # Backoff aggressivo
                    continue
                
                # Altri errori (401, 500)
                logger.error(f"Strava API Error {res.status_code}: {res.text}")
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Network Error: {e}")
                time.sleep(2)
        
        return None

    def fetch_activities(self, token: str, days_back: int=365, after_timestamp: int=None) -> List[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        
        if after_timestamp:
            epoch_time = after_timestamp
        else:
            start_date = datetime.now() - timedelta(days=days_back)
            epoch_time = int(start_date.timestamp())
        
        all_activities = []
        page = 1
        
        while True:
            # FIX PAGINAZIONE: Loop infinito finché Strava restituisce dati
            url = f"{self.base_url}/athlete/activities?after={epoch_time}&per_page=50&page={page}"
            data = self._request_with_retry("GET", url, headers=headers)
            
            if not data: 
                break # Fine o Errore
            
            runs = [x for x in data if x.get('type') == 'Run']
            all_activities.extend(runs)
            
            # Se riceviamo meno di 50 elementi, è l'ultima pagina.
            if len(data) < 50: 
                break 
                
            page += 1
            
        return all_activities

    def fetch_streams(self, token: str, activity_id: int) -> Optional[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/activities/{activity_id}/streams?keys=watts,heartrate&key_by_type=true"
        return self._request_with_retry("GET", url, headers=headers)

    # --- NUOVO METODO AGGIUNTO ---
    def fetch_zones(self, token: str) -> Optional[Dict[str, Any]]:
        """Scarica le zone cardiache dell'atleta per trovare la FC Max reale"""
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/athlete/zones"
        return self._request_with_retry("GET", url, headers=headers)
