import streamlit as st
from datetime import datetime


def render_legal_section():
    year = datetime.now().year
    
    # Wrapper per font Montserrat
    st.markdown("""
        <style>
        .footer-minimal {
            font-family: 'Montserrat', sans-serif !important;
            margin-top: 50px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    with st.container():
        st.markdown('<div class="footer-minimal">', unsafe_allow_html=True)
        # Grid minimale con Streamlit native
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            titolo = "sCore Lab v1.0"
            descrizione = "Powered by <strong>sCorengine 4.1</strong>"
            testo = f"{titolo}<br>{descrizione}"

            st.markdown(f"""
            <div style="text-align: left; margin-bottom: 30px;">
                <p style="color: #636E72; font-size: 1.1rem; margin: 0;">
                    {testo}<br>
                    Il nuovo standard per l'analisi della corsa.
                </p>
            </div>
            """, unsafe_allow_html=True)
                
        with col2:
            st.markdown("**Legale**")
            st.page_link("pages/privacy.py", label="Privacy Policy", icon="🔒")
            st.page_link("pages/terms.py", label="Terms of Service", icon="📜")

        with col3:
            st.markdown("**Risorse**")
            st.markdown("[GitHub 🐙](https://github.com)")
            st.markdown("[Strava 🏃](https://strava.com)")

        st.markdown("---")
        st.markdown(f"""
<div style="
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #636E72;
    margin-top: 20px;
">
    <span>© {year} Progetto indipendente sviluppato in Python</span>
    <span>Non è uno strumento medico. Interpreta i dati con consapevolezza.</span>
    <span>All rights reserved · sCore Lab</span>
</div>
""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
