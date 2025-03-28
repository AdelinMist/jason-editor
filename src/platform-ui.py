import streamlit as st
import validation
#import mongo as mon
import utils.authentication as auth
from components.pages.service_page import ServicePage


if __name__ == '__main__':
    st.set_page_config(layout="wide")
    
    auth.login()
    
    with st.sidebar:
        st.markdown(f"Welcome! {st.experimental_user.name}")
        auth.logout()
    
    pages = {}
    for category, class_list in validation.classes.items():
        class_page_list = [ServicePage(cls).get_page() for cls in class_list]
        pages.update({category: class_page_list})
            
    pg = st.navigation(pages)
    
    pg.run()