import streamlit as st
import pandas as pd
import altair as alt
from ui.style import SCORE_COLORS

# --- HELPER COMPONENTS ---

def get_coach_feedback(trend_direction):
    if trend_direction == "up": return "Stai entrando in una fase di miglioramento."
    if trend_direction == "down": return "Segnale di affaticamento. Oggi meglio controllare."
    return "Allenamento stabile. Buon controllo."

def render_quality_badge(label, color_key="neutral"):
    """
    Renders a pulsing quality badge
    """
    if color_key in ["purple", "blue", "green"]: c = SCORE_COLORS['good']
    elif color_key in ["teal", "yellow"]: c = SCORE_COLORS['ok']
    elif color_key in ["red"]: c = SCORE_COLORS['bad']
    else: c = SCORE_COLORS['neutral']

    st.markdown(f"""
<div style="text-align:center; padding: 20px;">
<div style="font-size:0.8rem; letter-spacing:1px; margin-bottom:10px; opacity:0.7;">QUALITY</div>
<div style="
display: inline-block;
padding: 10px 24px;
background: {c}20;
border: 1px solid {c};
color: {c};
border-radius: 12px;
font-weight: 800;
font-size: 1.2rem;
animation: pulse 2s infinite;
">
{label}
</div>
</div>
""", unsafe_allow_html=True)

def render_trend_card(delta):
    """
    Renders the Trend Card
    """
    if delta > 3: 
        col = SCORE_COLORS['good']
        icon = "📈"
    elif delta < -3: 
        col = SCORE_COLORS['bad']
        icon = "📉"
    else: 
        col = SCORE_COLORS['ok']
        icon = "⚖️"
        
    st.markdown(f"""
<div class="glass-card" style="text-align:center; height: 100%;">
<div style="font-size:0.8rem; font-weight:700; opacity:0.6;">RECENT TREND</div>
<div style="font-size:2rem; font-weight:800; margin: 10px 0; color:{col};">
{icon} {delta}
</div>
<div style="font-size:0.8rem; opacity:0.8;">vs Previous Average</div>
</div>
""", unsafe_allow_html=True)

def quality_circle(q):
    # Ensure q is a dict, robust fallback
    if not isinstance(q, dict):
         label = str(q) if q else "N/A"
         color = "#FFCF96"
    else:
         label = q.get("label", "N/A").split()[0]
         label_full = q.get("label", "N/A")
         
         color_map = {
             "LEGENDARY": "#FF8080", "EPIC": "#FFCF96",
             "GREAT": "#CDFAD5", "SOLID": "#F6FDC3",
             "OK": "#F6FDC3", "WEAK": "#FFCF96", "WASTED": "#FF8080"
         }
         # Try precise match first, then by key
         color = "#FFCF96"
         for k,v in color_map.items():
             if k in label_full: 
                 color = v
                 break
                 
    return f"""
    <div style="display:flex; justify-content:center;">
      <div class="stat-circle" style="width:130px;height:130px;border:5px solid {color};">
        <span style="font-size:0.65rem;color:#999;font-weight:700;">QUALITY</span>
        <span style="font-size:1.4rem;font-weight:900;color:{color};line-height:1;">{label}</span>
      </div>
    </div>
    """

def trend_circle(tr):
    direction = tr.get("direction", "flat")
    if direction == "up": icon, color = "▲", "#CDFAD5"
    elif direction == "down": icon, color = "▼", "#FF8080"
    else: icon, color = "●", "#FFCF96"
    return f"""
    <div style="display:flex; justify-content:center;">
      <div class="stat-circle" style="width:120px;height:120px;border:4px solid {color};">
        <span style="font-size:2.1rem;font-weight:900;color:{color};">{icon}</span>
        <span style="font-size:0.65rem;color:#999;">TREND</span>
      </div>
    </div>
    """

def comparison_circle(cp):
    rank = cp.get("rank", 0)
    total = cp.get("total", 0)
    if rank == 0: # No data
         color = "#F6FDC3"
         text = "-/-"
    else:
         if rank <= 3: color = "#CDFAD5"
         elif rank <= 7: color = "#F6FDC3"
         else: color = "#FF8080"
         text = f"{rank}/{total}"
         
    return f"""
    <div style="display:flex; justify-content:center;">
      <div class="stat-circle" style="width:120px;height:120px;border:4px solid {color};">
        <span style="font-size:1.6rem;font-weight:900;color:{color};">{text}</span>
        <span style="font-size:0.65rem;color:#999;">LAST 10</span>
      </div>
    </div>
    """

# --- CHARTS ---

def _apply_chart_style(chart):
    return chart.configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False,
        domain=False,
        labelFont='Manrope',
        titleFont='Manrope',
        labelColor='#888',
        titleColor='#888'
    ).configure_legend(
        labelFont='Manrope',
        titleFont='Manrope',
        labelColor='#888',
        titleColor='#888'
    ).properties(
        
    )

