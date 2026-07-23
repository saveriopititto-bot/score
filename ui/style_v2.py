import streamlit as st
from config import Config

def load_custom_css():
    """Injects fonts + custom CSS overrides matching the new responsive design."""
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">

        <style>
            body, .stApp { margin: 0; font-family: 'Manrope', sans-serif; background:#ffffff; }
            .mi { font-family: 'Material Icons Round'; font-weight: normal; font-style: normal; line-height: 1; }

            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            .navbtn:hover { background: #f9fafb; color: #374151; }
            .ctrlbtn:hover { background: #ffffff; }
            .bubble:hover { transform: translateY(-4px) scale(1.05); }
            .gauge { transition: transform 0.3s; }
            .gauge:hover { transform: scale(1.05); }
            a { color: #FB4141; }
            a:hover { color: #d93838; }

            .gauge-lg { width: 260px; height: 260px; }
            .gauge-sm { width: 160px; height: 160px; }
            .bubble { width: 112px; height: 112px; }
            .rings-row { gap: 24px; }
            .header-inner { flex-wrap: wrap; row-gap: 8px; }
            .header-controls { gap: 24px; flex-wrap: wrap; row-gap: 8px; justify-content: flex-end; }
            .nav-desktop { display: flex; }
            .nav-mobile { display: none; }
            .user-text { display: flex; }

            .sc-page { container-type: inline-size; container-name: sc-page; }

            @container sc-page (max-width: 900px) {
              .gauge-lg { width: 190px; height: 190px; }
              .gauge-sm { width: 120px; height: 120px; }
              .rings-row { gap: 10px; }
            }
            @container sc-page (max-width: 640px) {
              .nav-desktop { display: none; }
              .nav-mobile { display: flex; }
              .user-text { display: none; }
              .header-controls { gap: 10px; }
              .gauge-lg { width: 130px; height: 130px; }
              .gauge-sm { width: 84px; height: 84px; }
              .rings-row { gap: 4px; }
              .bubble { width: 84px; height: 84px; }
              .ctrl-label { display: none; }
            }
            @media (max-width: 900px) {
              .gauge-lg { width: 190px; height: 190px; }
              .gauge-sm { width: 120px; height: 120px; }
              .rings-row { gap: 10px; }
            }
            @media (max-width: 640px) {
              .nav-desktop { display: none; }
              .nav-mobile { display: flex; }
              .user-text { display: none; }
              .header-controls { gap: 10px; }
              .gauge-lg { width: 130px; height: 130px; }
              .gauge-sm { width: 84px; height: 84px; }
              .rings-row { gap: 4px; }
              .bubble { width: 84px; height: 84px; }
              .ctrl-label { display: none; }
            }
        </style>
    """, unsafe_allow_html=True)

def apply_theme():
    st.set_page_config(
        page_title=Config.APP_TITLE,
        page_icon=Config.APP_ICON,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    load_custom_css()

