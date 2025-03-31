import streamlit as st
import pandas as pd
from db.requests import update_requests, get_requests_for_approval
from utils.requests import execute_requests
from .requests_page import RequestsPage

class ApproveRequestsPage(RequestsPage):
    """
    This class exists to support the multipage architecture. This is a page to approve requests.
    """
    
    def __init__(self):
        
        self.url_pathname = 'approve-requests'
        self.page_title = 'Approve Requests'
        self.page_icon = ':material/mystery:' 
        
        self.allow_execute = True
        self.exec_button_label = "Approve Requests"
            
    def get_page_data(self):
        """
        This function simply gets the data already existing in the db for this page. Meant for overloading.
        """
        return get_requests_for_approval()