import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from config import Config
from engine.core import ScoreEngine, RunMetrics
from ui.legal import render_legal_section
from ui.visuals import render_history_table, render_trend_chart, render_scatter_chart, render_zones_chart, render_quality_badge, render_trend_card, get_coach_feedback, quality_circle, trend_circle, comparison_circle
from ui.feedback import render_feedback_form

# Components
from components.header import render_header
from components.athlete import render_top_section
from components.kpi import render_kpi_grid

def render_dashboard(auth_svc, db_svc):
    # 1. HEADER
    render_header()

    # 2. TOP SECTION (Profile & Controls)
    phys_params, start_sync, days_to_fetch = render_top_section(auth_svc, db_svc)
    ftp = phys_params.get('ftp', Config.DEFAULT_FTP)
    
    # Context for later use
    ath = st.session_state.strava_token.get("athlete", {})
    athlete_name = f"{ath.get('firstname', 'Atleta')} {ath.get('lastname', '')}"

    # --- ENGINE (Sync Logic) ---
    if start_sync and not st.session_state.demo_mode:
        token = st.session_state.strava_token["access_token"]
        athlete_id = ath.get("id")
        
        # Import the robust sync function
        from services.strava_sync import safe_strava_sync
        
        with st.spinner(f"Sync Strava sicuro (Engine {Config.ENGINE_VERSION})..."):
            res = safe_strava_sync(
                auth_svc,
                db_svc,
                ScoreEngine(),
                token,
                athlete_id,
                phys_params.get('weight', Config.DEFAULT_WEIGHT),
                phys_params.get('hr_max', Config.DEFAULT_HR_MAX),
                phys_params.get('hr_rest', Config.DEFAULT_HR_REST),
                phys_params.get('age', Config.DEFAULT_AGE),
                phys_params.get('sex', 'M'),
                days_to_fetch
            )
            
            if res['new'] > 0:
                st.success(f"✅ Sync completato: {res['new']} nuove corse, {res['updated']} aggiornate, {res['skipped']} già presenti")
                time.sleep(1)
                st.session_state.data = db_svc.get_history()  # Refresh data
                st.rerun()
            else:
                st.info(f"Database già aggiornato. {res['skipped']} corse già presenti.")

    # --- VISUALIZZAZIONE DASHBOARD ---
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        if pd.api.types.is_datetime64_any_dtype(df['Data']) and df['Data'].dt.tz is not None:
             df['Data'] = df['Data'].dt.tz_localize(None)

        df = df.sort_values("Data", ascending=True)
        df["SCORE_MA_7"] = df["SCORE"].rolling(7, min_periods=1).mean()
        df["SCORE_MA_28"] = df["SCORE"].rolling(28, min_periods=1).mean()
        df = df.sort_values("Data", ascending=False)
        
        if 'days_to_fetch' in locals():
            cutoff = datetime.now() - timedelta(days=days_to_fetch)
            df = df[df['Data'] > cutoff]
        
        if df.empty:
            st.warning("Nessuna corsa nel periodo selezionato.")
        else:
            cur_run = df.iloc[0]
            cur_score, cur_ma7 = cur_run['SCORE'], cur_run['SCORE_MA_7']
            delta_val = (cur_ma7 - df.iloc[1]['SCORE_MA_7']) if len(df) > 1 else 0
            
            score_color = "#FFCF96" # Statico
            if delta_val > 0.005: score_color = "#CDFAD5" 
            elif delta_val < -0.005: score_color = "#FF8080" 

            eng = ScoreEngine()
            
            # --- DEBUG TEMPORANEO ---
            if st.checkbox("Mostra Debug Engine", value=False):
                 st.write(f"Has gaming_feedback: {hasattr(eng, 'gaming_feedback')}")

            st.divider()

            # --- MIDDLE SECTION: METRICHE PRINCIPALI (KPI) ---
            render_kpi_grid(cur_run, score_color)

            # --- DEBUG LOGS FOR SCORE FORMULA ---
            with st.expander("⚙️ Score Process Logs (Debug Fomula)", expanded=False):
                st.write("**Dati Corsa (Input)**")
                st.json({
                    "Date": str(cur_run['Data']),
                    "Distance": cur_run['Dist (km)'],
                    "Power (Avg)": cur_run['Power'],
                    "HR (Avg)": cur_run['HR'],
                    "Drift (Decoupling)": cur_run['Decoupling'],
                    "Weight": phys_params.get('weight'),
                    "Age": phys_params.get('age')
                })
                st.write("**Dettagli Calcolo Score**")
                st.json(cur_run.get('SCORE_DETAIL', {}))
                st.write("**Raw Row Data**")
                st.json(cur_run.to_dict())
            
            st.divider()

            # --- GAMING FEEDBACK LAYER (from DB) ---
            cur_quality = cur_run.get("Quality")
            cur_achievements = cur_run.get("Achievements", [])
            cur_trend = cur_run.get("Trend", {})
            cur_comparison = cur_run.get("Comparison", {})
            
            # Fallback
            if not cur_quality or not cur_trend:
                scores_hist = df['SCORE'].dropna().tolist()[::-1]
                feedback = eng.gaming_feedback(scores_hist) if scores_hist else {}
            else:
                feedback = {
                    "quality": {"label": cur_quality, "color": eng.run_quality(cur_run['SCORE'])['color']} if isinstance(cur_quality, str) else cur_quality,
                    "achievements": cur_achievements,
                    "trend": cur_trend,
                    "comparison": cur_comparison
                }
            
            if feedback:
                st.markdown("### 🎮 Performance Feedback")
                
                # Use Stat Circles Layout
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(quality_circle(feedback.get("quality", {})), unsafe_allow_html=True)
                with c2: st.markdown(trend_circle(feedback.get("trend", {})), unsafe_allow_html=True)
                with c3: st.markdown(comparison_circle(feedback.get("comparison", {})), unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- Original details/logs kept below ---
                if feedback.get('achievements'):
                    with st.expander("🏅 Achievements", expanded=True):
                        for a in feedback['achievements']:
                            st.markdown(f"**{a}**")
                
                # Debug Log Button preserved in a discreet way
                with st.expander("⚙️ Feedback Logs"):
                    st.json(feedback)
                    q = feedback['quality']
                    render_quality_badge(q['label'], q['color'])
                    


            st.divider()

            # --- BOTTOM SECTION: GRAFICI ---
            st.markdown("### 🔬 Analisi & Trend")
            col_g1, col_g2, col_g3 = st.columns(3, gap="medium")
            
            with col_g1:
                st.markdown("##### 📈 Trend SCORE")
                if len(df) > 1:
                    render_trend_chart(df.head(60))
            
            with col_g2:
                st.markdown("##### 📍 Power vs HR")
                opts = {r['id']: f"{r['Data'].strftime('%Y-%m-%d')} - {r['Dist (km)']}km" for i, r in df.iterrows()}
                sel = st.selectbox("Seleziona attività:", list(opts.keys()), format_func=lambda x: opts[x], key="sel_scatter")
                run_scatter = df[df['id'] == sel].iloc[0].to_dict()
                render_scatter_chart(run_scatter.get('raw_watts', []), run_scatter.get('raw_hr', []))
                st.caption(f"Drift: {run_scatter['Decoupling']}%")

            with col_g3:
                st.markdown("##### 📊 Zone Intensità")
                run_zones = df[df['id'] == sel].iloc[0].to_dict() 
                zones_c = ScoreEngine().calculate_zones(run_zones.get('raw_watts', []), ftp)
                render_zones_chart(zones_c)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # --- SEZIONE DETTAGLI & ARCHIVIO ---
            c_break, c_arch = st.columns([1, 1], gap="large")
            with c_break:
                with st.expander("🔬 Perché questo punteggio? (Breakdown)", expanded=False):
                    details = cur_run.get("SCORE_DETAIL")
                    if not details or not isinstance(details, dict):
                         # Note: using 0 for optional params to metrics, just fallback
                         m_tmp = RunMetrics(cur_run['Power'], cur_run['HR'], cur_run['Dist (km)']*1000, 0, 0, phys_params['weight'], phys_params['hr_max'], phys_params['hr_rest'], 20, 50)
                         _, details, _, _, _ = eng.compute_score(m_tmp, cur_run['Decoupling']/100)
                    d1, d2 = st.columns(2)
                    with d1: st.metric("🚀 Potenza", f"+{details.get('Potenza', 0)}%")
                    with d2: st.metric("🔋 Volume", f"+{details.get('Volume', 0)}%")
                    d3, d4 = st.columns(2)
                    with d3: st.metric("💓 Intensità", f"+{details.get('Intensità', 0)}%")
                    with d4: st.metric("📉 Efficienza", f"{details.get('Malus Efficienza', 0)}")
            
            with c_arch:
                with st.expander("📂 Archivio Attività Completo", expanded=False):
                    render_history_table(df)

            st.divider()

            # --- D. FEEDBACK & LEGENDA ---
            c_feed, c_leg = st.columns([1, 1], gap="large")
            with c_feed:
                 with st.expander("🐞 Segnala un Bug / Idea", expanded=False):
                    render_feedback_form(db_svc, ath.get("id"), athlete_name)
                    
                    st.divider()
                    st.markdown("##### 🗑️ Zona Pericolo")
                    if st.button("Reset Totale Database (Cancella e Ricarica)", type="primary"):
                        if db_svc.reset_history(ath.get("id")):
                             st.session_state.data = []
                             st.success("Database resettato. Ricarica la pagina per risincronizzare.")
                             time.sleep(2)
                             st.rerun()
                        else:
                             st.error("Errore durante il reset.")
            with c_leg:
                 with st.expander("ℹ️ Legenda Metriche", expanded=False):
                     st.markdown("""
                     **Efficienza (Drift):**
                     - <span style="color:#10B981">●</span> <3% Eccellente
                     - <span style="color:#F59E0B">●</span> 3-5% Buono
                     - <span style="color:#EF4444">●</span> >5% Attenzione
                     - <span style="color:#991B1B">●</span> >10% Critico
                     **Percentile:** Confronto con atleti della tua età.
                     """, unsafe_allow_html=True)
            
            render_legal_section()
