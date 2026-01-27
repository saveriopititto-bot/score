import requests
import streamlit as st
import google.generativeai as genai
from typing import Optional

class AICoachService:
    def __init__(self, api_key):
        self.model = None
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def get_feedback(self, data):
        if not self.model: return "⚠️ API Key mancante."
        prompt = f"""
        Analizza questa corsa (SCORE 4.0) come un coach esperto.
        Dati: {data}
        Fornisci: 1. Analisi Efficienza, 2. Gestione Sforzo, 3. Consiglio Pratico.
        Usa Markdown. Sii breve.
        """
        try:
            return self.model.generate_content(prompt).text
        except Exception as e:
            return f"Errore AI: {e}"

class WeatherService:
    URL = "https://archive-api.open-meteo.com/v1/archive"
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_weather(lat, lon, date_str, hour):
        try:
            p = {"latitude": lat, "longitude": lon, "start_date": date_str, "end_date": date_str, "hourly": "temperature_2m,relative_humidity_2m"}
            res = requests.get(WeatherService.URL, params=p).json()
            idx = min(hour, 23)
            return res['hourly']['temperature_2m'][idx], res['hourly']['relative_humidity_2m'][idx]
        except: return None, None

class StravaService:
    AUTH = "https://www.strava.com/oauth/authorize"
    TOKEN = "https://www.strava.com/oauth/token"
    API = "https://www.strava.com/api/v3"
    
    def __init__(self, cid, csec): self.cid, self.csec = cid, csec
    
    def get_link(self, redirect):
        return f"{self.AUTH}?client_id={self.cid}&response_type=code&redirect_uri={redirect}&scope=activity:read_all"
    
    def get_token(self, code):
        r = requests.post(self.TOKEN, data={"client_id": self.cid, "client_secret": self.csec, "code": code, "grant_type": "authorization_code"})
        return r.json() if r.ok else None
        
    def fetch_activities(self, token, limit=5):
        try:
            acts = requests.get(f"{self.API}/athlete/activities", headers={'Authorization': f'Bearer {token}'}, params={'per_page': limit}).json()
            data = []
            for a in acts:
                if a.get('type') == 'Run':
                    s = requests.get(f"{self.API}/activities/{a['id']}/streams", headers={'Authorization': f'Bearer {token}'}, params={'keys': 'watts,heartrate,time', 'key_by_type': 'true'}).json()
                    if 'watts' in s and 'heartrate' in s: data.append({'summary': a, 'streams': s})
            return data
        except: return []
