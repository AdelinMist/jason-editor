import streamlit as st
import pymongo
import models
              
class MongoClient():
    """
    This class abstracts a connection to the MongoDB instance.
    """
    def __init__(self):
        self.db = self.init_database()
        
        # Init the collection with their validators
        self.init_project_collection()
        self.init_request_collection()
        
    # Initialize connection.
    # Uses st.cache_resource to only run once.
    @st.cache_resource
    def init_database():
        client = pymongo.MongoClient(**st.secrets["mongo"])
        return client['platform']

    @st.cache_resource
    def init_project_collection(db):
        coll_list = db.list_collection_names()
        
        if 'project' not in coll_list:
            # Creating a new collection
            try:
                db.create_collection('project')
            except Exception as e:
                print(e)
                
        # Add the schema validation!
        db.command("collMod", "project", validator=models.project.get_validator())
        
    @st.cache_resource
    def init_request_collection(db):
        coll_list = db.list_collection_names()
        
        if 'request' not in coll_list:
            # Creating a new collection
            try:
                db.create_collection('request')
            except Exception as e:
                print(e)
                
        # Add the schema validation!
        db.command("collMod", "request", validator=models.request.get_validator())
        
# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_data(db):
    items = db.mycollection.find()
    items = list(items)  # make hashable for st.cache_data
    return items