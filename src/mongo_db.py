import streamlit as st
import pymongo
import models.project
import models.request
from datetime import datetime, timezone
        
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
def get_data():
    db = get_database()
    items = db.mycollection.find()
    items = list(items)  # make hashable for st.cache_data
    return items

@st.cache_data(ttl=600)
def get_project():
    """
    Retrieves the matched project for the connected user.
    """
    db = get_database()
    groups_field_name = st.secrets["auth"]["groups_token_field"]
    subject_groups = st.experimental_user[groups_field_name]
    projects = db['projects'].find( { 'groups': { '$in': list(subject_groups) } } )
    
    projects = list(projects)  # if for some reason there are multiple matches
    
    return projects[0]

@st.cache_data(ttl=600)
def get_project_by_id(id):
    """
    Retrieves the matched project for the connected user.
    """
    db = get_database()
    projects = db['projects'].find( { '_id': { '$eq': id } } )
    
    projects = list(projects)  # if for some reason there are multiple matches
    
    return projects[0]

def insert_project(name, groups):
    """
    Inserts a new project to the database.
    """
    db = get_database()
    
    project = {
        "name": name,
        "groups": groups,
    }
    
    try:
        new_project= db['projects'].insert_one(project)
    except Exception as err:
        raise Exception("Error inserting project to db: ", err)
    
    return new_project

@st.cache_data(ttl=100)
def get_requests():
    """
    Retrieves the matched project for the connected user.
    """
    db = get_database()
    
    # pipeline to replace the project reference with the project name
    pipeline = [
        {
            "$lookup": {
                "from": "projects",            
                "localField": "project",
                "foreignField": "_id",
                "as": "project"
            }
        },
        {
            "$project": { 
                "_id": 0,
            }
        },
        {
            "$addFields": {
                "project": "$project.name",
            }
        },
        { "$unwind": "$project" }
    ]
    
    requests = db['requests'].aggregate(pipeline)
    
    requests = list(requests)

    return requests

def insert_request(title, request_objects):
    """
    Inserts a new request to the database.
    """
    db = get_database()
    
    utc_datetime = datetime.now(tz=timezone.utc)
    subject_field_name = st.secrets["auth"]["subject_token_field"]
    subject = st.experimental_user[subject_field_name]
    project = get_project()
    
    request = {
        "title": title,
        "request_date": utc_datetime,
        "project": project["_id"],
        "status": "AWAITING_APPROVAL",
        "subject": subject,
        "request_objects": request_objects
    }
    
    try:
        new_request= db['requests'].insert_one(request)
    except Exception as err:
        raise Exception("Error inserting request to db: ", err)
    
    return new_request