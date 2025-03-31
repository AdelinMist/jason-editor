from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from enum import Enum
from db.projects import get_project
from .types import ObjectId
from bson import ObjectId as _ObjectId

def default_project_factory():
    """
    Default factory for project values.
    """
    project = get_project()
    return project['_id']

class CustomBaseModel(BaseModel):
    """
    Custom base model with method overloads. This is for generic service objects!
    """
    model_config = ConfigDict(
        populate_by_name=True
    )
    
    id: Optional[ObjectId] = Field(description="The object id.", alias="_id")
    
    project: Optional[ObjectId] = Field(description="The associated object's object id.", default_factory=default_project_factory) 

    def model_dump(self, object_id_to_str = False, **kwargs):
        """
        This method overloads the model dump method to return the Enum values themselves, when printing the model object.
        """
        model_dump = super().model_dump(**kwargs)

        # if field is None, dont return it!
        none_fields = ['project', 'id', '_id']
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