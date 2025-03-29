import streamlit as st
import pandas as pd
import re
from mongo_db import get_all_requests

class AllRequestsPage():
    """
    This class exists to support the multipage architecture. This is a page to display all requests.
    """
    
    def run_page(self):
        """
        The 'main' fucntion of each page. Runs everything.
        """
        
        request_data = get_all_requests()
        st.session_state["all_requests_df"] = pd.DataFrame(request_data)
        columns_to_display = list(st.session_state["all_requests_df"].columns)
        
        if '_id' in columns_to_display:
            columns_to_display.remove('_id')
        
        st.subheader('All Requests')
        st.dataframe(
            st.session_state["all_requests_df"],
            column_config={
                "request_objects": st.column_config.JsonColumn(
                    "request data",
                    help="JSON strings or objects",
                    width="large",
                ),
            },
            column_order=columns_to_display,
            hide_index=False,
            use_container_width=False,
            width=10000,
        )
        
    def get_page(self):
        """
        Returns the page object as needed.
        """
        url_pathname = 'all-requests'
        page_title = 'All Requests'
        page_icon = ':material/electric_bolt:' 
        return st.Page(self.run_page, title=page_title, icon=page_icon, url_path=url_pathname)