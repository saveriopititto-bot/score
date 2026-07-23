import streamlit as st

def render_landing():
    st.title("Welcome to sCore")
    st.write("Please log in to continue.")
    if st.button("Login Simulation"):
        st.session_state.authenticated = True
        st.rerun()
