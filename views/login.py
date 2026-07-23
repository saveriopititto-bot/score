import streamlit as st

def render_login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign In"):
        if username and password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Please enter credentials.")
