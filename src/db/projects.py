import streamlit as st
import json
from bson import ObjectId as _ObjectId
from utils.validation import ObjectId
from mongo_db import get_database
from typing import List
from utils.validation.project import Project
from pydantic import validate_call

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
@validate_call
def get_project_by_id(id: ObjectId):
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

@validate_call
def upsert_projects(projects: List[Project]):
    """
    Updates projects in the database, inserts if no project exists.
    """
    db = get_database()
    projects = [project.model_dump() for project in projects] # dump model data
    
    try:
        for project in projects:
            if project['id'] == '':
                del project['id']
                db['projects'].insert_one(project)
            else:
                project_id = _ObjectId(project.pop('id'))
                db['projects'].update_one({'_id': { '$eq': project_id }}, { "$set": project }, upsert=True)
    except Exception as err:
        raise Exception("Error upserting projects to db: ", err)
    
    # clear the cache for the getter functions
    get_projects.clear()
    get_project.clear()

@validate_call
def delete_projects(project_ids: List[ObjectId]):
    """
    Deletes projects in the database, by name.
    """
    db = get_database()
    
    try:
        for project_id in project_ids:
            db['projects'].delete_many({'_id': _ObjectId(project_id)})
    except Exception as err:
        raise Exception("Error deleting projects in db: ", err)