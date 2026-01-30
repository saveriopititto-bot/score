import streamlit as st

def apply_custom_style():
    st.markdown("""
        <style>
        /* 1. IMPORT FONT MONTSERRAT (Usato per tutto) */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Montserrat', sans-serif !important;
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
            border: 2px solid #F0F0F3; /* Bordo neutro di default */
            border-radius: 12px;
            
            /* BOX PIÙ PICCOLI */
            padding: 10px 5px !important; 
            min-height: auto !important;
            
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
            
            /* CENTRATURA TOTALE */
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        /* Effetto Hover: Il bordo diventa del tuo nuovo colore #FFCF96 */
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: #FFCF96 !important; 
            box-shadow: 0 4px 10px rgba(255, 207, 150, 0.4); /* Ombra colorata */
        }

        /* Label (Titolo del box) */
        div[data-testid="stMetricLabel"] {
            font-size: 0.75rem !important; /* Testo più piccolo */
            color: #636E72 !important;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            
            /* Centratura forzata */
            width: 100%;
            display: flex;
            justify-content: center !important;
        }

        /* Valore (Numero) */
        div[data-testid="stMetricValue"] {
            font-size: 1.4rem !important; /* Numero proporzionato al box piccolo */
            color: #2D3436 !important;
            font-weight: 800;
            padding-top: 2px;
        }

        /* Delta (Freccina verde/rossa) - Centrata */
        div[data-testid="stMetricDelta"] {
            justify-content: center !important;
            font-size: 0.8rem !important;
        }

        /* 4. BOTTONI (Colore #FFCF96) */
        div.stButton > button {
            border-radius: 10px;
            font-family: 'Montserrat', sans-serif;
            font-weight: 700;
            text-transform: uppercase;
            border: none;
            transition: all 0.2s;
        }
        
        /* Bottone Primario (Pieno) */
        button[kind="primary"] {
            background-color: #FFCF96 !important;
            color: #2D3436 !important; /* Testo scuro per contrasto su giallo/arancio */
        }
        button[kind="primary"]:hover {
            background-color: #FFB347 !important; /* Arancio leggermente più scuro all'hover */
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        /* Bottone Secondario (Outline) */
        button[kind="secondary"] {
            border: 2px solid #FFCF96 !important;
            color: #2D3436 !important;
        }

        /* 5. TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 45px;
            border-radius: 8px;
            color: #636E72;
            font-weight: 600;
            font-family: 'Montserrat', sans-serif;
        }

        .stTabs [aria-selected="true"] {
            background-color: #FFF8E1; /* Sfondo giallo chiarissimo per tab attiva */
            color: #E67E22 !important; /* Testo arancio scuro */
            border-bottom: 2px solid #FFCF96;
        }
        
        /* 6. EXPANDER */
        .streamlit-expanderHeader {
            background-color: white;
            border-radius: 8px;
            font-weight: 600;
            border: 1px solid #F0F0F3;
        }
        
        /* TITOLI COLORE PERSONALE */
        h1 span, h2 span, h3 span {
             color: #FFCF96; /* Se ci sono highlight */
        }
        
        </style>
    """, unsafe_allow_html=True)
