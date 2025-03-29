import streamlit as st
import pandas as pd
import re
from mongo_db import get_requests

class RequestsPage():
    """
    This class exists to support the multipage architecture. This is a generic service type page.
    """
    
    def run_page(self):
        """
        The 'main' fucntion of each page. Runs everything.
        """
        
        request_data = get_requests()
        request_df = pd.DataFrame(request_data)
        
        st.subheader('Requests')
        st.dataframe(
            request_df,
            column_config={
                "request_objects": st.column_config.JsonColumn(
                    "JSON Data",
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
        page_icon = ':material/genetics:' # getting the default 
        return st.Page(self.run_page, title=page_title, icon=page_icon, url_path=url_pathname)