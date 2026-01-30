from supabase import create_client, Client
import streamlit as st

class DatabaseService:
    def __init__(self, url: str, key: str):
        # Usiamo self.client per coerenza con il resto del codice
        self.client: Client = create_client(url, key)

    def save_athlete_profile(self, profile_data):
        """
        Salva o aggiorna (Upsert) i dati dell'atleta.
        RITORNA DUE VALORI: (Successo, MessaggioErrore)
        """
        try:
            # Upsert: se l'ID esiste aggiorna, se no crea
            data, count = self.client.table("athletes").upsert(profile_data).execute()
            
            # ✅ RITORNA COPPIA: (True, None)
            return True, None 
            
        except Exception as e:
            print(f"⚠️ Errore salvataggio profilo: {e}")
            # ❌ RITORNA COPPIA: (False, Errore)
            return False, str(e)

    def get_athlete_profile(self, athlete_id):
        """Recupera i dati salvati dell'atleta"""
        try:
            res = self.client.table("athletes").select("*").eq("id", athlete_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            print(f"⚠️ Errore lettura profilo: {e}")
            return None

    def save_run(self, run_data, athlete_id):
        """Salva una corsa nel DB"""
        try:
            # Aggiungiamo l'ID atleta al record per associarlo
            run_data['athlete_id'] = athlete_id
            
            # Upsert diretto del dizionario run_data (che deve corrispondere alle colonne DB)
            # Se la tua tabella su Supabase usa nomi diversi (es. snake_case),
            # Supabase è intelligente abbastanza da mappare se i nomi coincidono,
            # ma per sicurezza qui usiamo il payload diretto che abbiamo creato in app.py
            
            # Nota: In app.py stiamo creando un oggetto "run_obj" con chiavi come "Dist (km)".
            # Se su Supabase hai colonne chiamate "distance_km", dobbiamo mapparle.
            # Per semplicità, in questa versione assumiamo che tu abbia creato la tabella
            # o che usiamo JSONB. Ma per far funzionare tutto SUBITO, usiamo la mappatura:
            
            payload = {
                "id": run_data['id'],
                "athlete_id": athlete_id,
                "Data": run_data['Data'],             # Assicurati che la colonna Supabase sia "Data" o mappala
                "Dist (km)": run_data['Dist (km)'],
                "Power": run_data['Power'],
                "HR": run_data['HR'],
                "Decoupling": run_data['Decoupling'],
                "WCF": run_data['WCF'],
                "SCORE": run_data['SCORE'],
                "WR_Pct": run_data['WR_Pct'],
                "Rank": run_data['Rank'],
                "Meteo": run_data['Meteo'],
                "SCORE_DETAIL": run_data['SCORE_DETAIL'],
                "raw_watts": run_data['raw_watts'],
                "raw_hr": run_data['raw_hr']
            }

            self.client.table("runs").upsert(payload).execute()
            return True
        except Exception as e:
            # Se fallisce per nomi colonne errati, stampiamo l'errore
            print(f"Errore DB Save Run: {e}")
            return False

    def get_history(self):
        """Scarica tutte le corse dal DB"""
        try:
            response = self.client.table("runs").select("*").order("Data", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Errore DB Get History: {e}")
            return []

    def update_ai_feedback(self, run_id, feedback_text):
        """Aggiorna solo il campo feedback AI"""
        try:
            self.client.table("runs").update({"ai_feedback": feedback_text}).eq("id", run_id).execute()
            return True
        except Exception as e:
            print(f"Errore Update AI: {e}")
            return False
