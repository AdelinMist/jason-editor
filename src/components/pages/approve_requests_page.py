import streamlit as st
import pandas as pd
import re
from mongo_db import upsert_projects, get_requests_for_approval

def approve_button_on_click(**kwargs):
    """
    Handles approval and execution of requests!
    """
    request_objects = kwargs["request_objects"]
    service_name = kwargs['service_name']
    
    try:
        insert_request(service_name, request_objects)
    except Exception as err:
        st.exception(err)

class ApproveRequestsPage():
    """
    This class exists to support the multipage architecture. This is a generic service type page.
    """
    
    def approve_requests(self):
        """
        Handles the submission of a new project to be added to the db.
        """

        st.button(
            label="Approve Requests",
            icon=":material/skull:",
            on_click=approve_button_on_click,
            kwargs={}
        )
    
    def run_page(self):
        """
        The 'main' fucntion of each page. Runs everything.
        """
        request_data = get_requests_for_approval()
        request_df = pd.DataFrame(request_data)
        
        st.subheader('Requests Awaiting Approval')
        requests = st.dataframe(
            request_df,
            column_config={
                "request_objects": st.column_config.JsonColumn(
                    "JSON Data",
                    help="JSON strings or objects",
                    width="large",
                ),
            },
            key = "approval_requests_df",
            on_select="rerun",
            selection_mode=["multi-row"],
            hide_index=False,
            use_container_width=False,
            width=10000,
        )
        
        st.write(st.session_state["approval_requests_df"])
        self.approve_requests()
        
    def get_page(self):
        """
        Returns the page object as needed.
        """
        url_pathname = 'approve-requests'
        page_title = 'Requests For Approval'
        page_icon = ':material/mystery:' 
        return st.Page(self.run_page, title=page_title, icon=page_icon, url_path=url_pathname)