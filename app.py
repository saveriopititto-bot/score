import streamlit as st
from ui.style_v2 import apply_theme

# --- SETUP & THEME ---
apply_theme()

from config import Config


# --- STATE MANAGEMENT ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- VIEWS IMPORT ---
# We import views here to avoid circular dependencies if they import app state
try:
    from views.landing import render_landing
    from views.dashboard import render_dashboard
    from views.login import render_login
except ImportError:
    # Fallback for initial run if files aren't ready
    def render_landing(): st.title("Landing Page (Placeholder)")
    def render_dashboard(): st.title("Dashboard (Placeholder)")
    def render_login(): st.title("Login (Placeholder)")

# --- ROUTING ---
def main():
    # Simple Routing Logic
    
    # 1. Custom URL Parameters (e.g. ?view=demo)
    query_params = st.query_params
    
    # 2. Authentication Check
    if not st.session_state.authenticated:
        if query_params.get("login") == "true":
            render_login()
        else:
            render_landing()
        return

    # 3. Authenticated View (Dashboard)
    render_dashboard()

if __name__ == "__main__":
    main()
