import streamlit as st
import logging

# --- 1. CONFIG & VALIDATION ---
from config import Config

# Setup Logging
logger = Config.setup_logging()
logger.info("Starting sCore App...")

missing_secrets = Config.check_secrets()
if missing_secrets:
    st.error(f"❌ Segreti mancanti: {', '.join(missing_secrets)}")
    st.stop()

# --- 2. IMPORT MODULI ---
# Force reload for debugging (safe to keep for now)
import importlib
import engine.core
importlib.reload(engine.core)

from services.api import StravaService
from services.db import DatabaseService
from ui.style import apply_custom_style

# Views
from views.landing import render_landing
from views.dashboard import render_dashboard

# --- 3. PAGE SETUP ---
st.set_page_config(
    page_title=Config.APP_TITLE, 
    page_icon=Config.APP_ICON, 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- THEME STATE & TOGGLE ---
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Sidebar theme toggle removed

# Apply Theme
from ui.style import apply_theme
apply_theme(st.session_state.theme)

# --- DEV MODE ROUTING ---
if st.session_state.get("dev_mode"):
    from ui.dev_console import render_dev_console
    render_dev_console()
    st.stop()

st.markdown("""
<style>
/* FORCE WHITE CIRCLES UI */
.stat-circle {
  background: #ffffff !important;  /* Sempre Bianco */
  color: #2D3436 !important;       /* Sempre Testo Scuro */
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15); /* Ombra per stacco */
  animation: scaleIn 0.45s ease-out;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

/* Hover Effect */
.stat-circle:hover {
  transform: scale(1.06);
  box-shadow: 0 15px 40px rgba(0,0,0,0.25);
}

@keyframes scaleIn {
  from { transform: scale(0.85); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# --- 4. SERVIZI ---
strava_creds = Config.get_strava_creds()
supa_creds = Config.get_supabase_creds()
auth_svc = StravaService(strava_creds["client_id"], strava_creds["client_secret"])
db_svc = DatabaseService(supa_creds["url"], supa_creds["key"])

# --- 5. STATE ---
if "strava_token" not in st.session_state: st.session_state.strava_token = None
if "data" not in st.session_state: st.session_state.data = db_svc.get_history()
if "demo_mode" not in st.session_state: st.session_state.demo_mode = False

# Callback Strava
if "code" in st.query_params and not st.session_state.strava_token:
    tk = auth_svc.get_token(st.query_params["code"])
    if tk: 
        st.session_state.strava_token = tk
        st.query_params.clear()
        st.rerun()

# =========================================================
# LOGICA PRINCIPALE (ROUTING)
# =========================================================

if not st.session_state.strava_token:
    render_landing(auth_svc)
else:
    render_dashboard(auth_svc, db_svc)
