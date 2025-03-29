import streamlit as st
import pymongo
import models.project
import models.request
import json
from logger import logger
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
            db.projects.createIndex( { "name": 1 }, { "unique": "true" } )
        except Exception as e:
            logger.error(e)
            
    # Add the schema validation!
    db.command("collMod", "projects", validator=models.project.get_validator())
    
def init_request_collection(db):
    coll_list = db.list_collection_names()
    
    if 'requests' not in coll_list:
        # Creating a new collection
        try:
            db.create_collection('requests')
        except Exception as e:
            logger.error(e)
            
    # Add the schema validation!
    db.command("collMod", "requests", validator=models.request.get_validator())


# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=100)
def get_data():
    db = get_database()
    items = db.mycollection.find()
    items = list(items)  # make hashable for st.cache_data
    return items

@st.cache_data(ttl=100)
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

@st.cache_data(ttl=100)
def get_project_by_id(id):
    """
    Retrieves the matched project by id.
    """
    db = get_database()
    projects = db['projects'].find( { '_id': { '$eq': id } } )
    
    projects = list(projects)  # if for some reason there are multiple matches
    
    return projects[0]

@st.cache_data(ttl=100)
def get_projects():
    """
    Retrieves the matched project for the connected user.
    """
    db = get_database()

    projects = db['projects'].find({}, {'_id': 0})
    
    list_to_str = lambda kv: (kv[0], json.dumps(kv[1])) if kv[0]=='groups' else (kv[0], kv[1])
    
    projects = list(projects)  # if for some reason there are multiple matches
    projects = [dict(map(list_to_str, prj.items())) for prj in projects]
    
    return projects

def upsert_projects(projects):
    """
    Updates projects in the database, inserts if no project exists.
    """
    db = get_database()
    
    try:
        for project in projects:
            db['projects'].update_one({'name': { '$eq': project['name'] }}, { "$set": project }, upsert=True)
    except Exception as err:
        raise Exception("Error upserting projects to db: ", err)
    
    # clear the cache for the getter functions
    get_projects.clear()
    get_project.clear()
    
def delete_projects(projects):
    """
    Deletes projects in the database, by name.
    """
    db = get_database()
    
    try:
        for project in projects:
            db['projects'].delete_many({'name': project})
    except Exception as err:
        raise Exception("Error deleting projects in db: ", err)

def get_request_by_id(id):
    """
    Retrieves the matched request by id.
    """
    db = get_database()
    requests = db['requests'].find( { '_id': { '$eq': id } } )
    
    requests = list(requests)  # if for some reason there are multiple matches
    
    return requests[0]

@st.cache_data(ttl=100)
def get_requests_for_approval():
    """
    Retrieves the matched project for the connected user.
    """
    db = get_database()
    
    # pipeline to replace the project reference with the project name
    pipeline = [
        { "$match" : { "status" : "APPROVAL_PENDING" } },
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

@st.cache_data(ttl=100)
def get_my_requests():
    """
    Retrieves the matched requests for the connected user by project.
    """
    db = get_database()
    
    project = get_project()
    
    # pipeline to replace the project reference with the project name
    pipeline = [
        { "$match" : { "project" : { '$eq': project['_id'] } } },
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

def insert_request(req_type, request_objects):
    """
    Inserts a new request to the database.
    """
    db = get_database()
    
    utc_datetime = datetime.now(tz=timezone.utc)
    subject_field_name = st.secrets["auth"]["subject_token_field"]
    subject = st.experimental_user[subject_field_name]
    project = get_project()
    
    request = {
        "type": req_type,
        "request_date": utc_datetime,
        "project": project["_id"],
        "status": "APPROVAL_PENDING",
        "subject": subject,
        "request_objects": request_objects
    }
    
    try:
        new_request= db['requests'].insert_one(request)
    except Exception as err:
        raise Exception("Error inserting request to db: ", err)
    
    # clear the cache for the getter functions
    get_requests_for_approval.clear()
    get_my_requests.clear()
    
    return new_request