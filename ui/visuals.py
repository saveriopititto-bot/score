import streamlit as st
import pandas as pd
import altair as alt

# ... (le altre funzioni render_benchmark, render_zones etc rimangono uguali) ...

def render_trend_chart(df):
    """
    Mostra SCORE grezzo e Media Mobile (MA7).
    """
    st.markdown("##### 📈 Trend Intelligente (Score vs Media 7gg)")

    if df.empty:
        st.info("Nessun dato SCORE disponibile.")
        return

    # Preparazione dati pulita
    chart_data = df[['Data', 'SCORE', 'SCORE_MA_7']].copy()
    chart_data['Data'] = pd.to_datetime(chart_data['Data'])
    
    # Pulizia
    chart_data = (
        chart_data
        .dropna(subset=["SCORE"])
        .set_index('Data')
        .sort_index()
    )
    
    # Rinominiamo per la legenda
    chart_data = chart_data.rename(columns={
        'SCORE': 'Score Giornaliero', 
        'SCORE_MA_7': 'Trend (Media 7gg)'
    })

    # Grafico Linee Multiplo (Nativo Streamlit = Bulletproof)
    # Mostra due linee colorate diversamente
    st.line_chart(
        chart_data, 
        color=["#FFCF96", "#FF8080"], # Arancio chiaro (Day), Rosso forte (Trend)
        height=250 # Un po' più alto per apprezzare i dettagli
    )
