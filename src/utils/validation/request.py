from pydantic import Field, ConfigDict, conlist, BaseModel
from datetime import datetime
from typing import Optional
from utils.validation.types import ObjectId
from bson import ObjectId as _ObjectId
from enum import Enum

class ActionType(Enum):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    
class StatusType(Enum):
    APPROVAL_PENDING = 'APPROVAL_PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

class Request(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True
    )
    
    id: Optional[ObjectId] = Field(description="The request object id.", alias="_id", default=None)
    
    request_type: str = Field(description="The request type.") 
    
    project: ObjectId = Field(description="The associated request's object id.") 
    
    request_date: datetime = Field(description="The request submission date.")
    
    action: ActionType = Field(description="The request action type.")
    
    status: StatusType = Field(description="The request status.")
    
    subject: str = Field(description="The request's subject.")
    
    request_objects: conlist(dict, min_length=1) = Field(description="The request objects, in the form of a list of objects. \
        These will be passed to the backend in an API call!")
    
    def model_dump(self, object_id_to_str = False, **kwargs):
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
            
        if not object_id_to_str:
            object_id_fields = ['project', 'id', '_id']
            object_id_fields = list(set(object_id_fields) & set(model_dump.keys()))
            for field in object_id_fields:
                model_dump[field] = _ObjectId(model_dump[field])
            
        for key, value in model_dump.items():
            if isinstance(value, Enum):
                model_dump[key] = value.value
        
        return model_dump
            