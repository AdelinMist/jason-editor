import streamlit as st
import pandas as pd
from db.requests import get_my_requests

class MyRequestsPage():
    """
    This class exists to support the multipage architecture. This is a generic service type page.
    """
    
    def run_page(self):
        """
        The 'main' fucntion of each page. Runs everything.
        """
        st.title("My Requests")
        
        request_data = get_my_requests()
        request_df = pd.DataFrame(request_data)
        
        st.subheader('Requests')
        st.dataframe(
            request_df,
            column_config={
                "request_objects": st.column_config.JsonColumn(
                    "request data",
                    help="JSON strings or objects",
                    width="large",
                ),
            },
            hide_index=False,
            use_container_width=False,
            width=10000,
        )
        
    def get_page(self):
        """
        Returns the page object as needed.
        """
        url_pathname = 'my-requests'
        page_title = 'My Requests'
        page_icon = ':material/genetics:' 
        return st.Page(self.run_page, title=page_title, icon=page_icon, url_path=url_pathname)