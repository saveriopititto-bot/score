import streamlit as st
import sys
import os

# --- 1. FIX PER I PERCORSI ---
# Necessario perché siamo nella sottocartella /pages e dobbiamo
# dire a Python di guardare nella cartella superiore per trovare 'ui.style'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from ui.style import apply_custom_style

# --- 2. SETUP PAGINA ---
st.set_page_config(
    page_title="Privacy Policy",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_custom_style()

# --- 3. LAYOUT CENTRATO ---
# Usiamo 3 colonne per centrare il testo e renderlo elegante da leggere
c_left, c_center, c_right = st.columns([1, 2, 1])

with c_center:
    # Bottone per tornare alla Home
    if st.button("← Back to Dashboard", type="secondary"):
        st.switch_page("app.py")
    
    st.divider()

    # --- 4. IL TUO CONTENUTO ---
    st.markdown("### 🔒 Privacy Policy")
    
    st.markdown("""
    <div style="font-size: 1.05rem; line-height: 1.6; color: #2D3436;">
    
    <strong>SCORE 4.1</strong> accesses Strava data only after explicit user authorization via OAuth.
    <br><br>
    The application collects and processes running activity data exclusively for personal performance analysis of the authenticated user.
    <br><br>
    No personal data is shared with third parties, sold, or used for advertising purposes.
    <br><br>
    All data is stored securely and can be deleted upon user request.
    <br><br>
    SCORE 4.1 is not a social platform and does not expose user data publicly.
    
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("© 2026 sCore Lab")