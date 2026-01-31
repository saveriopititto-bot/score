import streamlit as st
from datetime import datetime
from pages import privacy, terms

def render_legal_section():
    year = datetime.now().year
    
    st.divider()
    
    # Grid minimale con Streamlit native
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"### sCore Lab v1.0")
        st.caption(f"© {year} Progetto indipendente sviluppato in Python.")
        st.info("⚠️ Non è uno strumento medico. Interpreta i dati con consapevolezza.")
        
    with col2:
        st.markdown("**Risorse**")
        st.page_link("app.py", label="Home", icon="🏠")
        st.markdown("[GitHub 🐙](https://github.com)")
        st.markdown("[Strava 🏃](https://strava.com)")

    with col3:
        st.markdown("**Legale**")
        if st.button("Privacy Policy"):
            st.info("Sezione in fase di caricamento...")
            privacy.show()
        if st.button("Terms of Service"):
            terms.show()

    st.markdown("---")
    st.caption(f"All rights reserved &middot; {athlete_info_str if 'athlete_info_str' in globals() else ''}")
