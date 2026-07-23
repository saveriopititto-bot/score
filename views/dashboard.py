import streamlit as st
from components.header import render_header
from components.footer import render_footer

def render_dashboard():
    render_header()
    
    st.markdown('<div class="sc-page">', unsafe_allow_html=True)
    
    st.title("Dashboard")
    st.write("Welcome to the sCore Dashboard.")
    st.info("This is a placeholder. Logic to be implemented.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    render_footer()

