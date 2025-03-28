import streamlit as st
import pymongo
import models.project
import models.request
        
# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def get_database():
    client = pymongo.MongoClient(**st.secrets["mongo"])
    db = client['platform']
    init_project_collection(db)
    init_request_collection(db)
    
    return db

def init_project_collection(db):
    coll_list = db.list_collection_names()
    
    if 'projects' not in coll_list:
        # Creating a new collection
        try:
            db.create_collection('projects')
        except Exception as e:
            print(e)
            
    # Add the schema validation!
    db.command("collMod", "projects", validator=models.project.get_validator())
    
def init_request_collection(db):
    coll_list = db.list_collection_names()
    
    if 'requests' not in coll_list:
        # Creating a new collection
        try:
            db.create_collection('requests')
        except Exception as e:
            print(e)
            
    # Add the schema validation!
    db.command("collMod", "requests", validator=models.request.get_validator())

# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_data(db):
    items = db.mycollection.find()
    items = list(items)  # make hashable for st.cache_data
    return items

def insert_request(request_objects):
    db = get_database()
    
    request = {
        "request_objects": request_objects
    }
    
    try:
        new_request= db['requests'].insert_one(request)
    except Exception as err:
        raise err
    
    return new_request