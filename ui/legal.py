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
