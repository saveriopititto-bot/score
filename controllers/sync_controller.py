import time
from datetime import datetime
from config import Config
from engine.core import ScoreEngine, RunMetrics
from services.api import WeatherService

class SyncController:
    def __init__(self, auth_svc, db_svc):
        self.auth = auth_svc
        self.db = db_svc
        self.engine = ScoreEngine()

    def run_sync(self, token, athlete_id, physical_params, days_back, existing_ids, history_scores, progress_bar=None, last_import_timestamp=None):
        """
        Esegue la sync. Ritona (count_new, message).
        history_scores: lista di float degli score precedenti (per calcolo gaming)
        """
        weight = physical_params.get('weight', Config.DEFAULT_WEIGHT)
        hr_max = physical_params.get('hr_max', Config.DEFAULT_HR_MAX)
        hr_rest = physical_params.get('hr_rest', Config.DEFAULT_HR_REST)
        age = physical_params.get('age', Config.DEFAULT_AGE)
        sex = physical_params.get('sex', 'M')

        # --- 1. FETCH SEMPLIFICATO (SOLUZIONE DEFINITIVA) ---
        activities_list = self.auth.fetch_all_activities_simple(token)
        
        # Debug Temporaneo
        if progress_bar:
             import streamlit as st
             st.write(f"Strava activities fetched: {len(activities_list)}")
        
        if not activities_list:
             return -1, "Nessuna attività trovata"

        # FIX ORDER: Strava returns Newest-First. We need Oldest-First for Gaming History.
        activities_list.sort(key=lambda x: x['start_date_local'])

        count_new = 0
        total = len(activities_list)
        
        # Local copy of history
        current_history = list(history_scores)

        # FIX TYPE MISMATCH: Ensure all are strings
        existing_ids_str = set(str(eid) for eid in existing_ids)
        
        # Cutoff Date (Filtro post-fetch)
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days_back)

        for i, s in enumerate(activities_list):
            if progress_bar:
                progress_bar.progress((i + 1) / total)
            
            # --- FILTRI STRAVA ---
            # Date Filter
            try:
                dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                if dt < cutoff:
                    continue
            except:
                continue # Skip invalid dates

            # Robust string ID check
            if str(s['id']) in existing_ids_str: 
                continue 
            
            # DB Double check
            if self.db.run_exists(s["id"]):
                continue

            streams = self.auth.fetch_streams(token, s['id'])

            if not streams:
                continue

            if len(streams.get("watts", {}).get("data", [])) < 300:
                continue

            if len(streams.get("heartrate", {}).get("data", [])) < 300:
                continue

            if streams and 'watts' in streams and 'heartrate' in streams:
                dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                
                # Meteo
                t, h = 20.0, 50.0 
                if s.get('start_latlng'):
                        t, h = WeatherService.get_weather(s['start_latlng'][0], s['start_latlng'][1], dt.strftime("%Y-%m-%d"), dt.hour)
                
                # Metriche
                # Metriche Base
                avg_watts = s.get('average_watts', 0)
                
                # FALLBACK: Se 0 watt ma esiste lo stream, calcoliamo la media
                if avg_watts == 0 and streams.get('watts', {}).get('data'):
                    import numpy as np
                    avg_watts = np.mean(streams['watts']['data'])

                m = RunMetrics(
                    avg_watts, 
                    s.get('average_heartrate', 0), 
                    s.get('distance', 0), 
                    s.get('moving_time', 0), 
                    s.get('total_elevation_gain', 0), 
                    weight, hr_max, hr_rest, t, h, age, sex
                )
                
                # Engine Calc
                dec = self.engine.calculate_decoupling(streams['watts']['data'], streams['heartrate']['data'])
                score, details, wcf, wr_pct, quality = self.engine.compute_score(m, dec)
                rnk, _ = self.engine.get_rank(score)
                
                # Gaming Layer
                current_history.append(score)
                gaming = self.engine.gaming_feedback(current_history)

                run_obj = {
                    "id": s['id'], 
                    "Data": dt.strftime("%Y-%m-%d"), 
                    "Dist (km)": round(m.distance_meters/1000, 2),
                    "Power": int(m.avg_power), 
                    "HR": int(m.avg_hr), 
                    "Decoupling": round(dec*100, 1), 
                    "SCORE": round(score, 2), 
                    "WCF": round(wcf, 2), 
                    "WR_Pct": round(wr_pct, 1),
                    "Rank": rnk, 
                    "Meteo": f"{t}°C", 
                    "SCORE_DETAIL": details,
                    "raw_watts": streams['watts']['data'], 
                    "raw_hr": streams['heartrate']['data'],
                    
                    # Gaming Layer properties
                    "Quality": gaming["quality"],
                    "Achievements": gaming["achievements"],
                    "Trend": gaming["trend"],
                    "Comparison": gaming["comparison"]
                }
                
                if self.db.save_run(run_obj, athlete_id): 
                    count_new += 1
            
            time.sleep(0.1) # Rate limit

        if count_new > 0:
            self.db.update_streak(athlete_id)
        
        return count_new, f"Archiviate {count_new} nuove attività!"
