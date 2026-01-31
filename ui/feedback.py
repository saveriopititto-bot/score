import streamlit as st

def render_feedback_form(db_service, user_id, user_name):
    """
    Renderizza il form di feedback in fondo alla pagina.
    """
    st.markdown("---") # Linea separatrice elegante
    
    with st.expander("💬 Hai trovato un Bug o hai un'idea? Scrivici!", expanded=False):
        st.caption("Il tuo feedback aiuta a migliorare l'algoritmo SCORE.")
        
        with st.form("feedback_form"):
            c1, c2 = st.columns([1, 2])
            
            with c1:
                f_type = st.selectbox("Tipo di segnalazione", ["🐛 Segnala un Bug", "💡 Suggerimento", "🤖 Errore AI", "d Altro"])
                rating = st.slider("Voto all'esperienza", 1, 5, 5)
            
            with c2:
                msg = st.text_area("Messaggio", placeholder="Descrivi il problema o la tua idea...", height=100)
            
            # Bottone di invio
            submitted = st.form_submit_button("Invia Feedback")
            
            if submitted:
                if not msg:
                    st.warning("Per favore scrivi un messaggio.")
                else:
                    payload = {
                        "user_id": user_id,
                        "user_name": user_name,
                        "type": f_type,
                        "message": msg,
                        "rating": rating
                    }
                    
                    success, err = db_service.save_feedback(payload)
                    
                    if success:
                        st.success("Grazie! Messaggio ricevuto. 🚀")
                    else:
                        st.error(f"Errore nell'invio: {err}")
                        
    # --- DEV CONSOLE SECRET ACCESS ---
    from config import Config
    try:
        user_id_int = int(user_id) if user_id else 0
        if user_id_int in Config.DEV_IDS:
             st.markdown("<br>", unsafe_allow_html=True)
             if st.button("🛠 Developer Console", key="k_dev_btn"):
                 st.session_state.dev_mode = True
                 st.rerun()
    except:
        pass
