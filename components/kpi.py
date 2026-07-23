import streamlit as st
from config import Config
from ui import visuals

def render_kpi_grid(cur_run, quality_data, trend_data, consistency_data, ef_data, zones_data):
    """
    Renders the KPI Grid matching the React App.tsx layout.
    """
    
    # --- 1. PREPARE DATA ---
    details = cur_run.get('SCORE_DETAIL', {})
    # PB Percentile (Use legacy WR_Pct or calculate new)
    percentile_val = cur_run.get('WR_Pct', 0.0) 
    # Use actual PB pct if available in details, fallback to something else
    if 'pb_pct' in details: percentile_val = details['pb_pct']
    
    score_val = cur_run.get('SCORE', 0.0)
    drift_val = cur_run.get('Decoupling', 0.0)
    
    # --- 2. GENERATE SVG/HTML COMPONENTS ---
    
    # Rings
    html_pct = visuals.render_kpi_percentile(percentile_val)
    html_score = visuals.render_kpi_score(score_val)
    html_drift = visuals.render_kpi_drift(drift_val)
    
    # Bubbles
    html_quality = visuals.quality_circle(quality_data)
    html_trend = visuals.trend_circle(trend_data)
    html_constcy = visuals.consistency_circle(consistency_data)
    html_ef = visuals.efficiency_circle(ef_data)
    
    # Zone Badge (Dominant Zone)
    dom_zone = "Z5"
    if zones_data:
        dom_zone = max(zones_data, key=zones_data.get)
    html_zones = visuals.zones_circle_badge(dom_zone, 0)

    # --- 3. RENDER LAYOUT ---
    
    # Use the layout structure from App.tsx
    # Main Rings Section with negative margins handled in HTML generation or here
    # Since we are using standard divs, we use flexbox with gap.
    
    st.markdown(f"""
    <div class="flex flex-col items-center justify-center overflow-hidden py-4">
        
        <!-- Main Rings Section -->
        <div class="flex items-center justify-center rings-row gap-2 sm:gap-6 mb-12 relative mt-4 md:mt-8">
            
            <!-- Left Ring - Percentile -->
            <div class="relative z-10 gauge gauge-sm">
                {html_pct}
            </div>

            <!-- Center Ring - Score -->
            <div class="relative z-20 gauge gauge-lg">
                {html_score}
            </div>

            <!-- Right Ring - Drift -->
            <div class="relative z-10 gauge gauge-sm">
                {html_drift}
            </div>
        </div>

        <!-- Lower Stats Row -->
        <div class="flex flex-wrap justify-center gap-4 sm:gap-8 mt-4 max-w-4xl px-2">
            {html_quality}
            {html_trend}
            {html_constcy}
            {html_ef}
            {html_zones}
        </div>

    </div>
    """, unsafe_allow_html=True)
