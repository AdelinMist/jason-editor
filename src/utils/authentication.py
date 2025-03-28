import streamlit as st

def login():
    if not st.experimental_user.is_logged_in:
        st.title("Login Page")
        st.header("Please login below!", divider=True)
        st.button("Log in with OIDC", on_click=st.login)
            
        st.stop()

def logout():
    st.button("Log out", on_click=st.logout)    