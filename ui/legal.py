import streamlit as st
from datetime import datetime
from pages import privacy, terms

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
            st.markdown("**Risorse**")
            st.markdown("[Home](/)")
            st.markdown("[GitHub 🐙](https://github.com)")
            st.markdown("[Strava 🏃](https://strava.com)")

        with col3:
            st.markdown("**Legale**")
            st.markdown("[Privacy Policy](https://scorerun.streamlit.app/privacy)")
            st.markdown("[Terms of Service](https://scorerun.streamlit.app/terms)")

        st.markdown("---")
        st.caption(f"© {year} Progetto indipendente sviluppato in Python. All rights reserved &middot; sCore Lab {year} Non è uno strumento medico. Interpreta i dati con consapevolezza.")
        st.markdown('</div>', unsafe_allow_html=True)
