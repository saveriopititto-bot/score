import altair as alt
import pandas as pd
import streamlit as st

# Configurazione Clean/White
def clean_chart(chart):
    return chart.configure_axis(
        grid=True,
        gridColor="#F0F0F0", # Griglia leggerissima
        domain=False,
        labelColor='#666666',
        titleColor='#666666',
        labelFont='Questrial',
        titleFont='Questrial'
    ).configure_view(
        strokeWidth=0
    ).configure_legend(
        labelColor='#666666',
        titleColor='#666666',
        labelFont='Questrial'
    ).configure_title(
        font='Questrial',
        color='#FF8080',
        fontSize=16
    )

def render_benchmark_chart(df):
    st.subheader("🌍 Benchmark Mondiale")
    
    base = alt.Chart(df).encode(
        x=alt.X('Dist (km)', title='Distanza (km)'),
        y=alt.Y('WR_Pct', title='% vs Record Mondo', scale=alt.Scale(domain=[40, 100])),
        tooltip=['Data', 'SCORE', 'WR_Pct', 'Dist (km)']
    )
    
    # Usiamo la tua palette per colorare i punti in base alla performance
    points = base.mark_circle(size=150, opacity=0.9, stroke='white', strokeWidth=2).encode(
        color=alt.Color('WR_Pct', 
            scale=alt.Scale(
                domain=[50, 65, 80, 100], 
                range=['#FF8080', '#FFCF96', '#F6FDC3', '#CDFAD5'] # Rosso -> Arancio -> Giallo -> Verde
            ), 
            legend=None
        )
    )
    
    line = base.transform_loess('Dist (km)', 'WR_Pct').mark_line(color='#4A4A4A', size=2, opacity=0.3)
    
    st.altair_chart(clean_chart(points + line).interactive(), use_container_width=True)

def render_zones_chart(zones_data):
    if not zones_data:
        st.info("Dati insufficienti per le Zone.")
        return
        
    z_df = pd.DataFrame(zones_data)
    
    # Mappiamo le zone ai tuoi colori pastello
    # Z1-Z2: Relax (Verde/Giallo)
    # Z3-Z4: Sforzo (Arancio)
    # Z5-Z6: Duro (Rosso)
    color_scale = alt.Scale(
        domain=['Z1 Recupero', 'Z2 Fondo Lento', 'Z3 Tempo', 'Z4 Soglia', 'Z5 VO2Max', 'Z6 Anaerobico'],
        range=['#CDFAD5', '#CDFAD5', '#F6FDC3', '#FFCF96', '#FF8080', '#FF8080'] 
    )

    bars = alt.Chart(z_df).mark_bar(cornerRadius=10).encode(
        x=alt.X('Percent', title=None, axis=None),
        y=alt.Y('Zone', sort=None, title=None, axis=alt.Axis(labels=True, ticks=False)),
        color=alt.Color('Zone', scale=color_scale, legend=None),
        tooltip=['Zone', 'Percent', 'Minutes']
    ).properties(height=250)
    
    text = bars.mark_text(align='left', dx=5, color='#4A4A4A', font='Questrial').encode(
        text=alt.Text('Percent', format='.1f')
    )
    
    st.altair_chart(clean_chart(bars + text), use_container_width=True)

def render_scatter_chart(watts, hr):
    min_len = min(len(watts), len(hr))
    step = 5 if min_len > 2000 else 1
    
    dd = pd.DataFrame({
        'Watts': watts[:min_len:step], 
        'HR': hr[:min_len:step], 
        'Time': range(0, min_len, step)
    })
    
    scat = alt.Chart(dd).mark_circle(size=30, opacity=0.6).encode(
        x=alt.X('Watts', title='Potenza (W)', scale=alt.Scale(zero=False)), 
        y=alt.Y('HR', title='FC (bpm)', scale=alt.Scale(zero=False)), 
        # Gradiente temporale usando la tua palette
        color=alt.Color('Time', title='Tempo', scale=alt.Scale(range=['#CDFAD5', '#FF8080']), legend=None),
        tooltip=['Watts', 'HR']
    ).properties(height=300).interactive()
    
    st.altair_chart(clean_chart(scat), use_container_width=True)

def render_history_table(df):
    st.dataframe(
        df,
        column_order=("Data", "Dist (km)", "Power", "HR", "SCORE", "Rank", "WCF"),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Data": st.column_config.DateColumn("📅 Data", format="DD/MM/YYYY"),
            "Dist (km)": st.column_config.NumberColumn("📏 km", format="%.2f"),
            "Power": st.column_config.ProgressColumn(
                "⚡ Watt", 
                format="%d W", 
                min_value=0, max_value=400,
            ),
            "HR": st.column_config.NumberColumn("❤️ HR"),
            "SCORE": st.column_config.NumberColumn("⭐️ SCORE", format="%.2f"),
            "Rank": st.column_config.TextColumn("🏅 Livello"),
            "WCF": st.column_config.NumberColumn("🌤 WCF", format="%.2fx")
        }
    )
