import streamlit as st
import pandas as pd
import altair as alt
import math
from config import Config

# --- 1. BUSINESS LOGIC (COLOR HELPERS) ---

def get_score_color(score):
    try: val = float(score)
    except: val = 0.0
    if val <= Config.Thresholds.WEAK: return Config.Theme.SCORE_WEAK
    if val <= Config.Thresholds.SOLID: return Config.Theme.SCORE_SOLID
    if val <= Config.Thresholds.GREAT: return Config.Theme.SCORE_GREAT
    return Config.Theme.SCORE_EPIC

def get_percentile_color(pct):
    try: val = float(pct)
    except: val = 0.0
    if val > 75: return Config.Theme.SCORE_EPIC
    if val > 50: return Config.Theme.SCORE_GREAT
    if val > 25: return Config.Theme.SCORE_SOLID
    return Config.Theme.SCORE_WEAK

def get_drift_color(drift):
    try: val = float(drift)
    except: val = 0.0
    if val > 5.0: return Config.Theme.SCORE_WEAK
    if val > 3.0: return Config.Theme.SCORE_SOLID
    return Config.Theme.SCORE_EPIC # Low drift is Green

# --- 2. SVG GENERATORS (Ported from ArcGauge.tsx) ---

def generate_arc_svg(value_pct: float, label: str, display_value: str, color: str, size: str = 'lg', sub_value: str = None, glow: bool = False):
    """
    Generates an SVG string mimicking the ArcGauge.tsx React component.
    """
    is_lg = (size == 'lg')
    
    # Dimensions based on React component logic
    # To ensure high quality rendering in HTML, we define viewBox
    view_box_size = 180 if is_lg else 100
    radius = 80 if is_lg else 45
    center = view_box_size / 2
    stroke_width = 8 if is_lg else 5
    
    # Angles
    start_angle = 135
    # Full circle is 360. Arc is 270 deg (from 135 to 405).
    # 135 deg start. 
    # End angle calculation: 
    # React code: startAngle=135, endAngle=45 (which is 405).
    
    def to_rad(deg):
        return deg * math.pi / 180

    start_x = center + radius * math.cos(to_rad(135))
    start_y = center + radius * math.sin(to_rad(135))
    end_x = center + radius * math.cos(to_rad(405))
    end_y = center + radius * math.sin(to_rad(405))
    
    # Background Track Path
    # Large arc flag is 1 because 270 > 180
    path_d = f"M {start_x} {start_y} A {radius} {radius} 0 1 1 {end_x} {end_y}"
    
    # Value Path (Stroke Dash)
    # Arc length calculation
    # 270 degrees = 0.75 of circle circumference
    full_circumference = 2 * math.pi * radius
    arc_length = full_circumference * 0.75
    
    # Clamp value 0-100
    safe_value = max(0, min(float(value_pct), 100))
    
    # Dash Offset:
    # offset = length - (length * value / 100)
    dash_offset = arc_length - (arc_length * safe_value / 100)
    
    # Classes for responsive sizing
    container_class = "gauge gauge-lg" if is_lg else "gauge gauge-sm"
    
    # Font sizes
    label_class = "text-[0.65rem] sm:text-xs" if is_lg else "text-[0.5rem] sm:text-[0.65rem]"
    value_class = "text-6xl sm:text-8xl" if is_lg else "text-2xl sm:text-4xl"
    
    glow_style = f"filter: drop-shadow(0 0 10px {color}80);" if glow else ""
    
    # Unique ID for gradient
    grad_id = f"grad-{label.lower().replace(' ', '')}"

    return f"""
    <div class="relative {container_class} flex items-center justify-center select-none transform transition-transform hover:scale-105 duration-500 mx-auto">
        <!-- SVG Ring -->
        <svg viewBox="0 0 {view_box_size} {view_box_size}" class="absolute inset-0 w-full h-full rotate-90" preserveAspectRatio="xMidYMid meet">
            <defs>
                <linearGradient id="{grad_id}" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="{color}" stop-opacity="0.4" />
                    <stop offset="100%" stop-color="{color}" />
                </linearGradient>
            </defs>
            <!-- Track -->
            <path d="{path_d}" fill="none" stroke="{color}" stroke-opacity="0.30" stroke-width="{stroke_width}" stroke-linecap="round" />
            <!-- Progress -->
            <path d="{path_d}" fill="none" stroke="url(#{grad_id})" stroke-width="{stroke_width}" stroke-linecap="round"
                  stroke-dasharray="{arc_length}" stroke-dashoffset="{dash_offset}"
                  style="transition: stroke-dashoffset 1s ease-out; {glow_style}" />
        </svg>
        
        <!-- Center Content -->
        <div class="absolute inset-0 flex flex-col items-center justify-center z-10 w-[84%] h-[84%] m-auto bg-white rounded-full shadow-soft border-[3px] border-white">
            <span class="{label_class} font-bold text-gray-400 uppercase tracking-widest">{label}</span>
            <span class="{value_class} font-black tracking-tight leading-none mt-1 sm:mt-2" style="color: {color}">{display_value}</span>
            {f'<span class="text-[0.6rem] sm:text-xs text-gray-400 font-medium mt-1">{sub_value}</span>' if sub_value else ''}
        </div>
    </div>
    """

