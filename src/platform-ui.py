import streamlit as st
import utils.authentication as auth
from components.pages.service_page import ServicePage
from components.pages.my_requests_page import MyRequestsPage
from components.pages.all_requests_page import AllRequestsPage
from components.pages.approve_requests_page import ApproveRequestsPage
from components.pages.projects_page import ProjectsPage
import validation

if __name__ == '__main__':
    st.set_page_config(layout="wide")
    
    auth.login()
    
    with st.sidebar:
        st.badge(f"Welcome! {st.experimental_user.name}", icon=":material/account_circle:", color="violet")
        auth.logout()
        
    ### if user is admin, show admin pages
    admins_groups = st.secrets["authZ"]["admin_groups"]
    groups_field_name = st.secrets["auth"]["groups_token_field"]
    subject_groups = st.experimental_user[groups_field_name]
    
    has_project = auth.test_user_project()
    if bool(set(subject_groups) & set(admins_groups)):
        if not has_project:
            pages = {
                "Admin": [ProjectsPage().get_page()]
            }
        else:
            pages = {
                "Admin": [AllRequestsPage().get_page(), ApproveRequestsPage().get_page(), ProjectsPage().get_page()]
            }
    else:
        pages = {}
        if not has_project:
            st.info("Problem getting the associated project!  \nYou either don't have a project, or there is some other problem...  \nPlease contact a system admin for further investigation.", icon="ℹ️")
            st.stop()
        
    if has_project:
        pages.update({
            "Main": [MyRequestsPage().get_page()]
        })
        
        for category, class_list in validation.classes.items():
            class_page_list = [ServicePage(cls).get_page() for cls in class_list]
            pages.update({category: class_page_list})
            
    pg = st.navigation(pages)
    
    pg.run()