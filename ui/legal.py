import streamlit as st
# Importiamo i file dalla cartella pages come fossero librerie
from pages import privacy, terms 

def render_legal_section():
    """
    Renderizza l'expander Note Legali nel footer.
    """
    # Stile per rendere l'header dell'expander discreto (grigio)
    st.markdown("""
        <style>
        .streamlit-expanderHeader {
            font-size: 0.85rem;
            color: #636E72;
            background-color: transparent !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.expander("⚖️ Privacy Policy & Terms of Service", expanded=False):
        # Creiamo due schede
        tab_priv, tab_terms = st.tabs(["Privacy Policy", "Terms of Service"])
        
        with tab_priv:
            privacy.show()  # Chiama la funzione dentro pages/privacy.py
            
        with tab_terms:
            terms.show()    # Chiama la funzione dentro pages/terms.py

def render_colophon():
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("📜 Info Progetto & Colophon (v1.0)", expanded=False):
        st.markdown("""
        <div style="font-size: 0.9rem; color: #555;">
            <p><strong>SCORE – Running Performance · 2026</strong></p>
            <p>Nato per aiutare i runner a privilegiare la qualità e la sostenibilità, 
            non solo la performance pura.</p>
            <p><strong>Tecnologia:</strong> Sviluppato in Python con un approccio essenziale.</p>
            <p><strong>Metodo:</strong> Analisi multi-segnale (Power, HR, Meteo) per un contesto reale.</p>
            <hr>
            <p style="font-size: 0.8rem;"><em>Nota: Questo è un progetto indipendente. 
            Non è uno strumento medico. Ascolta sempre il tuo corpo.</em></p>
        </div>
        """, unsafe_allow_html=True)