def render_stat_bubble(label, value_or_icon, color_class, border_color_class, text_color_class=None, glow_class=None, is_icon=False):
    """
    Renders the StatBubble component.
    """
    # React uses Tailwind classes. We can pass them through or map hex to inline styles if needed.
    # Since we loaded Tailwind, we try to use classes where possible, but mapped to Python strings.
    
    content = ""
    if is_icon:
        content = f'<span class="material-icons-round {text_color_class or color_class} text-xl md:text-3xl">{value_or_icon}</span>'
    else:
        content = f'<span class="text-lg md:text-3xl font-black leading-none {text_color_class or color_class}">{value_or_icon}</span>'

    glow_html = f"hover:{glow_class}" if glow_class else ""
    
    return f"""
    <div class="group relative bubble flex items-center justify-center cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:scale-105">
      <!-- Outer Ring -->
      <div class="absolute inset-0 rounded-full border-[3px] md:border-4 {border_color_class} bg-white shadow-sm group-hover:shadow-lg transition-all duration-300 {glow_html}"></div>
      <!-- Inner Content -->
      <div class="relative w-full h-full flex flex-col items-center justify-center z-10">
        <span class="text-[0.5rem] md:text-[0.65rem] font-bold text-gray-400 uppercase leading-tight mb-0.5">{label}</span>
        {content}
      </div>
    </div>
    """

# --- 3. PUBLIC API (CONSUMERS) ---

def render_kpi_score(score):
    try: val = float(score)
    except: val = 0.0
    color = get_score_color(val)
    return generate_arc_svg(val, "SCORE", f"{val:.1f}", color, size='lg')

def render_kpi_drift(drift):
    try: val = float(drift)
    except: val = 0.0
    color = get_drift_color(val)
    # Drift 0% is good (100% fill visually? or 0% fill? React app logic implies 0% is good)
    # React App screenshot shows Drift 0.0% with a full or empty ring? 
    # Usually Drift is a penalty. Let's visualize it inversely or just as a value.
    # Visual preference: 0 drift = empty ring or full ring? 
    # Let's map 0-10% drift to 0-100% on the gauge for visualization scaling
    viz_val = min(val * 10, 100) 
    return generate_arc_svg(viz_val, "Drift", f"{val:.1f}%", color, size='sm')

def render_kpi_percentile(pct):
    try: val = float(pct)
    except: val = 0.0
    color = get_percentile_color(val)
    return generate_arc_svg(val, "Percentile", f"{val:.1f}%", color, size='sm')

# --- Bottom Row Bubbles ---

