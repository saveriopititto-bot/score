import streamlit as st

def apply_custom_style():
    st.markdown("""
        <style>
        /* 1. IMPORT FONT MONTSERRAT (Usato per tutto) */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Montserrat', sans-serif !important;
            color: #2D3436;
        }

        h1, h2, h3 {
            font-family: 'Montserrat', sans-serif !important;
            font-weight: 800;
            color: #2D3436;
            letter-spacing: -0.5px;
        }

        /* 2. PULIZIA STREAMLIT */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;} 
        
        .block-container {
            padding-top: 2rem;
            padding-bottom: 5rem;
        }

        /* 3. STILE KPI CARDS (COMPATTI & CENTRATI) */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #F0F0F3; 
            border-radius: 12px;
            padding: 10px 5px !important; 
            min-height: auto !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); /* Ombra leggera */
            transition: all 0.3s ease;
            
            /* CENTRATURA TOTALE */
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        /* Effetto Hover Card */
        div[data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            border-color: #FFCF96 !important; 
            box-shadow: 0 10px 20px rgba(255, 207, 150, 0.3); /* Ombra pesca */
        }

        /* Label (Titolo del box) */
        div[data-testid="stMetricLabel"] {
            font-size: 0.75rem !important; 
            color: #636E72 !important;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            width: 100%;
            display: flex;
            justify-content: center !important;
        }

        /* Valore (Numero) */
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem !important; 
            color: #2D3436 !important;
            font-weight: 800;
            padding-top: 2px;
        }

        div[data-testid="stMetricDelta"] {
            justify-content: center !important;
            font-size: 0.8rem !important;
        }

        /* ========================================================= */
        /* 4. BOTTONI "BEAUTIFUL" (Palette #FFCF96) */
        /* ========================================================= */
        
        div.stButton > button {
            width: 100%;
            border: none;
            border-radius: 12px;
            padding: 0.6rem 1rem;
            font-family: 'Montserrat', sans-serif;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.9rem;
            transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            background-color: white;
            color: #2D3436;
            border: 1px solid #E0E0E0;
        }

        /* Hover Base */
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
            border-color: #FFCF96;
            color: #E67E22; /* Arancio scuro al passaggio */
        }

        /* Active (Click) */
        div.stButton > button:active {
            transform: translateY(1px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        /* --- BOTTONE PRIMARIO (Es. Aggiorna, Login) --- */
        /* Qui usiamo il gradiente Pesca/Oro */
        button[kind="primary"] {
            background: linear-gradient(135deg, #FFCF96 0%, #FFB347 100%) !important;
            color: #2D3436 !important; /* Testo scuro per leggibilità */
            border: none !important;
            box-shadow: 0 4px 15px rgba(255, 179, 71, 0.4) !important; /* Glow arancio */
        }

        button[kind="primary"]:hover {
            background: linear-gradient(135deg, #FFC06E 0%, #FFA030 100%) !important;
            box-shadow: 0 6px 20px rgba(255, 179, 71, 0.5) !important;
            transform: translateY(-2px) !important;
        }
        
        button[kind="primary"]:active {
            transform: translateY(1px) !important;
            box-shadow: 0 2px 10px rgba(255, 179, 71, 0.3) !important;
        }

        /* --- LINK BUTTON (Es. Connetti Strava) --- */
        .stLinkButton > a {
            background: linear-gradient(135deg, #FFCF96 0%, #FFB347 100%) !important;
            color: #2D3436 !important;
            font-weight: 800 !important;
            text-transform: uppercase;
            border-radius: 12px !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(255, 179, 71, 0.4) !important;
            transition: all 0.2s ease !important;
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .stLinkButton > a:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(255, 179, 71, 0.6) !important;
        }

        /* 5. TABS & EXPANDER */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            border-radius: 8px;
            color: #636E72;
            font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
            background-color: #FFF8E1;
            color: #E67E22 !important;
            border-bottom: 2px solid #FFCF96;
        }
        
        .streamlit-expanderHeader {
            background-color: white;
            border-radius: 8px;
            font-weight: 600;
            border: 1px solid #F0F0F3;
        }
        
        /* 6. MEDIA QUERIES (Responsive Hardening) */
        
        @media (max-width: 1200px) {
            .block-container { padding-left: 2rem; padding-right: 2rem; }
            div[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        }
        
        @media (max-width: 768px) {
            h1 { font-size: 1.8rem !important; }
            .block-container { padding: 1rem; }
            div[data-testid="stMetric"] { padding: 8px 4px !important; }
            div[data-testid="stMetricValue"] { font-size: 1.3rem !important; }
        }
        
        @media (max-width: 480px) {
            div.stButton > button { width: 100% !important; }
        }
        
        /* Touch Device Fallback */
        @media (hover: none) {
            div[data-testid="stMetric"]:hover { transform: none !important; }
            button[kind="primary"]:hover { transform: none !important; }
        }
        /* ========================================================= */
        /* 7. PRO FOOTER STYLES (Full-Width Breakout) */
        /* ========================================================= */
        
        .footer-container {
            width: 100vw !important;
            position: relative;
            left: 50%;
            right: 50%;
            margin-left: -50vw !important;
            margin-right: -50vw !important;
            background-color: #F8F9FA;
            border-top: 1px solid #E0E0E0;
            padding: 60px 0;
            margin-top: 80px;
            font-family: 'Montserrat', sans-serif;
        }
        
        .footer-grid {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            gap: 40px;
            max-width: 1100px; /* Allineato al contenuto main */
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .footer-col h4 {
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            color: #2D3436;
            margin-bottom: 15px;
            letter-spacing: 0.5px;
        }
        
        .footer-col li { list-style: none; margin-bottom: 8px; }
        .footer-col ul { padding: 0; margin: 0; }
        
        .footer-col a {
            text-decoration: none;
            color: #636E72;
            font-size: 0.8rem;
            transition: color 0.2s;
            font-weight: 500;
        }
        
        .footer-col a:hover { color: #E67E22; }
        
        .footer-brand p {
            font-size: 0.8rem;
            color: #636E72;
            line-height: 1.6;
            margin-top: 10px;
        }

        .footer-bottom {
            margin-top: 50px;
            padding: 30px 20px 0 20px;
            border-top: 1px solid #E0E0E0;
            text-align: center;
            font-size: 0.75rem;
            color: #B2BEC3;
            max-width: 1100px;
            margin-left: auto;
            margin-right: auto;
        }

        /* Mobile Responsive */
        @media (max-width: 768px) {
            .footer-grid {
                grid-template-columns: 1fr;
                text-align: center;
                gap: 40px;
            }
            .footer-container { padding: 40px 0; }
        }
        </style>
    """, unsafe_allow_html=True)
