import streamlit as st
import pandas as pd
import altair as alt

def render_benchmark_chart(df):
    """
    Istogramma della distribuzione degli SCORE.
    """
    st.markdown("##### 📊 Distribuzione Punteggi")
    if df.empty:
        st.info("Dati insufficienti.")
        return

    base = alt.Chart(df).encode(
        x=alt.X('SCORE:Q', bin=alt.Bin(maxbins=10), title='Score'),
        y=alt.Y('count()', title='Freq')
    )
    chart = base.mark_bar(color='#CDFAD5', cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
    st.altair_chart(chart, use_container_width=True)

def render_zones_chart(zones):
    """
    Grafico a barre delle zone di potenza (Z1-Z5).
    """
    st.markdown("##### ⚡ Zone Potenza")
    if not zones:
        st.info("Dati di potenza non disponibili.")
        return

    df_zones = pd.DataFrame(list(zones.items()), columns=['Zona', 'Percentuale'])
    
    # Colori per le zone: Z1 (Grigio) -> Z5 (Rosso)
    colors = ['#E0E0E0', '#90CAF9', '#A5D6A7', '#FFCC80', '#EF9A9A']
    
    chart = alt.Chart(df_zones).mark_bar().encode(
        x=alt.X('Zona', sort=None),
        y=alt.Y('Percentuale'),
        color=alt.Color('Zona', scale=alt.Scale(range=colors), legend=None),
        tooltip=['Zona', 'Percentuale']
    )
    st.altair_chart(chart, use_container_width=True)

def render_scatter_chart(watts, hr):
    """
    Scatter plot Potenza vs Cuore.
    """
    st.markdown("##### ❤️ Accoppiamento Potenza/Cuore")
    if not watts or not hr:
        st.info("Stream dati mancanti.")
        return

    # Creiamo un df ridotto (campioniamo 1 ogni 5 secondi per velocità)
    df = pd.DataFrame({'Watts': watts[::5], 'HR': hr[::5]})
    
    chart = alt.Chart(df).mark_circle(size=60, opacity=0.3).encode(
        x=alt.X('Watts', title='Potenza (W)'),
        y=alt.Y('HR', title='Frequenza Cardiaca (bpm)', scale=alt.Scale(zero=False)),
        color=alt.value('#6C5DD3'),
        tooltip=['Watts', 'HR']
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)

def render_history_table(df):
    """
    Tabella interattiva con le ultime attività.
    """
    if df.empty:
        st.text("Nessun dato.")
        return

    # Selezioniamo e ordiniamo le colonne per la visualizzazione
    cols_to_show = ['Data', 'Dist (km)', 'Power', 'HR', 'SCORE', 'Rank']
    # Controlliamo che esistano tutte (per evitare KeyError su vecchi dati)
    available_cols = [c for c in cols_to_show if c in df.columns]
    
    display_df = df[available_cols].copy()
    display_df['Data'] = pd.to_datetime(display_df['Data']).dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "SCORE": st.column_config.NumberColumn(
                "Score",
                format="%.2f"
            ),
            "Power": st.column_config.NumberColumn(
                "Watt",
                format="%d w"
            ),
             "HR": st.column_config.NumberColumn(
                "FC",
                format="%d bpm"
            )
        }
    )

def render_trend_chart(df):
    """
    Mostra SCORE grezzo e Media Mobile (MA7).
    Versione 'Intelligente' con st.line_chart nativo.
    """
    st.markdown("##### 📈 Trend Intelligente (Score vs Media 7gg)")

    if df.empty:
        st.info("Nessun dato SCORE disponibile.")
        return

    # Preparazione dati pulita
    # Nota: Assicurati che SCORE_MA_7 esista nel DF (viene calcolato in app.py)
    cols = ['Data', 'SCORE']
    if 'SCORE_MA_7' in df.columns:
        cols.append('SCORE_MA_7')
        
    chart_data = df[cols].copy()
    chart_data['Data'] = pd.to_datetime(chart_data['Data'])
    
    # Pulizia
    chart_data = (
        chart_data
        .dropna(subset=["SCORE"])
        .set_index('Data')
        .sort_index()
    )
    
    # Rinominiamo per la legenda
    rename_map = {'SCORE': 'Score Giornaliero'}
    if 'SCORE_MA_7' in df.columns:
        rename_map['SCORE_MA_7'] = 'Trend (Media 7gg)'
        
    chart_data = chart_data.rename(columns=rename_map)

    # Grafico Linee Multiplo (Nativo Streamlit = Bulletproof)
    # Mostra due linee colorate diversamente
    # Se manca la media mobile (vecchi dati), mostra solo una linea
    colors = ["#FFCF96", "#FF8080"] if 'Trend (Media 7gg)' in chart_data.columns else ["#FFCF96"]
    
    st.line_chart(
        chart_data, 
        color=colors, 
        height=250 
    )
