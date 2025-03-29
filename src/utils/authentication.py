import streamlit as st
from mongo_db import get_project

def login():
    if not st.experimental_user.is_logged_in:
        st.title("Login Page")
        st.header("Please login below!", divider=True)
        st.button("Log in with OIDC", on_click=st.login)
            
        st.stop()
    else:
        ### logged in, try to get the project, stop if failed
        try:
            project = get_project()
        except Exception as err:
            st.info("Problem getting the associated project! Please contact a system admin for further investigation.", icon="ℹ️")
            st.exception("Problem getting the associated project! Please contact a system admin for further investigation.")
            st.stop()

def logout():
    st.button("Log out", on_click=st.logout)    