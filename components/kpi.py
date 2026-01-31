import streamlit as st
from ui.style import SCORE_COLORS

def render_kpi_grid(cur_run, score_color_override=None):
    """
    Renders the main KPI grid using Circular Design (Restored).
    Uses Glassmorphic class for background consistency.
    """
    
    # CSS for Circles
    row_style = """
    <style>
        .stat-circle { 
            transition: all 0.3s ease; 
        }
        .stat-circle:hover { transform: scale(1.05); box-shadow: 0 15px 35px rgba(0,0,0,0.15) !important; }
        
        .score-circle-svg circle.progress { fill: none; stroke-width: 6; stroke-dasharray: 0, 1000; transition: stroke-dasharray 1s ease-out; }
        .score-circle-container:hover circle.progress { stroke-dasharray: 800, 1000; }
        
        @media (max-width: 768px) {
            .stat-circle { width: 110px !important; height: 110px !important; }
            .score-circle-container { transform: scale(0.75); transform-origin: center top; margin-bottom: -50px; }
        }
    </style>
    """
    st.markdown(row_style, unsafe_allow_html=True)

    c_pct, c_score, c_drift = st.columns([1, 2, 1], gap="small", vertical_alignment="center")
    
    wr_pct_val = cur_run.get('WR_Pct', 0.0)
    
    with c_pct:
        # Determine Color
        if wr_pct_val > 75: pct_color = SCORE_COLORS['good']
        elif wr_pct_val > 50: pct_color = SCORE_COLORS['ok']
        elif wr_pct_val > 25: pct_color = SCORE_COLORS['neutral']
        else: pct_color = SCORE_COLORS['bad']

        # Added "glass-card" class and forced border-radius 50%
        st.markdown(f"""
<div style="display: flex; justify-content: center;">
<div class="stat-circle glass-card" style="width: 155px; height: 155px; border-radius: 50%; border: 4px solid {pct_color}; display: flex; flex-direction: column; align-items: center; justify-content: center; padding:0;">
<span style="opacity: 0.7; font-size: 0.70rem; font-weight: 700;">PERCENTILE</span>
<span style="color: {pct_color}; font-size: 2.5rem; font-weight: 800; line-height: 1;">{wr_pct_val}%</span>
<div style="background:{pct_color}22; opacity:0.8; border: 1px solid {pct_color}; padding:2px 12px; border-radius:15px; font-size:0.65rem; font-weight:700; margin-top:5px;">RANKING</div>
</div>
</div>""", unsafe_allow_html=True)
    
    with c_score:
        clean_rank = str(cur_run['Rank']).split('/')[0].strip()
        cur_score = cur_run['SCORE']
        
        # Use valid color from palette
        s_col = score_color_override if score_color_override else SCORE_COLORS['neutral']

        st.markdown(f"""
<div class="score-circle-container" style="display: flex; justify-content: center; cursor: pointer;">
<div style="position: relative; width: 230px; height: 230px;">
<svg class="score-circle-svg" width="230" height="230" style="position: absolute; top:0; left:0; transform: rotate(-90deg);">
<circle cx="115" cy="115" r="110" stroke="rgba(128,128,128,0.2)" stroke-width="6" fill="transparent" />
<circle class="progress" cx="115" cy="115" r="110" style="stroke: {s_col} !important;" />
</svg>
<div class="glass-card" style="position: absolute; top:15px; left:15px; width: 200px; height: 200px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 10; padding:0; box-shadow:none; border:none;">
<span style="opacity: 0.7; font-size: 0.9rem; font-weight: 700; letter-spacing: 1px;">SCORE</span>
<span style="color: {s_col}; font-size: 5rem; font-weight: 800; line-height: 0.9;">{cur_score}</span>
<div style="background:{s_col}25; opacity:0.9; border: 1px solid {s_col}; padding:4px 16px; border-radius:20px; font-size:0.8rem; font-weight: 700; margin-top: 10px;">{clean_rank}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

    with c_drift:
        dec_val = cur_run.get('Decoupling', 0.0)
        # Determine Color
        if dec_val > 5.0: dec_color = SCORE_COLORS['bad']
        elif dec_val > 3.0: dec_color = SCORE_COLORS['ok'] # Was ok
        else: dec_color = SCORE_COLORS['good'] # Excellent
        
        drift_cat = "ECCELLENTE" if dec_val <= 3 else "BUONO" if dec_val <= 5 else "ATTENZIONE"

        st.markdown(f"""
<div style="display: flex; justify-content: center;">
<div class="stat-circle glass-card" style="width: 155px; height: 155px; border-radius: 50%; border: 4px solid {dec_color}; display: flex; flex-direction: column; align-items: center; justify-content: center; padding:0;">
<span style="opacity: 0.7; font-size: 0.70rem; font-weight: 700;">DRIFT</span>
<span style="color: {dec_color}; font-size: 2.5rem; font-weight: 800; line-height: 1;">{dec_val}%</span>
<div style="background:{dec_color}22; opacity:0.8; border: 1px solid {dec_color}; padding:2px 12px; border-radius:15px; font-size:0.65rem; font-weight:700; margin-top:5px;">{drift_cat}</div>
</div>
</div>""", unsafe_allow_html=True)
