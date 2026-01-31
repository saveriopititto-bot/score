import streamlit as st

def render_kpi_grid(cur_run, score_color):
    row_style = """
    <style>
        .stat-circle { transition: all 0.3s ease; }
        .stat-circle:hover { transform: scale(1.05); box-shadow: 0 15px 35px rgba(0,0,0,0.15) !important; }
        .score-circle-svg circle.progress { fill: none; stroke: #CDFAD5; stroke-width: 6; stroke-dasharray: 0, 1000; transition: stroke-dasharray 1s ease-out; }
        .score-circle-container:hover circle.progress { stroke-dasharray: 800, 1000; stroke: #6C5DD3; }
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
        pct_color = "#FF8080"
        if wr_pct_val > 75: pct_color = "#CDFAD5"
        elif wr_pct_val > 50: pct_color = "#F6FDC3"
        elif wr_pct_val > 25: pct_color = "#FFCF96"

        st.markdown(f"""
        <div style="display: flex; justify-content: center;">
            <div class="stat-circle" style="width: 155px; height: 155px; border-radius: 50%; border: 5px solid {pct_color}; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 5px 20px rgba(0,0,0,0.05);">
                <span style="color: #999; font-size: 0.70rem; font-weight: 700;">PERCENTILE</span>
                <span style="color: {pct_color}; font-size: 2.5rem; font-weight: 800; line-height: 1;">{wr_pct_val}%</span>
                <div style="background:{pct_color}22; color: #555; border: 1px solid {pct_color}; padding:2px 12px; border-radius:15px; font-size:0.65rem; font-weight:700; margin-top:5px;">RANKING</div>
            </div>
        </div>""", unsafe_allow_html=True)
    
    with c_score:
        clean_rank = str(cur_run['Rank']).split('/')[0].strip()
        cur_score = cur_run['SCORE']
        st.markdown(f"""
        <div class="score-circle-container" style="display: flex; justify-content: center; cursor: pointer;">
            <div style="position: relative; width: 230px; height: 230px;">
                <svg class="score-circle-svg" width="230" height="230" style="position: absolute; top:0; left:0; transform: rotate(-90deg);">
                    <circle cx="115" cy="115" r="110" stroke="#eee" stroke-width="6" fill="white" />
                    <circle class="progress" cx="115" cy="115" r="110" style="stroke: {score_color} !important;" />
                </svg>
                <div style="position: absolute; top:0; left:0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 10;">
                    <span style="color: #999; font-size: 0.9rem; font-weight: 700; letter-spacing: 1px;">SCORE</span>
                    <span style="color: #2D3436; font-size: 5rem; font-weight: 800; line-height: 0.9;">{cur_score}</span>
                    <div style="background:{score_color}25; color:#555; border: 1px solid {score_color}; padding:4px 16px; border-radius:20px; font-size:0.8rem; font-weight: 700; margin-top: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">{clean_rank}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    with c_drift:
        dec_val = cur_run.get('Decoupling', 0.0)
        dec_color = "#10B981"; drift_cat = "ECCELLENTE"
        if dec_val > 10.0: dec_color = "#991B1B"; drift_cat = "CRITICO"
        elif dec_val > 5.0: dec_color = "#EF4444"; drift_cat = "ATTENZIONE"
        elif dec_val > 3.0: dec_color = "#F59E0B"; drift_cat = "BUONO"

        st.markdown(f"""
        <div style="display: flex; justify-content: center;">
            <div class="stat-circle" style="width: 155px; height: 155px; border-radius: 50%; border: 5px solid {dec_color}; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 5px 20px rgba(0,0,0,0.05);">
                <span style="color: #999; font-size: 0.70rem; font-weight: 700;">DRIFT</span>
                <span style="color: {dec_color}; font-size: 2.5rem; font-weight: 800; line-height: 1;">{dec_val}%</span>
                <div style="background:{dec_color}22; color: #555; border: 1px solid {dec_color}; padding:2px 12px; border-radius:15px; font-size:0.65rem; font-weight:700; margin-top:5px;">{drift_cat}</div>
            </div>
        </div>""", unsafe_allow_html=True)