def quality_circle(q):
    if not isinstance(q, dict): 
        return render_stat_bubble("Quality", "?", "text-gray-400", "border-gray-200")
    
    label = q.get("label", "N/A").split()[0] # e.g. "Solid"
    color_hex = q.get("color", "#888")
    
    # Map hex to tailwind classes if possible or use arbitrary values style
    # Since we can't easily map dynamic hex to tailwind classes without safelist, 
    # we might need inline styles for specific colors if they aren't in config.
    # But Config.Theme has tailwind-friendly hexes.
    
    # Icon mapping based on label
    icon = "emoji_events" # Default Trophy
    
    # Using inline style for border-color since color comes from logic
    border_style = f"border-color: {color_hex};"
    text_style = f"color: {color_hex};"
    
    # We will use a wrapper to inject style since render_stat_bubble takes classes
    # We'll abuse the class parameter to inject style="..."
    
    return f"""
    <div class="group relative bubble flex items-center justify-center cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:scale-105">
      <div class="absolute inset-0 rounded-full border-[3px] md:border-4 bg-white shadow-sm group-hover:shadow-lg transition-all duration-300" style="border-color: {color_hex};"></div>
      <div class="relative w-full h-full flex flex-col items-center justify-center z-10">
        <span class="text-[0.5rem] md:text-[0.65rem] font-bold text-gray-400 uppercase leading-tight mb-0.5">Quality</span>
        <span class="material-icons-round text-xl md:text-3xl" style="color: {color_hex};">{icon}</span>
      </div>
    </div>
    """

def trend_circle(tr):
    direction = tr.get("direction", "flat")
    if direction == "up": 
        icon = "arrow_drop_up"
        color_class = "text-score-green"
        border_class = "border-score-green"
        glow = "shadow-glow-green"
    elif direction == "down": 
        icon = "arrow_drop_down"
        color_class = "text-score-red"
        border_class = "border-score-red"
        glow = "shadow-glow-red"
    else: 
        icon = "remove"
        color_class = "text-score-yellow"
        border_class = "border-score-yellow"
        glow = "shadow-glow-yellow"
        
    return render_stat_bubble("Trend", icon, color_class, border_class, glow_class=glow, is_icon=True)

def consistency_circle(cons_data):
    score = cons_data.get("score", 0) if cons_data else 0
    val_str = str(int(score))
    
    color_class = "text-score-red"
    border_class = "border-score-red"
    glow = "shadow-glow-red"
    
    if score >= 80:
        color_class = "text-score-green"
        border_class = "border-score-green"
        glow = "shadow-glow-green"
    elif score >= 60:
        color_class = "text-score-yellow"
        border_class = "border-score-yellow"
        glow = "shadow-glow-yellow"
        
    return render_stat_bubble("Constcy", val_str, color_class, border_class, glow_class=glow)

def efficiency_circle(ef_data):
    ef = ef_data.get("ef", 0) if ef_data else 0
    return render_stat_bubble("EF", f"{ef:.2f}", "text-score-blue", "border-score-blue")

def zones_circle_badge(zone_label, pct):
    """
    Renders the Z5 bubble with gradient border.
    """
    # Custom HTML for the gradient border bubble to match React
    return f"""
    <div class="group relative bubble flex items-center justify-center cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:scale-105">
        <div class="absolute inset-0 rounded-full bg-gradient-to-br from-score-red to-score-yellow p-[6px] md:p-[10px] shadow-sm group-hover:shadow-glow-red transition-all">
            <div class="w-full h-full bg-white rounded-full"></div>
        </div>
        <div class="relative w-full h-full flex flex-col items-center justify-center z-10">
            <span class="text-[0.5rem] md:text-[0.65rem] font-bold text-gray-400 uppercase leading-tight mb-0.5">
                {zone_label}
            </span>
            <span class="text-lg md:text-3xl font-black leading-none text-score-red">
                {zone_label}
            </span>
        </div>
    </div>
    """

