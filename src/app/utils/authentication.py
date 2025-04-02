import streamlit as st
from db.projects import get_project

def login():
    if not st.experimental_user.is_logged_in:
        st.title("Login Page")
        st.header("Please login below!", divider=True)
        st.button("Log in with OIDC", on_click=st.login)
            
        st.stop()
        
def test_user_project():
    try:
        project = get_project()
        return True if project != None else False
    except Exception as err:
        return False

def logout():
    st.button("Log out", on_click=st.logout)    