def render_benchmark_chart(df):
    st.markdown("##### 📊 Distribuzione Punteggi")
    if df.empty:
        st.info("Dati insufficienti.")
        return

    base = alt.Chart(df).encode(
        x=alt.X('SCORE:Q', bin=alt.Bin(maxbins=10), title='Score'),
        y=alt.Y('count()', title='Frequency')
    )
    chart = base.mark_bar(color=SCORE_COLORS['neutral'], cornerRadiusTopLeft=5, cornerRadiusTopRight=5).properties(
        height=200,
        background='rgba(0,0,0,0)'
    )
    
    st.altair_chart(_apply_chart_style(chart), use_container_width=True)

def render_zones_chart(zones):
    st.markdown("##### ⚡ Zone Potenza")
    if not zones:
        st.info("Dati di potenza non disponibili.")
        return

    df_zones = pd.DataFrame(list(zones.items()), columns=['Zona', 'Percentuale'])
    
    # Custom Palette for Zones
    colors = [SCORE_COLORS['ok'], SCORE_COLORS['ok'], SCORE_COLORS['neutral'], SCORE_COLORS['neutral'], SCORE_COLORS['bad']]
    
    chart = alt.Chart(df_zones).mark_bar(cornerRadiusEnd=5).encode(
        x=alt.X('Zona', sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Percentuale', title=None),
        color=alt.Color('Zona', scale=alt.Scale(range=colors), legend=None),
        tooltip=['Zona', 'Percentuale']
    ).properties(
        height=200,
        background='rgba(0,0,0,0)'
    )

    st.altair_chart(_apply_chart_style(chart), use_container_width=True)

def render_scatter_chart(watts, hr):
    st.markdown("##### ❤️ Power vs HR")
    if not watts or not hr:
        st.info("Stream dati mancanti.")
        return

    df = pd.DataFrame({'Watts': watts[::10], 'HR': hr[::10]}) # Sampled
    
    chart = alt.Chart(df).mark_circle(size=60, opacity=0.4).encode(
        x=alt.X('Watts', title='Power (W)'),
        y=alt.Y('HR', title='Heart Rate (bpm)', scale=alt.Scale(zero=False)),
        color=alt.value(SCORE_COLORS['neutral']),
        tooltip=['Watts', 'HR']
    ).interactive().properties(
        height=300,
        background='rgba(0,0,0,0)'
    )
    
    st.altair_chart(_apply_chart_style(chart), use_container_width=True)

def render_history_table(df):
    if df.empty:
        st.text("Nessun dato.")
        return

    cols_to_show = ['Data', 'Dist (km)', 'Power', 'HR', 'SCORE', 'Rank']
    available_cols = [c for c in cols_to_show if c in df.columns]
    
    display_df = df[available_cols].copy()
    display_df['Data'] = pd.to_datetime(display_df['Data']).dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "SCORE": st.column_config.NumberColumn("Score", format="%.2f"),
            "Power": st.column_config.NumberColumn("Watt", format="%d w"),
             "HR": st.column_config.NumberColumn("FC", format="%d bpm")
        }
    )

def render_trend_chart(df):
    st.markdown("##### 📈 Smart Trend")
    if df.empty:
        st.info("Nessun dato SCORE disponibile.")
        return

    cols = ['Data', 'SCORE']
    if 'SCORE_MA_7' in df.columns: cols.append('SCORE_MA_7')
        
    chart_data = df[cols].copy().dropna(subset=["SCORE"]).sort_values("Data")
    chart_data['Data'] = pd.to_datetime(chart_data['Data'])
    
    y_col = 'SCORE_MA_7' if 'SCORE_MA_7' in df.columns else 'SCORE'

    base = alt.Chart(chart_data).encode(x='Data:T')

    # Line Chart using Neutral Color (Focus)
    line = base.mark_line(color=SCORE_COLORS['neutral'], strokeWidth=3).encode(
        y=alt.Y(y_col, scale=alt.Scale(zero=False), title=None)
    )
    
    # Area gradient
    area = base.mark_area(
        line=False,
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color=SCORE_COLORS['neutral'], offset=0),
                   alt.GradientStop(color='rgba(255,255,255,0)', offset=1)],
            x1=1, x2=1, y1=1, y2=0
        ),
        opacity=0.2
    ).encode(y=alt.Y(y_col))

    points = base.mark_circle(color=SCORE_COLORS['good']).encode(
        y=y_col, tooltip=['Data', y_col]
    )

    chart = (area + line + points).properties(
        height=250,
        background='rgba(0,0,0,0)'
    )
    
    st.altair_chart(_apply_chart_style(chart), use_container_width=True)
