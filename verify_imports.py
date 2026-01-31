try:
    print("--- 1. Base Modules ---")
    from config import Config
    print("✅ Config imported")
    Config.setup_logging()
    
    from engine.core import ScoreEngine, RunMetrics
    print("✅ ScoreEngine imported")
    
    from services.api import StravaService, WeatherService
    print("✅ Services API imported")
    
    from services.db import DatabaseService
    print("✅ DatabaseService imported")

    print("\n--- 2. Controllers ---")
    from controllers.sync_controller import SyncController
    print("✅ SyncController imported")

    print("\n--- 3. Components ---")
    from components.header import render_header
    from components.athlete import render_top_section
    from components.kpi import render_kpi_grid
    print("✅ UI Components imported")

    print("\n--- 4. Views ---")
    from views.landing import render_landing
    from views.dashboard import render_dashboard
    print("✅ Views imported")
    
    print("\n🎉 All modules imported successfully.")
except Exception as e:
    print(f"\n❌ Import Error: {e}")
    exit(1)
