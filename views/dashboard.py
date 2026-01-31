import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from config import Config
from engine.core import ScoreEngine, RunMetrics
from controllers.sync_controller import SyncController
from ui.legal import render_legal_section
from ui.visuals import render_history_table, render_trend_chart, render_scatter_chart, render_zones_chart, render_quality_badge, render_trend_card, get_coach_feedback
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
        
        # Prepare context (history for gaming feedback)
        existing_data = st.session_state.data or []
        existing_ids = [r['id'] for r in existing_data]
        scores_asc = [r['SCORE'] for r in existing_data][::-1] 

        # Calculate last_import_timestamp from the latest run in DB
        last_import_timestamp = None
        if existing_data:
            try:
                # We assume "Data" is YYYY-MM-DD
                dates = [datetime.strptime(r['Data'], "%Y-%m-%d") for r in existing_data if r.get('Data')]
                if dates:
                    max_date = max(dates)
                    last_import_timestamp = int(max_date.timestamp())
            except Exception as e:
                # Fallback to None if date parsing fails
                pass

        ctrl = SyncController(auth_svc, db_svc)
        
        with st.spinner(f"Analisi attività Strava con Engine {Config.ENGINE_VERSION}..."):
            bar = st.progress(0)
            count, msg = ctrl.run_sync(
                token, athlete_id, phys_params, days_to_fetch, 
                existing_ids, scores_asc, progress_bar=bar,
                last_import_timestamp=last_import_timestamp
            )
            
            if count > 0:
                st.success(msg)
                time.sleep(1)
                st.session_state.data = db_svc.get_history() # Refresh data
                st.rerun()
            elif count == 0:
                 st.info("Database già aggiornato.")
            else:
                 st.warning(msg)

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
                c_qual, c_trend, c_comp = st.columns([1.2, 1.2, 1.6], gap="medium")
                
                with c_qual:
                    q = feedback['quality']
                    render_quality_badge(q['label'], q['color'])
                    
                    if feedback['achievements']:
                        with st.expander("🏅 Achievements", expanded=True):
                            for a in feedback['achievements']:
                                st.markdown(f"**{a}**")

                with c_trend:
                    tr = feedback['trend']
                    render_trend_card(tr['delta'])
                    
                    # Microcopy Coach Feedback
                    msg = get_coach_feedback("up" if tr['delta'] > 3 else "down" if tr['delta'] < -3 else "flat")
                    st.caption(f"🧠 {msg}")
                
                with c_comp:
                    cp = feedback['comparison']
                    if cp:
                        st.markdown(f"""
<div class="glass-card">
<span style="color:#666; font-size:0.8rem; font-weight:700;">VS LAST 10 RUNS</span><br>
<div style="display:flex; justify-content:space-between; margin-top:5px;">
<span>Media: <b>{'+' if cp['vs_avg'] > 0 else ''}{cp['vs_avg']}</b></span>
<span>Best: <b>{'+' if cp['vs_best'] > 0 else ''}{cp['vs_best']}</b></span>
</div>
<div style="margin-top:8px; font-size:0.9rem;">Rank: <b>#{cp['rank']}</b> di {cp['total']}</div>
</div>
""", unsafe_allow_html=True)

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
