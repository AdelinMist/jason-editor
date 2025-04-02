import streamlit as st
import pandas as pd
import re
from pydantic import BaseModel, ValidationError
from typing import List
from db.projects import upsert_projects, get_projects, delete_projects
from utils.validation.project import Project
from utils.misc import highlight_is_valid
from utils.validation.request import ActionType
from .service_page import ServicePage, convert_to_records
       
class ProjectsPage(ServicePage):
    """
    This class exists to support the multipage architecture. This is a page to handle projects.
    """ 
    def __init__(self):
        self.cls = {}
        self.cls['name'] = Project.__name__
        self.cls['obj'] = Project
        
        self.page_title = 'Projects'
        
        self.snake_case_name = 'project'
        
    def submit_logic(self, submitted_objects, action_type):
        """
        Handles the submission logic itself, based on the action type.
        """
        if action_type == ActionType.CREATE:
            upsert_projects(submitted_objects)
        elif action_type == ActionType.UPDATE:
            upsert_projects(submitted_objects)
        elif action_type == ActionType.DELETE:
            delete_projects(submitted_objects)
        
    def get_page_data(self):
        return get_projects()
    
    def get_page(self):
        """
        Returns the page object as needed.
        """
        url_pathname = 'projects'
        page_title = 'Projects'
        page_icon = ':material/sunny_snowing:' 
        return st.Page(self.run_page, title=page_title, icon=page_icon, url_path=url_pathname)