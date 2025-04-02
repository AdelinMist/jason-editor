from pydantic import Field, ConfigDict, conlist, BaseModel, field_validator
from datetime import datetime
from typing import Optional, Union
from .generic import CustomBaseModel
from utils.validation.types import ObjectId
from bson import ObjectId as _ObjectId
from enum import Enum
from db.projects import get_project_by_name

class ActionType(Enum):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    
class StatusType(Enum):
    APPROVAL_PENDING = 'APPROVAL_PENDING'
    APPROVED = 'APPROVED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

class Request(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True
    )
    
    id: Optional[ObjectId] = Field(description="The request object id.", alias="_id", default=None)
    
    request_type: str = Field(description="The request type.") 
    
    project: Union[ObjectId, str] = Field(description="The associated request's object id. Can be either the project id or name.") 
    
    request_date: datetime = Field(description="The request submission date.")
    
    action: ActionType = Field(description="The request action type.")
    
    status: StatusType = Field(description="The request status.")
    
    subject: str = Field(description="The request's subject.")
    
    request_objects: conlist(CustomBaseModel, min_length=1) = Field(description="The request objects, in the form of a list of objects. \
        These will be passed to the backend in an API call!")
    
    @field_validator('project', mode='after')  
    @classmethod
    def is_valid_project(cls, value: str) -> str:
        if not _ObjectId.is_valid(value):
            project = get_project_by_name(value)
            if project == None:
                raise ValueError('Invalid project! Not existant in db!')
        return value 
    
    def model_dump(self, object_id_to_str = False, project_name_to_id = False, **kwargs):
        """
        This method overloads the model dump method to return true ObjectIDs.
        """
        model_dump = super().model_dump(**kwargs)
        
        # if field is None, dont return it!
        none_fields = ['id', '_id']
        none_fields = list(set(none_fields) & set(model_dump.keys()))
        for field in none_fields:
            if model_dump[field] == None:
                del model_dump[field]
        
        # convert project name to objectid     
        if project_name_to_id:
            project = model_dump['project']
            if _ObjectId.is_valid(project):
                model_dump['project'] = _ObjectId(project)
            else:
                model_dump['project'] = get_project_by_name(project)['_id']

        # convert specified fields to objectid
        if not object_id_to_str:
            object_id_fields = ['id', '_id']
            object_id_fields = list(set(object_id_fields) & set(model_dump.keys()))
            for field in object_id_fields:
                field_value = model_dump[field]
                if _ObjectId.is_valid(field_value):
                    model_dump[field] = _ObjectId(field_value)
            
        # if enum, return it's value!
        for key, value in model_dump.items():
            if isinstance(value, Enum):
                model_dump[key] = value.value
        
        return model_dump
            