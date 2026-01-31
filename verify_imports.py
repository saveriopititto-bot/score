try:
    from config import Config
    print("Config imported")
    Config.setup_logging()
    
    from engine.core import ScoreEngine, RunMetrics
    print("ScoreEngine imported")
    
    from services.api import StravaService, WeatherService, AICoachService
    print("Services API imported")
    
    from services.db import DatabaseService
    print("DatabaseService imported")
    
    print("\n✅ All modules imported successfully.")
except Exception as e:
    print(f"\n❌ Import Error: {e}")
    exit(1)
