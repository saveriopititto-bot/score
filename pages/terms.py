import streamlit as st
import sys
import os

# --- 1. FIX PER I PERCORSI ---
# Necessario per importare lo stile dalla cartella principale
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from ui.style import apply_custom_style

# --- 2. SETUP PAGINA ---
st.set_page_config(
    page_title="Terms of Service",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_custom_style()

# --- 3. LAYOUT CENTRATO ---
c_left, c_center, c_right = st.columns([1, 2, 1])

with c_center:
    # Bottone per tornare alla Home
    if st.button("← Back to Dashboard", type="secondary"):
        st.switch_page("app.py")
    
    st.divider()

    # --- 4. IL TUO CONTENUTO ---
    st.markdown("### 📝 Terms of Service")
    
    st.markdown("""
    <div style="font-size: 1.05rem; line-height: 1.6; color: #2D3436;">
    
    <strong>SCORE 4.1</strong> is provided "as-is" for personal and informational purposes only.
    <br><br>
    The application does not provide medical advice, training plans, or health recommendations.
    <br><br>
    Users remain fully responsible for their training decisions and physical activity.
    <br><br>
    By using the app, users voluntarily connect their Strava account and may revoke access at any time via Strava settings.
    
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("© 2026 sCore Lab")