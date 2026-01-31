import streamlit as st

class Config:
    # --- GLOBAL CONSTANTS ---
    APP_TITLE = "sCore"
    APP_ICON = "favicon.png"
    
    # --- ALGORITHM PARAMETERS ---
    ENGINE_VERSION = "4.2"
    
    # World Record Benchmark (Elite standard)
    WR_WKG = 6.4 
    
    # Score Component Weights (Must sum to 1.0)
    WEIGHT_POWER = 0.5
    WEIGHT_VOLUME = 0.3
    WEIGHT_INTENSITY = 0.2
    
    # Penalties
    DECOUPLING_THRESHOLD = 0.05 # 5% drift is normal
    DECOUPLING_PENALTY_FACTOR = 2.0
    
    # Volume Scaling
    VOLUME_LOG_DIVISOR = 4.5
    
    # Rank Thresholds
    RANK_THRESHOLDS = {
        "ELITE": 0.35,
        "PRO": 0.28,
        "ADVANCED": 0.22,
        "INTERMEDIATE": 0.15
    }

    # Rank Colors (Hex for SVG/CSS)
    RANK_COLORS = {
        "ELITE": "#CDFAD5",       # Light Green (Palette)
        "PRO": "#3B82F6",         # Blue
        "ADVANCED": "#10B981",    # Emerald
        "INTERMEDIATE": "#F59E0B", # Amber
        "ROOKIE": "#9CA3AF"       # Gray
    }
    
    # --- DEFAULTS ---
    DEFAULT_WEIGHT = 70.0
    DEFAULT_HR_MAX = 185
    DEFAULT_HR_REST = 50
    DEFAULT_FTP = 250
    DEFAULT_AGE = 30
    
    # --- SECRETS & KEYS ---
    @staticmethod
    def check_secrets():
        """
        Validates that all necessary secrets are present.
        Returns a list of missing keys.
        """
        missing = []
        
        # Strava
        if not st.secrets.get("strava", {}).get("client_id"): missing.append("strava.client_id")
        if not st.secrets.get("strava", {}).get("client_secret"): missing.append("strava.client_secret")
        
        # Supabase
        if not st.secrets.get("supabase", {}).get("url"): missing.append("supabase.url")
        if not st.secrets.get("supabase", {}).get("key"): missing.append("supabase.key")
        
        # Gemini (Optional but recommended)
        if not st.secrets.get("gemini", {}).get("api_key"): missing.append("gemini.api_key")
        
        return missing

    @staticmethod
    def get_strava_creds():
        return st.secrets.get("strava", {})

    @staticmethod
    def get_supabase_creds():
        return st.secrets.get("supabase", {})

    @staticmethod
    def get_gemini_key():
        return st.secrets.get("gemini", {}).get("api_key")

    # --- LOGGING ---
    @staticmethod
    def setup_logging():
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        return logging.getLogger("sCore")

    # --- EXTERNAL SERVICES ---
    OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
    STRAVA_BASE_URL = "https://www.strava.com/api/v3"

    # --- ALGORITHM TUNING ---
    SCALING_FACTOR = 280.0
    ELITE_SPEED_M_S = 5.8
    
    # Score 4.1 Parameters
    SCORE_ALPHA = 0.8
    SCORE_BETA = 3.0
    SCORE_GAMMA = 2.0
    SCORE_W_REF = 6.0
    W_REF = 6.0
    
    # --- DEV MODE ---
    DEV_IDS = {12345678, 59049495} # Saverio's ID added


