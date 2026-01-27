import altair as alt
import pandas as pd
import streamlit as st

def render_benchmark_chart(df):
    st.subheader("Benchmark Mondiale (Riegel)")
    chart = alt.Chart(df).mark_circle(size=120).encode(
        x=alt.X('Dist (km)', scale=alt.Scale(zero=False)),
        y=alt.Y('WR_Pct', title='% Velocità Record Mondo'),
        color=alt.Color('WR_Pct', scale=alt.Scale(scheme='magma')),
        tooltip=['Data', 'SCORE', 'WR_Pct']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

def render_zones_chart(zones_data):
    if not zones_data:
        st.info("Dati insufficienti per le Zone.")
        return
    z_df = pd.DataFrame(zones_data)
    bars = alt.Chart(z_df).mark_bar().encode(
        x=alt.X('Percent', title='% Tempo'),
        y=alt.Y('Zone', sort=None),
        color=alt.Color('Color', scale=None),
        tooltip=['Zone', 'Percent', 'Minutes']
    ).properties(height=250)
    text = bars.mark_text(dx=3, align='left').encode(text=alt.Text('Percent', format='.1f'))
    st.altair_chart(bars + text, use_container_width=True)

def render_scatter_chart(watts, hr):
    min_len = min(len(watts), len(hr))
    dd = pd.DataFrame({'Watts': watts[:min_len], 'HR': hr[:min_len], 'Time': range(min_len)})
    scat = alt.Chart(dd).mark_circle(opacity=0.3).encode(
        x='Watts', y=alt.Y('HR', scale=alt.Scale(zero=False)), 
        color=alt.Color('Time', title='Tempo', scale=alt.Scale(scheme='plasma'))
    ).properties(height=250).interactive()
    st.altair_chart(scat, use_container_width=True)
