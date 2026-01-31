import streamlit as st
from ui.style import SCORE_COLORS

def render_kpi_grid(cur_run, score_color_override=None):
    """
    Renders the main KPI grid using the Glassmorphic Design System.
    """
    
    # Extract values
    cur_score = cur_run['SCORE']
    rank = str(cur_run['Rank']).split('/')[0].strip()
    wr_pct_val = cur_run.get('WR_Pct', 0.0)
    dec_val = cur_run.get('Decoupling', 0.0)
    
    # 1. HERO SCORE
    # Using the specific HTML structure from the design system
    
    c_pct, c_score, c_drift = st.columns([1, 1.2, 1], gap="medium", vertical_alignment="center")
    
    with c_score:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center; position: relative; overflow: hidden;">
            <div style="font-size:0.75rem; letter-spacing:3px; opacity:0.6; font-weight: 700; margin-bottom: 10px;">SCORE</div>
            <div style="font-size:5rem; font-weight:800; color:{SCORE_COLORS['neutral']}; line-height: 1;">{cur_score}</div>
            <div style="margin-top: 15px;">
                <span style="background:{SCORE_COLORS['neutral']}25; border:1px solid {SCORE_COLORS['neutral']}; padding:6px 18px; border-radius:999px; font-weight:700; font-size:0.8rem; color: {SCORE_COLORS['neutral']};">
                    {rank}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_pct:
        # Determine Color
        if wr_pct_val > 75: col = SCORE_COLORS['good']
        elif wr_pct_val > 50: col = SCORE_COLORS['ok']
        elif wr_pct_val > 25: col = SCORE_COLORS['neutral']
        else: col = SCORE_COLORS['bad']
        
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
             <div style="font-size:0.7rem; font-weight:700; opacity:0.6;">PERCENTILE</div>
             <div style="font-size:2.5rem; font-weight:800; color:{col};">{wr_pct_val}%</div>
             <div style="font-size:0.8rem; opacity:0.7;">di atleti simili</div>
        </div>
        """, unsafe_allow_html=True)

    with c_drift:
        # Determine Color for Drift
        if dec_val > 5.0: col = SCORE_COLORS['bad']
        elif dec_val > 3.0: col = SCORE_COLORS['ok']
        else: col = SCORE_COLORS['good'] # Excellent
        
        label = "ECCELLENTE" if dec_val <= 3 else "BUONO" if dec_val <= 5 else "ATTENZIONE"

        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
             <div style="font-size:0.7rem; font-weight:700; opacity:0.6;">EFFICIENZA</div>
             <div style="font-size:2.5rem; font-weight:800; color:{col};">{dec_val}%</div>
             <div style="font-size:0.8rem; font-weight:700; color:{col};">{label}</div>
        </div>
        """, unsafe_allow_html=True)
