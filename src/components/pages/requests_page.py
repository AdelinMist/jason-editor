import streamlit as st
import pandas as pd
import re
from mongo_db import get_database

# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_requests(db):
    items = db.requests.find()
    items = list(items)  # make hashable for st.cache_data
    return items

class RequestsPage():
    """
    This class exists to support the multipage architecture. This is a generic service type page.
    """
    def __init__(self):
        self.db = get_database()
    
    def run_page(self):
        """
        The 'main' fucntion of each page. Runs everything.
        """
        
        request_data = get_requests(self.db)
        request_df = pd.DataFrame(request_data)
        
        st.subheader('Requests')
        st.data_editor(
            request_df,
            num_rows="dynamic",
            hide_index=False,
            use_container_width=False,
            width=10000,
        )
        
    def get_page(self):
        """
        Returns the page object as needed.
        """
        split_name = re.sub( r"([A-Z])", r" \1", self.cls['name']).split()
        lower_split_name = [word.lower() for word in split_name]
        url_pathname = '-'.join(lower_split_name)
        page_title = ' '.join(split_name)
        page_icon = getattr(self.cls['obj'], f"_{self.cls['name']}__icon") # getting the default 
        return st.Page(self.run_page, title=page_title, icon=f"{page_icon.default}", url_path=url_pathname)