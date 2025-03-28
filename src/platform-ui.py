import streamlit as st
import validation
from mongo_db import get_database, insert_request
import utils.authentication as auth
from components.pages.service_page import ServicePage
from components.pages.requests_page import RequestsPage


if __name__ == '__main__':
    st.set_page_config(layout="wide")
    
    auth.login()
    
    db = get_database()
    insert_request([{"hello":"hi"}])
    
    with st.sidebar:
        st.markdown(f"Welcome! {st.experimental_user.name}")
        auth.logout()
    
    pages = {
        "Main": [RequestsPage().get_page()]
    }
    for category, class_list in validation.classes.items():
        class_page_list = [ServicePage(cls).get_page() for cls in class_list]
        pages.update({category: class_page_list})
            
    pg = st.navigation(pages)
    
    pg.run()