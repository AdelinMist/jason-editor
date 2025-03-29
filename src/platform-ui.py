import streamlit as st
import validation
import utils.authentication as auth
from components.pages.service_page import ServicePage
from components.pages.requests_page import RequestsPage
from components.pages.approve_requests_page import ApproveRequestsPage
from components.pages.new_project_page import NewProjectPage

if __name__ == '__main__':
    st.set_page_config(layout="wide")
    
    auth.login()
    
    with st.sidebar:
        st.markdown(f"Welcome! {st.experimental_user.name}")
        auth.logout()
        
    ### if user is admin, show admin pages
    admins_groups = st.secrets["authZ"]["admin_groups"]
    groups_field_name = st.secrets["auth"]["groups_token_field"]
    subject_groups = st.experimental_user[groups_field_name]
    
    if bool(set(subject_groups) & set(admins_groups)):
        pages = {
            "Admin": [ApproveRequestsPage().get_page(), NewProjectPage().get_page()]
        }
    else:
        pages = {}
        
    pages.update({
        "Main": [RequestsPage().get_page()]
    })
    
    for category, class_list in validation.classes.items():
        class_page_list = [ServicePage(cls).get_page() for cls in class_list]
        pages.update({category: class_page_list})
            
    pg = st.navigation(pages)
    
    pg.run()