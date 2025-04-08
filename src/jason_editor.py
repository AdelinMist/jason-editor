import streamlit as st
from components.pages.service_page import ServicePage
import validation

if __name__ == '__main__':
    st.set_page_config(layout="wide")
        
    pages = {}
    
    for category, class_list in validation.classes.items():
        class_page_list = [ServicePage(cls).get_page() for cls in class_list]
        pages.update({category: class_page_list})
            
    pg = st.navigation(pages)
    
    pg.run()