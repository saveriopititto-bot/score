import streamlit as st

def render_header():
    col_header, col_logout = st.columns([3, 1], gap="large")
    with col_header:
        try: st.image("sCore.png", width=220) 
        except: st.title("sCore Lab 4.1")
        if st.session_state.get("demo_mode"): st.caption("🔴 DEMO MODE")

    with col_logout:
        if st.button("Esci / Logout", key="logout_btn", use_container_width=True):
            st.session_state.strava_token = None
            st.session_state.demo_mode = False
            if "strava_zones" in st.session_state: del st.session_state.strava_zones
            st.rerun()