# --- CHARTS & TABLES (Unchanged but ensuring imports) ---

def _apply_chart_style(chart):
    return chart.configure_view(strokeWidth=0).configure_axis(
        grid=False, domain=False, labelFont='Manrope', titleFont='Manrope', labelColor='#888', titleColor='#888'
    ).configure_legend(
        labelFont='Manrope', titleFont='Manrope', labelColor='#888', titleColor='#888'
    )

def render_zones_chart(zones, title="⚡ Zone Potenza"):
    if not zones: return
    df_zones = pd.DataFrame(list(zones.items()), columns=['Zona', 'Percentuale'])
    colors = [Config.Theme.SCORE_EPIC, Config.Theme.SCORE_EPIC, Config.Theme.SCORE_SOLID, Config.Theme.SCORE_SOLID, Config.Theme.SCORE_WEAK]
    chart = alt.Chart(df_zones).mark_bar(cornerRadiusEnd=5).encode(
        x=alt.X('Zona', sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Percentuale', title=None),
        color=alt.Color('Zona', scale=alt.Scale(range=colors), legend=None),
        tooltip=['Zona', 'Percentuale']
    ).properties(height=200, background='rgba(0,0,0,0)')
    st.altair_chart(_apply_chart_style(chart), width='stretch')

def render_scatter_chart(watts, hr):
    if not watts or not hr: return
    df = pd.DataFrame({'Watts': watts[::10], 'HR': hr[::10]}) 
    chart = alt.Chart(df).mark_circle(size=60, opacity=0.4).encode(
        x=alt.X('Watts', title='Power (W)'),
        y=alt.Y('HR', title='Heart Rate (bpm)', scale=alt.Scale(zero=False)),
        color=alt.value(Config.Theme.SCORE_GREAT),
        tooltip=['Watts', 'HR']
    ).interactive().properties(height=300, background='rgba(0,0,0,0)')
    st.altair_chart(_apply_chart_style(chart), width='stretch')

def render_history_table(df):
    if df.empty:
        st.text("Nessun dato.")
        return
    cols_to_show = ['Data', 'Dist (km)', 'Time', 'HR', 'Power', 'SCORE']
    available_cols = [c for c in cols_to_show if c in df.columns]
    display_df = df[available_cols].copy()
    if 'Data' in display_df.columns:
        display_df['Data'] = pd.to_datetime(display_df['Data']).dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        height=300,
        column_config={
            "SCORE": st.column_config.NumberColumn("Score", format="%.1f"),
            "Power": st.column_config.NumberColumn("Watt", format="%d w"),
            "HR": st.column_config.NumberColumn("FC", format="%d bpm"),
            "Dist (km)": st.column_config.NumberColumn("KM", format="%.1f km")
        }
    )

def render_trend_chart(df):
    if df.empty: return
    cols = ['Data', 'SCORE']
    if 'SCORE_MA_7' in df.columns: cols.append('SCORE_MA_7')
    chart_data = df[cols].copy().dropna(subset=["SCORE"]).sort_values("Data")
    y_col = 'SCORE_MA_7' if 'SCORE_MA_7' in df.columns else 'SCORE'
    
    base = alt.Chart(chart_data).encode(x='Data:T')
    line = base.mark_line(color=Config.Theme.SCORE_SOLID, strokeWidth=3).encode(y=alt.Y(y_col, scale=alt.Scale(zero=False), title=None))
    area = base.mark_area(
        line=False,
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color=Config.Theme.SCORE_SOLID, offset=0),
                   alt.GradientStop(color='rgba(255,255,255,0)', offset=1)],
            x1=1, x2=1, y1=1, y2=0
        ), opacity=0.2
    ).encode(y=alt.Y(y_col))
    
    st.altair_chart(_apply_chart_style(area + line), width='stretch')

# Stubs for compatibility
def render_trend_card(*args): pass
def get_coach_feedback(*args): return "..."
