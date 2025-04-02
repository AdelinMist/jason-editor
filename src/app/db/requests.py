import streamlit as st
from datetime import datetime, timezone
from bson import ObjectId
from mongo_db import get_database
from db.projects import get_project
from pydantic import validate_call
from typing import List, TypeVar, Generic
from utils.validation.request import Request, ActionType, StatusType

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
            }
        },
        { "$unwind": "$project" }
    ]
    
    requests = db['requests'].aggregate(pipeline)
    
    requests = list(requests)
    
    # cast to request object
    requests = [Request(**req).model_dump(object_id_to_str=True) for req in requests]

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
            }
        },
        { "$unwind": "$project" }
    ]
    
    requests = db['requests'].aggregate(pipeline)
    
    requests = list(requests)
    
    # cast to request object
    requests = [Request(**req).model_dump(object_id_to_str=True) for req in requests]

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
            }
        },
        { "$unwind": "$project" }
    ]
    
    requests = db['requests'].aggregate(pipeline)
    
    requests = list(requests)
    
    # cast to request object
    requests = [Request(**req).model_dump(object_id_to_str=True) for req in requests]

    return requests

@validate_call
def update_requests(requests: List[Request]):
    """
    Updates requests in the database, inserts if no request exists.
    """
    db = get_database()
    requests = [request.model_dump(by_alias=True, project_name_to_id=True) for request in requests] # dump model data
    
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

# set generic type var for the service type class
T = TypeVar('T')

@validate_call
def insert_request(req_type: str, req_action: ActionType, request_objects: list[T] ):
    """
    Inserts a new request to the database.
    """
    db = get_database()
    
    utc_datetime = datetime.now(tz=timezone.utc)
    subject_field_name = st.secrets["auth"]["subject_token_field"]
    subject = st.experimental_user[subject_field_name]
    project = get_project()
    
    request_objects = [ obj.model_dump() for obj in request_objects ]
    
    try:
        # validate request
        request = Request(**{
            "request_type": req_type,
            "request_date": utc_datetime,
            "project": project["_id"],
            "action": req_action,
            "status": StatusType.APPROVAL_PENDING,
            "subject": subject,
            "request_objects": request_objects
        }).model_dump(by_alias=True, project_name_to_id=True)
        new_request= db['requests'].insert_one(request)
    except Exception as err:
        raise Exception("Error inserting request to db: ", err)
    
    # clear the cache for the getter functions
    get_requests_for_approval.clear()
    get_my_requests.clear()
    get_all_requests.clear()
    
    return new_request