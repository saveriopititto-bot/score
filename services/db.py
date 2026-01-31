from supabase import create_client, Client
import streamlit as st
import logging
from typing import Optional, Dict, List, Any, Tuple
from config import Config

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
                "wcf": run_data['WCF'],
                "wr_pct": run_data['WR_Pct'],
                "rank": run_data['Rank'],
                "rank": run_data['Rank'],
                "meteo_desc": run_data['Meteo'],
                "score_version": Config.ENGINE_VERSION,
                # Gaming Layer
                "quality": run_data.get("Quality", {}).get("label"),
                "achievements": run_data.get("Achievements", []),
                "trend": run_data.get("Trend", {}),
                "comparison": run_data.get("Comparison", {}),
                "raw_data": {
                    "watts": run_data['raw_watts'],
                    "hr": run_data['raw_hr'],
                    "details": run_data.get('SCORE_DETAIL', {})
                }
            }
            self.client.table("runs").upsert(payload).execute()
            return True
        except Exception as e:
            logger.error(f"Error DB Save Run: {e}")
            return False

    def run_exists(self, run_id: int) -> bool:
        try:
            res = self.client.table("runs").select("id").eq("id", run_id).execute()
            return bool(res.data)
        except Exception as e:
            logger.error(f"Error checking if run exists: {e}")
            return False

    def get_run_ids_for_athlete(self, athlete_id: int) -> List[int]:
        """Recupera tutti gli ID delle corse per un atleta specifico"""
        try:
            res = self.client.table("runs").select("id").eq("athlete_id", athlete_id).execute()
            return [row['id'] for row in res.data] if res.data else []
        except Exception as e:
            logger.error(f"Error getting run IDs for athlete: {e}")
            return []

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
                    "WCF": row.get('wcf', 1.0),
                    "WR_Pct": row.get('wr_pct', 0.0),
                    "Rank": row['rank'],
                    "Meteo": row['meteo_desc'],
                    "ai_feedback": row.get('ai_feedback'),
                    # Gaming Layer
                    "Quality": row.get("quality"),
                    "Achievements": row.get("achievements", []),
                    "Trend": row.get("trend", {}),
                    "Comparison": row.get("comparison", {}),
                    # Dati complessi
                    "SCORE_DETAIL": raw.get('details', {}),
                    "raw_watts": raw.get('watts', []),
                    "raw_hr": raw.get('hr', [])
                })
            return processed
        except Exception as e:
            logger.error(f"Error DB Get History: {e}")
            return []
            
    def reset_history(self, athlete_id: int) -> bool:
        """Cancella tutte le corse di un atleta per forzare un ricaricamento pulito."""
        try:
            self.client.table("runs").delete().eq("athlete_id", athlete_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error resetting history: {e}")
            return False

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

    # --- STREAK PERSISTENTE ---
    def update_streak(self, athlete_id: int):
        """Calcola e aggiorna la streak di miglioramento dell'atleta"""
        try:
            res = self.client.table("runs")\
                .select("score")\
                .eq("athlete_id", athlete_id)\
                .order("date", desc=True)\
                .limit(10).execute()

            scores = [r["score"] for r in res.data] if res.data else []
            streak = 1
            for i in range(1, len(scores)):
                if scores[i-1] >= scores[i]:
                    streak += 1
                else:
                    break

            self.client.table("athletes")\
                .update({"streak": streak})\
                .eq("id", athlete_id)\
                .execute()
        except Exception as e:
            logger.error(f"Error updating streak: {e}")

    # --- REPLAY & LOGS ---
    def save_replay(self, replay_data: Dict[str, Any]) -> bool:
        try:
            self.client.table("score_replay").insert(replay_data).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving replay: {e}")
            return False

    def log_achievement(self, log_data: Dict[str, Any]) -> bool:
        try:
            self.client.table("achievements_log").insert(log_data).execute()
            return True
        except Exception as e:
            logger.error(f"Error logging achievement: {e}")
            return False
