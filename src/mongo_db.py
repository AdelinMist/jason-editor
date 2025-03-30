import streamlit as st
import pymongo
import models.project
import models.request
import json
from utils.logger import logger
from datetime import datetime, timezone
from bson import ObjectId
        
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
            logger.error(e)
            
    # Add the schema validation!
    db['projects'].create_index("name", unique=True)
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
    
    pipeline = [
        {
            "$addFields": {
                "id": { "$convert": { "input": "$_id", "to": "string" } }
            }
        },
        {
            "$project": {
                "_id": 0
            }
        }
    ]
    
    projects = db['projects'].aggregate(pipeline)
    
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
            if project['id'] == '':
                del project['id']
                db['projects'].insert_one(project)
            else:
                project_id = ObjectId(project.pop('id'))
                db['projects'].update_one({'_id': { '$eq': project_id }}, { "$set": project }, upsert=True)
    except Exception as err:
        raise Exception("Error upserting projects to db: ", err)
    
    # clear the cache for the getter functions
    get_projects.clear()
    get_project.clear()
    
def delete_projects(project_ids):
    """
    Deletes projects in the database, by name.
    """
    db = get_database()
    
    try:
        for project_id in project_ids:
            db['projects'].delete_many({'_id': ObjectId(project_id)})
    except Exception as err:
        raise Exception("Error deleting projects in db: ", err)

def get_requests_by_id(ids):
    """
    Retrieves the matched requests by id.
    """
    db = get_database()
    requests = db['requests'].find( { '_id': { '$in': ids } } )
    
    requests = list(requests)  # if for some reason there are multiple matches
    
    return requests

@st.cache_data(ttl=100)
def get_all_requests():
    """
    Retrieves the all requests.
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
            "$addFields": {
                "project": "$project.name",
                "_id": { "$convert": { "input": "$_id", "to": "string" } }
            }
        },
        { "$unwind": "$project" }
    ]
    
    requests = db['requests'].aggregate(pipeline)
    
    requests = list(requests)

    return requests

@st.cache_data(ttl=100)
def get_requests_for_approval():
    """
    Retrieves the matched requests awaiting approval.
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
            "$addFields": {
                "project": "$project.name",
                "_id": { "$convert": { "input": "$_id", "to": "string" } }
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
            "$addFields": {
                "project": "$project.name",
                "_id": { "$convert": { "input": "$_id", "to": "string" } }
            }
        },
        { "$unwind": "$project" }
    ]
    
    requests = db['requests'].aggregate(pipeline)
    
    requests = list(requests)

    return requests

def update_requests(requests):
    """
    Updates requests in the database, inserts if no request exists.
    """
    db = get_database()
    
    try:
        for request in requests:
            request['_id'] = ObjectId(request['_id'])
            db['requests'].update_one({'_id': { '$eq': request['_id'] }}, { "$set": request })
    except Exception as err:
        raise Exception("Error updating requests to db: ", err)
    
    # clear the cache for the getter functions
    get_requests_for_approval.clear()
    get_my_requests.clear()
    get_all_requests.clear()

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
    get_all_requests.clear()
    
    return new_request