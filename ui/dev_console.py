import streamlit as st
import pandas as pd

def render_dev_console():
    st.title("🛠 Developer Console")
    st.caption("Internal diagnostics — SCORE Lab")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Import",
        "🧮 Formula",
        "❤️ Drift",
        "🚦 Rate Limit"
    ])

    with tab1:
        st.subheader("Strava Import Debug")
        st.json(st.session_state.get("last_strava_response", {}))
        st.write(f"Activities fetched: {len(st.session_state.get('last_activities', []))}")

    with tab2:
        st.subheader("SCORE Breakdown")
        st.json(st.session_state.get("last_score_math", {}))

    with tab3:
        st.subheader("Drift Debug")
        st.json(st.session_state.get("last_drift_debug", {}))

    with tab4:
        st.subheader("Rate Limit")
        st.json(st.session_state.get("rate_limit_headers", {}))

    if st.button("⬅️ Torna alla app"):
        st.session_state.dev_mode = False
        st.rerun()
