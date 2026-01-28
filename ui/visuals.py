import altair as alt
import pandas as pd
import streamlit as st

# Funzione Stile Clean + Questrial
def clean_pastel_chart(chart):
    return chart.configure(
        background='#FFFFFF' # <--- FORZA SFONDO BIANCO
    ).configure_axis(
        grid=True, # Rimettiamo una griglia leggerissima per leggibilità
        gridColor="#F3F4F6",
        domain=False,
        labelColor='#9CA3AF',
        titleColor='#9CA3AF',
        labelFont='Questrial',
        titleFont='Questrial'
    ).configure_view(
        strokeWidth=0,
        fill='#FFFFFF' # <--- Assicurati che il riempimento sia bianco
    ).configure_title(
        font='Questrial',
        fontSize=16,
        color='#1F2937',
        anchor='start'
    ).configure_legend(
        labelFont='Questrial',
        titleFont='Questrial',
        labelColor='#4A4A4A'
    )

def render_benchmark_chart(df):
    st.markdown("##### 🌍 Benchmark Mondiale")
    
    base = alt.Chart(df).encode(
        x=alt.X('Dist (km)', title='Distanza'),
        y=alt.Y('WR_Pct', title='% WR', scale=alt.Scale(domain=[40, 100])),
        tooltip=['Data', 'SCORE', 'WR_Pct']
    )
    
    # Punti color Salmone e Pesca
    points = base.mark_circle(size=150, opacity=0.9).encode(
        color=alt.Color('WR_Pct', 
            scale=alt.Scale(range=['#FF8080', '#FFCF96', '#CDFAD5']), 
            legend=None
        )
    )
    
    line = base.transform_loess('Dist (km)', 'WR_Pct').mark_line(color='#4A4A4A', opacity=0.2, size=3)
    
    st.altair_chart(clean_pastel_chart(points + line).interactive(), use_container_width=True)

def render_zones_chart(zones_data):
    if not zones_data: return
    z_df = pd.DataFrame(zones_data)
    
    # Palette TUA mappata sulle zone
    # Z1/Z2 -> Mint (#CDFAD5)
    # Z3/Z4 -> Peach (#FFCF96)
    # Z5/Z6 -> Salmon (#FF8080)
    
    bars = alt.Chart(z_df).mark_bar(cornerRadius=10).encode(
        x=alt.X('Zone', title=None, sort=None),
        y=alt.Y('Percent', title=None, axis=None),
        color=alt.Color('Zone', scale=alt.Scale(
            domain=['Z1 Recupero', 'Z2 Fondo Lento', 'Z3 Tempo', 'Z4 Soglia', 'Z5 VO2Max', 'Z6 Anaerobico'],
            range=['#CDFAD5', '#CDFAD5', '#F6FDC3', '#FFCF96', '#FF8080', '#FF8080']
        ), legend=None),
        tooltip=['Zone', 'Percent']
    ).properties(height=200, title="Distribuzione Sforzo")
    
    st.altair_chart(clean_pastel_chart(bars), use_container_width=True)

def render_scatter_chart(watts, hr):
    min_len = min(len(watts), len(hr))
    step = 5 if min_len > 2000 else 1
    dd = pd.DataFrame({'Watts': watts[:min_len:step], 'HR': hr[:min_len:step], 'Time': range(0, min_len, step)})
    
    scat = alt.Chart(dd).mark_circle(size=30, opacity=0.5).encode(
        x=alt.X('Watts', title='Watt', scale=alt.Scale(zero=False)), 
        y=alt.Y('HR', title='BPM', scale=alt.Scale(zero=False)), 
        # Gradiente Mint -> Salmon
        color=alt.Color('Time', title='Tempo', scale=alt.Scale(range=['#CDFAD5', '#FF8080']), legend=None)
    ).properties(height=250, title="HR vs Power").interactive()
    
    st.altair_chart(clean_pastel_chart(scat), use_container_width=True)

def render_history_table(df):
    st.dataframe(
        df,
        column_order=("Data", "Dist (km)", "Power", "HR", "SCORE"),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Data": st.column_config.DateColumn("📅", format="DD/MM"),
            "Dist (km)": st.column_config.NumberColumn("Km", format="%.1f"),
            "Power": st.column_config.ProgressColumn("Watt", format="%d", min_value=0, max_value=400),
            "HR": st.column_config.NumberColumn("BPM"),
            "SCORE": st.column_config.NumberColumn("⭐️", format="%.2f"),
        }
    )
def render_trend_chart(df):
    """
    Mostra l'andamento dello SCORE nel tempo con una linea smussata.
    """
    # Ordiniamo per data
    df_sorted = df.sort_values(by="Data")
    
    # Grafico
    chart = alt.Chart(df_sorted).mark_line(
        interpolate='basis', # Linea curva morbida
        color='#FF8080',     # Color Salmone
        strokeWidth=3
    ).encode(
        x=alt.X('Data:T', axis=False), # Niente asse X per pulizia
        y=alt.Y('SCORE:Q', scale=alt.Scale(domain=[df['SCORE'].min()-0.5, df['SCORE'].max()+0.5]), axis=False),
        tooltip=['Data', 'SCORE', 'Dist (km)']
    ).properties(
        height=80, # Basso e largo (Sparkline style)
        width='container'
    )
    
    # Aggiungiamo un'area sfumata sotto
    area = chart.mark_area(
        interpolate='basis',
        opacity=0.2,
        color='#FF8080'
    ).encode(
        y2=alt.value(100) # Sfumatura verso il basso
    )

    st.markdown("##### 📈 Trend SCORE (Ultimi allenamenti)")
    st.altair_chart((area + chart).interactive(), use_container_width=True)
