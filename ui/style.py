import streamlit as st

# --- CONSTANTS ---
SCORE_COLORS = {
    "bad": "#FF8080",      # Alert/Fatigue
    "neutral": "#FFCF96",  # Focus/Base
    "ok": "#F6FDC3",       # Steady
    "good": "#CDFAD5"      # Success
}

def apply_theme(theme_mode="light"):
    """
    Injects CSS for Glassmorphic Design System.
    """
    
    # 1. THEME DEFINITION
    if theme_mode == "dark":
        bg = "#0f1115"
        card = "rgba(255,255,255,0.05)"
        text = "#f1f1f1"
        border = "rgba(255,255,255,0.1)"
    else:
        bg = "#f8f9fa"
        card = "rgba(255,255,255,0.7)"
        text = "#1f2937"
        border = "rgba(255,255,255,0.4)"

    # 2. CSS INJECTION
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Manrope', sans-serif !important;
        background-color: {bg};
        color: {text};
    }}

    /* Streamlit Main Container tweaks for background */
    .stApp {{
        background-color: {bg};
    }}

    /* GLASS CARD CLASS */
    .glass-card {{
        background: {card};
        backdrop-filter: blur(14px);
        border: 1px solid {border};
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        transition: all .25s ease;
    }}
    .glass-card:hover {{
        transform: scale(1.015);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }}

    /* PULSE ANIMATION */
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(255,207,150,.6); }}
        70% {{ box-shadow: 0 0 0 20px rgba(255,207,150,0); }}
    }}

    /* RESPONSIVE */
    @media (max-width: 768px) {{
        .glass-card {{
            padding: 12px;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

def apply_custom_style():
    """Legacy wrapper if needed, but we should use apply_theme now"""
    if "theme" in st.session_state:
        apply_theme(st.session_state.theme)
    else:
        apply_theme("light")
