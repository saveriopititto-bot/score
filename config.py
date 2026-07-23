import streamlit as st

class Config:
    # --- GLOBAL CONSTANTS ---
    APP_TITLE = "sCore"
    APP_ICON = "assets/favicon.png"
    
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

    # --- THEME & COLORS ---
    class Theme:
        """Centralized Color Palette for UI and Charts"""
        # Primary Colors (Neon Palette from React App)
        PRIMARY = "#FB4141"      # score-red
        SECONDARY = "#5CB338"    # score-green
        ACCENT = "#FFC145"       # score-yellow
        ACCENT_LIGHT = "#ECE852" # score-yellow-light
        DANGER = "#FB4141"       # score-red
        INFO = "#5C5CFF"         # score-blue
        ORANGE = "#FF8E53"       # score-orange
        
        # Backgrounds
        BG_DARK = "#1F2937"      # score-dark
        BG_LIGHT = "#F9FAFB"
        
        # Surfaces
        SURFACE_LIGHT = "#FFFFFF"
        SURFACE_DARK = "#1F2937"
        
        # Text
        TEXT_DARK = "#f3f4f6"
        TEXT_LIGHT = "#1f2937"
        
        # Score Quality Colors (Matched to new Palette)
        SCORE_EPIC = "#5CB338"      # Green
        SCORE_GREAT = "#5C5CFF"     # Blue 
        SCORE_SOLID = "#FFC145"     # Yellow
        SCORE_WEAK = "#FB4141"      # Red
        
        # Legacy mappings
        SCORE_LEGENDARY = SCORE_EPIC
        SCORE_WASTED = SCORE_WEAK
        
        # Gradients / Special
        GLASS_BORDER_LIGHT = "rgba(229, 231, 235, 1)" # border-light
        GLASS_BORDER_DARK = "rgba(55, 65, 81, 1)"     # border-dark

    # --- SCORE THRESHOLDS ---
    class Thresholds:
        LEGENDARY = 90
        EPIC = 80
        GREAT = 70
        SOLID = 60
        OK = 40
        WEAK = 20

    # Rank Colors (Hex for SVG/CSS)
    RANK_COLORS = {
        "ELITE": "#5CB338", # Green
        "PRO": "#5C5CFF",   # Blue
        "ADVANCED": "#FFC145", # Yellow
        "INTERMEDIATE": "#FB4141", # Red
        "ROOKIE": "#9CA3AF"  # Gray
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
    DEV_IDS = {12345678, 59049495}