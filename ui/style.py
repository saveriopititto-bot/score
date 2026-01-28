import streamlit as st

def apply_custom_style():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Questrial&display=swap');

        /* 1. SETUP GLOBALE */
        .stApp {
            background-color: #F8F9FA;
            font-family: 'Questrial', sans-serif;
            color: #4A4A4A;
        }
        header {visibility: hidden;}

        /* 2. SIDEBAR E INPUT (FIX CRITICO) */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #F0F0F0;
        }
        
        /* Questo trasforma gli input neri in box grigio chiaro eleganti */
        div[data-baseweb="input"] {
            background-color: #F3F4F6 !important; /* Grigio chiaro */
            border-radius: 12px !important;
            border: 1px solid #EEE !important;
            color: #4A4A4A !important;
        }
        /* Colore del testo dentro gli input */
        input[class*="st-"] {
            color: #4A4A4A !important;
        }
        /* I bottoncini +/- degli input numerici */
        button[kind="secondary"] {
            background-color: transparent !important;
            border: none !important;
            color: #888 !important;
        }
        /* Etichette della sidebar */
        .stMarkdown label p {
            font-size: 0.9rem;
            color: #888;
            font-weight: 600;
        }

        /* 3. METRIC CARDS (Bento Style) */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #F0F0F0; /* Bordo sottile per definizione */
            padding: 20px;
            border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.03);
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            overflow: visible; /* Importante per l'hover */
            transition: all 0.3s ease;
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            border-color: #FF8080; /* Highlight colorato al passaggio */
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.85rem;
            color: #9CA3AF; /* Grigio medio */
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        div[data-testid="stMetricValue"] {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1F2937; /* Quasi nero */
        }

        /* Badge colorati (Delta) */
        div[data-testid="stMetricDelta"] {
            background-color: #CDFAD5; /* Menta */
            color: #1F2937;
            padding: 4px 10px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.8rem;
            margin-top: 8px;
            display: inline-block;
        }

        /* 4. GRAFICI E TABELLE */
        .stDataFrame, .stAltairChart {
            background-color: #FFFFFF;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        }

        /* 5. TITOLI */
        h1, h2, h3 {
            color: #1F2937;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        /* 6. BOTTONI */
        .stButton>button {
            border-radius: 50px;
            font-weight: 600;
            box-shadow: 0 4px 10px rgba(255, 128, 128, 0.3);
            transition: transform 0.2s;
        }
        .stButton>button:hover {
            transform: scale(1.03);
        }
        </style>
    """, unsafe_allow_html=True)
