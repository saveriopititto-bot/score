import streamlit as st
import time
from datetime import datetime
from config import Config

def render_top_section(auth_svc, db_svc):
    """
    Renders Sync Controls and Athlete Profile.
    Returns: physical_params (dict), start_sync (bool), days_to_fetch (int)
    """
    ath = st.session_state.strava_token.get("athlete", {})
    athlete_name = f"{ath.get('firstname', 'Atleta')} {ath.get('lastname', '')}"
    
    weight, hr_max, hr_rest, ftp, age, sex = Config.DEFAULT_WEIGHT, Config.DEFAULT_HR_MAX, Config.DEFAULT_HR_REST, Config.DEFAULT_FTP, Config.DEFAULT_AGE, "M"
    zones_data = None
    saved_profile = None

    if not st.session_state.demo_mode:
        token = st.session_state.strava_token["access_token"]
        athlete_id = ath.get("id")
        saved_profile = db_svc.get_athlete_profile(athlete_id)
        
        if saved_profile:
            weight = saved_profile.get('weight', weight)
            hr_max = saved_profile.get('hr_max', hr_max)
            hr_rest = saved_profile.get('hr_rest', hr_rest)
            ftp = saved_profile.get('ftp', ftp)
            age = saved_profile.get('age', age)
            sex = saved_profile.get('sex', sex)
        else:
            s_weight = ath.get('weight', 0)
            if s_weight: weight = float(s_weight)
            s_ftp = ath.get('ftp', 0) 
            if s_ftp: ftp = int(s_ftp)
            s_sex = ath.get('sex')
            if s_sex in ['M', 'F']: sex = s_sex 
            
            birthdate = ath.get('birthdate')
            if birthdate:
                try: age = datetime.now().year - int(str(birthdate).split("-")[0])
                except: pass

            if "strava_zones" not in st.session_state:
                st.session_state.strava_zones = auth_svc.fetch_zones(token)
            zones_data = st.session_state.strava_zones
            
            if zones_data:
                hr_zones = zones_data.get("heart_rate", {}).get("zones", [])
                if hr_zones:
                    extracted_max = hr_zones[-1].get("max")
                    if extracted_max and extracted_max > 0: hr_max = int(extracted_max)
                    elif age > 0: hr_max = int(208 - (0.7 * age))
                
                if ftp == Config.DEFAULT_FTP: 
                    pwr_zones = zones_data.get("power", {}).get("zones", [])
                    if len(pwr_zones) > 1:
                        z2_max = pwr_zones[1].get("max") 
                        if z2_max and z2_max > 0: ftp = int(z2_max / 0.75)

    # UI RENDERING
    st.markdown("<br>", unsafe_allow_html=True)
    col_controls, col_athlete = st.columns([1, 1], gap="large")
    
    start_sync = False
    days_to_fetch = 30 # Default

    with col_controls:
        c_sync_drop, c_sync_btn = st.columns([2, 1], gap="small", vertical_alignment="bottom")
        with c_sync_drop:
            time_options = {"30 Giorni": 30, "90 Giorni": 90, "12 Mesi": 365, "Storico": 3650}
            selected_label = st.selectbox("Periodo Analisi:", list(time_options.keys()), index=2)
            days_to_fetch = time_options[selected_label]
        with c_sync_btn:
            start_sync = st.button("🔄 AGGIORNA", type="primary", use_container_width=True, disabled=st.session_state.demo_mode)

    with col_athlete:
        st.markdown(f"**Benvenuto, {athlete_name}**")
        st.caption(f"ID Atleta Strava: {ath.get('id', 'N/A')}")
        
        with st.expander("⚙️ Modifica profilo atleta", expanded=False):
            st.markdown("""<div style="background:#fafafa; padding:20px; border-radius:16px; border:1px solid #eee;">""", unsafe_allow_html=True)
            with st.form("athlete_settings"):
                c1, c2, c3 = st.columns(3, gap="medium")
                with c1:
                    new_weight = st.number_input("Peso (kg)", value=float(weight), step=0.5)
                    new_age = st.number_input("Età", value=int(age))
                with c2:
                    new_hr_max = st.number_input("FC Max", value=int(hr_max))
                    new_hr_rest = st.number_input("FC Riposo", value=int(hr_rest))
                with c3:
                    new_ftp = st.number_input("FTP (W)", value=int(ftp))
                    new_sex = st.selectbox("Sesso", ["M", "F"], index=0 if sex == "M" else 1)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("💾 Salva profilo"):
                    if not st.session_state.demo_mode:
                        payload = {"id": int(ath.get("id")), "firstname": str(ath.get("firstname", "")), "lastname": str(ath.get("lastname", "")), "weight": float(new_weight), "hr_max": int(new_hr_max), "hr_rest": int(new_hr_rest), "ftp": int(new_ftp), "age": int(new_age), "sex": str(new_sex), "updated_at": datetime.now().isoformat()}
                        success, msg = db_svc.save_athlete_profile(payload)
                        if success:
                            st.success("✅ Profilo salvato!"); time.sleep(1); st.rerun()
                        else: st.error(f"❌ Errore DB: {msg}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        if saved_profile: st.caption("✅ Profilo caricato dal database.")
        elif zones_data: st.caption(f"ℹ️ Dati stimati (FTP ~{ftp}W, Età {age}). Clicca Salva per confermare.")

    phys_params = {
        "weight": weight, "hr_max": hr_max, "hr_rest": hr_rest,
        "age": age, "sex": sex, "ftp": ftp
    }
    return phys_params, start_sync, days_to_fetch
