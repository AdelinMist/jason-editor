import streamlit as st
from bson.objectid import ObjectId
from mongo_db import get_database
from db.projects import get_project
from pydantic import BaseModel, validate_call
from typing import List
import validation

@st.cache_data(ttl=100)
def get_my_service_objects(service_name: str) -> List:
    """
    Retrieves the matched service objects for the connected user by project.
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
                "project": "$project._id",
                "id": { "$convert": { "input": "$_id", "to": "string" } }
            }
        },
        {
            "$project": {
                "_id": 0
            }    
        },
        { "$unwind": "$project" }
    ]
    
    service_objects = db[service_name].aggregate(pipeline)
    
    service_objects = list(service_objects)
    
    return service_objects

@validate_call
def upsert_services(services: List[BaseModel], service_name: str):
    """
    Updates service objects in the database, inserts if no service object exists. Expects a list of pydantic model instances.
    """
    if len(services) == 0:
        return 
    
    db = get_database()
    
    services = [service.model_dump(by_alias=True) for service in services] # dump model data
    
    try:
        print("Services")
        for service in services:
            print(service)
            if service['_id'] == None:
                del service['_id']
                db[service_name].insert_one(service)
            else:
                service['_id'] = ObjectId(service['_id'])
                db[service_name].update_one({'_id': { '$eq': service['_id'] }}, { "$set": service }, upsert=True)
    except Exception as err:
        raise Exception("Error updating services to db: ", err)
    
    # clear the cache for the getter functions
    get_my_service_objects.clear()