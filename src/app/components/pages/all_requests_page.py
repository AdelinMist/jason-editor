from db.requests import get_all_requests
from .requests_page import RequestsPage

class AllRequestsPage(RequestsPage):
    """
    This class exists to support the multipage architecture. This is a page to display all requests.
    """
    
    def __init__(self):
        """
        Init, meant to be overloaded.
        """
        
        self.url_pathname = 'all-requests'
        self.page_title = 'All Requests'
        self.page_icon = ':material/electric_bolt:'  
        
        self.allow_execute = True
        self.exec_button_label = "Re-Exec Requests"
        
    def get_page_data(self):
        """
        This function simply gets the data already existing in the db for this page. Meant for overloading.
        """
        return get_all_requests()