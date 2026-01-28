import streamlit as st

def apply_custom_style():
    # Palette TUA:
    # Primary (Salmon): #FF8080
    # Secondary (Peach): #FFCF96
    # Light (Cream): #F6FDC3
    # Success (Mint): #CDFAD5
    # Text: #4A4A4A

    st.markdown("""
        <style>
        /* 1. IMPORT FONT QUESTRIAL */
        @import url('https://fonts.googleapis.com/css2?family=Questrial&display=swap');

        /* 2. SFONDO E FONT GLOBALI */
        .stApp {
            background-color: #F8F9FA; /* Grigio chiarissimo per far risaltare le card bianche */
            font-family: 'Questrial', sans-serif;
            color: #4A4A4A;
        }

        /* Nasconde header default */
        header {visibility: hidden;}

        /* TITOLI */
        h1, h2, h3 {
            color: #4A4A4A;
            font-weight: 600;
        }

        /* 3. BENTO CARDS (Box Fluttuanti) */
        /* Questo trasforma le metriche in Card Pinterest */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: none;
            padding: 20px 25px;
            border-radius: 25px; /* Molto arrotondato */
            box-shadow: 0 10px 30px rgba(0,0,0,0.04); /* Ombra soffice */
            height: 150px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        /* Effetto Hover "Lift" */
        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.08);
        }
        
        /* Decorazione colorata in alto alla card */
        div[data-testid="stMetric"]::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 6px;
            background: linear-gradient(90deg, #FF8080, #FFCF96); /* La tua sfumatura */
        }

        /* Etichetta */
        div[data-testid="stMetricLabel"] {
            font-size: 0.9rem;
            color: #888;
            font-weight: 600;
            letter-spacing: 1px;
        }

        /* Valore */
        div[data-testid="stMetricValue"] {
            font-size: 2.5rem;
            font-weight: 600;
            color: #4A4A4A;
        }

        /* Delta (Badge Mint) */
        div[data-testid="stMetricDelta"] {
            background-color: #CDFAD5; /* TUO VERDE MENTA */
            color: #4A4A4A;
            padding: 5px 12px;
            border-radius: 15px;
            font-weight: 600;
            font-size: 0.85rem;
            margin-top: 10px;
            width: fit-content;
        }
        div[data-testid="stMetricDelta"] svg {
            fill: #4A4A4A !important;
        }

        /* 4. GRAFICI E TABELLE (Card Bianche) */
        .stDataFrame, .stAltairChart, .element-container iframe {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.03);
            border: 1px solid #FFFFFF;
        }

        /* 5. SIDEBAR PULITA */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            box-shadow: 5px 0 20px rgba(0,0,0,0.02);
            border: none;
        }

        /* 6. BOTTONI "PILLOLA" (Tuo Salmone) */
        .stButton>button {
            border-radius: 50px;
            background-color: #FF8080; /* TUO SALMONE */
            color: white;
            border: none;
            padding: 0.6rem 2rem;
            font-family: 'Questrial', sans-serif;
            font-weight: 600;
            box-shadow: 0 5px 15px rgba(255, 128, 128, 0.3);
            transition: all 0.2s;
        }
        .stButton>button:hover {
            background-color: #FF6666;
            transform: scale(1.05);
            box-shadow: 0 8px 20px rgba(255, 128, 128, 0.5);
            color: white;
        }

        /* TABS FLUTTUANTI */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #FFFFFF;
            border-radius: 50px;
            padding: 8px 25px;
            border: 1px solid #EFEFEF;
            font-family: 'Questrial', sans-serif;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }
        .stTabs [aria-selected="true"] {
            background-color: #F6FDC3 !important; /* TUO GIALLO CREMA */
            border: 1px solid #F6FDC3 !important;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)
