from supabase import create_client, Client
import streamlit as st

class DatabaseService:
    def __init__(self, url: str, key: str):
        # CORREZIONE 1: Usiamo self.client ovunque per coerenza
        self.client: Client = create_client(url, key)

    def save_feedback(self, feedback_data):
        """Salva il feedback utente"""
        try:
            self.client.table("feedback").insert(feedback_data).execute()
            return True, None
        except Exception as e:
            print(f"Errore Feedback: {e}")
            return False, str(e)

    def save_athlete_profile(self, profile_data):
        """
        Salva o aggiorna (Upsert) i dati dell'atleta.
        RITORNA DUE VALORI: (Successo, MessaggioErrore)
        """
        try:
            # Upsert: se l'ID esiste aggiorna, se no crea
            data, count = self.client.table("athletes").upsert(profile_data).execute()
            
            # CORREZIONE 2: RITORNA UNA COPPIA (True, None)
            # Questo soddisfa la richiesta "success, error_msg =" in app.py
            return True, None 
            
        except Exception as e:
            print(f"⚠️ Errore salvataggio profilo: {e}")
            # CORREZIONE 2: RITORNA UNA COPPIA (False, Errore)
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
            # Aggiungiamo l'ID atleta al record
            run_data['athlete_id'] = athlete_id
            
            # Upsert diretto: Supabase cercherà di mappare le chiavi del dizionario 
            # alle colonne della tabella. Assicurati che le colonne esistano o 
            # che stai usando una colonna JSONB.
            self.client.table("runs").upsert(run_data).execute()
            return True
        except Exception as e:
            print(f"Errore DB Save Run: {e}")
            return False

    def get_history(self):
        """Scarica tutte le corse dal DB"""
        try:
            # Order by Data decrescente
            response = self.client.table("runs").select("*").order("Data", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Errore DB Get History: {e}")
            return []

    def update_ai_feedback(self, run_id, feedback_text):
        """Aggiorna solo il campo feedback AI di una corsa specifica"""
        try:
            self.client.table("runs").update({"ai_feedback": feedback_text}).eq("id", run_id).execute()
            return True
        except Exception as e:
            print(f"Errore Update AI: {e}")
            return False
