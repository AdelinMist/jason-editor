from pydantic import ValidationError
import streamlit as st
import pandas as pd
from db.requests import get_my_requests
from utils.validation.request import Request
from .requests_page import RequestsPage

class MyRequestsPage(RequestsPage):
    """
    This class exists to support the multipage architecture. This is a generic service type page.
    """
    
    def __init__(self):
        
        self.url_pathname = 'my-requests'
        self.page_title = 'My Requests'
        self.page_icon = ':material/genetics:' 
        
        self.allow_execute = False
            
    def get_page_data(self):
        """
        This function simply gets the data already existing in the db for this page. Meant for overloading.
        """
        return get_my_requests()