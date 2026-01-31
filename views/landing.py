import streamlit as st
from ui.legal import render_legal_section

def render_landing(auth_svc):
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. HERO SECTION (Logo 20% più grande, No Slogan, Strava sotto Logo)
    _, c_center, _ = st.columns([1, 2, 1])
    with c_center:
        # Contenitore centratura
        col_logo_L, col_logo_C, col_logo_R = st.columns([1, 1.5, 1])
        with col_logo_C:
             try: st.image("sCore.png", use_container_width=True) 
             except: st.markdown("<h1 style='text-align: center; color: #FFCF96;'>sCore Lab</h1>", unsafe_allow_html=True)
             
             # Bottone Strava sotto il LOGO (stessa dimensione visiva tramite colonne)
             redirect_url = "https://scorerun.streamlit.app/" 
             link_strava = auth_svc.get_link(redirect_url)
             st.link_button("Connetti Strava", link_strava, type="primary", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True) 

    # 2. IL MANIFESTO

    col_a, col_b, col_c = st.columns(3, gap="large")

    with col_a:
        st.markdown("""
        <div style="background-color: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 5px solid #FFCF96; height: 100%;">
            <h4 style="color: #444; text-transform: uppercase; letter-spacing: 1px;">CORRI</h4>
            <p style="font-size: 0.9rem; color: #555;">
                Non tutte le corse sono uguali.<br>
                SCORE non guarda solo velocità o distanza, ma <strong>come hai gestito lo sforzo</strong> nel tuo contesto attuale.
            </p>
            <p style="font-size: 0.9rem; font-weight: bold;">
                Un numero solo,<br>molte informazioni utili.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div style="background-color: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 5px solid #FF8080; height: 100%;">
            <h4 style="color: #444; text-transform: uppercase; letter-spacing: 1px;">ANALIZZA</h4>
            <p style="font-size: 0.9rem; color: #555;">
                Non è una gara, è un feedback. Nessun giudizio, solo un obiettivo: <strong>correre meglio la prossima volta</strong>.
            </p>
            <p style="font-size: 0.9rem;">
                Un punteggio alto = corsa controllata e sostenibile.<br>
                Un punteggio basso? 👉 <em>Solo un segnale, non un errore.</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_c:
        st.markdown("""
        <div style="background-color: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 5px solid #CDFAD5; height: 100%;">
            <h4 style="color: #444; text-transform: uppercase; letter-spacing: 1px;">EVOLVI</h4>
            <p style="font-size: 0.9rem; color: #555;">
                Il vero progresso non è spingere sempre, ma capire <strong>quando</strong> farlo.
                Usa SCORE per riconoscere i giorni buoni e quelli no.
            </p>
            <p style="font-size: 0.9rem; font-weight: bold;">
                Allenarsi bene non significa fare di più,<br>ma fare meglio.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # 3. FOOTER
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # PRO FOOTER
    render_legal_section()
