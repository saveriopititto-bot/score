from supabase import create_client, Client
import streamlit as st
import logging
from typing import Optional, Dict, List, Any, Tuple

# Setup Logger
logger = logging.getLogger("sCore.DB")

class DatabaseService:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    # --- GESTIONE PROFILO ---
    def save_athlete_profile(self, profile_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        try:
            self.client.table("athletes").upsert(profile_data).execute()
            return True, None 
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            return False, str(e)

    def get_athlete_profile(self, athlete_id: int) -> Optional[Dict[str, Any]]:
        try:
            res = self.client.table("athletes").select("*").eq("id", athlete_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            logger.error(f"Error reading profile: {e}")
            return None

    # --- GESTIONE CORSE (RUNS) ---
    def save_run(self, run_data: Dict[str, Any], athlete_id: int) -> bool:
        """Salva una corsa mappando i dati Python -> SQL Supabase"""
        try:
            # MAPPATURA: Chiavi App -> Colonne SQL
            payload = {
                "id": run_data['id'],
                "athlete_id": athlete_id,
                "date": run_data['Data'],             
                "distance_km": run_data['Dist (km)'],
                "duration_sec": len(run_data.get('raw_watts', [])) if run_data.get('raw_watts') else 0,
                "avg_power": run_data['Power'],
                "avg_hr": run_data['HR'],
                "decoupling": run_data['Decoupling'],
                "score": run_data['SCORE'],
                "wcf": run_data['WCF'],       # <--- NUOVO 4.1
                "wr_pct": run_data['WR_Pct'], # <--- NUOVO 4.1
                "rank": run_data['Rank'],
                "meteo_desc": run_data['Meteo'],
                "raw_data": {
                    "watts": run_data['raw_watts'],
                    "hr": run_data['raw_hr'],
                    "details": run_data.get('SCORE_DETAIL', {}) # Salviamo i dettagli nel JSON
                }
            }
            self.client.table("runs").upsert(payload).execute()
            return True
        except Exception as e:
            logger.error(f"Error DB Save Run: {e}")
            return False

    def get_history(self) -> List[Dict[str, Any]]:
        """Carica lo storico mappando SQL Supabase -> Dati Python"""
        try:
            response = self.client.table("runs").select("*").order("date", desc=True).execute()
            data = response.data if response.data else []
            
            processed = []
            for row in data:
                # Estrazione sicura dal JSON raw_data
                raw = row.get('raw_data', {}) or {}
                
                # MAPPATURA INVERSA: Colonne SQL -> Chiavi App
                processed.append({
                    "id": row['id'],
                    "Data": row['date'],
                    "Dist (km)": row['distance_km'],
                    "Power": row['avg_power'],
                    "HR": row['avg_hr'],
                    "Decoupling": row['decoupling'],
                    "SCORE": row['score'],
                    "WCF": row.get('wcf', 1.0),       # <--- Fondamentale
                    "WR_Pct": row.get('wr_pct', 0.0), # <--- Fondamentale
                    "Rank": row['rank'],
                    "Meteo": row['meteo_desc'],
                    "ai_feedback": row.get('ai_feedback'),
                    # Dati complessi
                    "SCORE_DETAIL": raw.get('details', {}),
                    "raw_watts": raw.get('watts', []),
                    "raw_hr": raw.get('hr', [])
                })
            return processed
        except Exception as e:
            logger.error(f"Error DB Get History: {e}")
            return []

    def update_ai_feedback(self, run_id: int, feedback_text: str) -> bool:
        try:
            self.client.table("runs").update({"ai_feedback": feedback_text}).eq("id", run_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating feedback: {e}")
            return False
    
    def save_feedback(self, feedback_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        try:
            self.client.table("feedback").insert(feedback_data).execute()
            return True, None
        except Exception as e:
            logger.error(f"Error saving user feedback: {e}")
            return False, str(e)

