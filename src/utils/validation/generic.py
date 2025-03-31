from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from db.projects import get_project
from .types import ObjectId

def default_project_factory():
    """
    Default factory for project values.
    """
    project = get_project()
    return str(project['_id'])

class CustomBaseModel(BaseModel):
    """
    Custom base model with method overloads. This is for generic service objects!
    """
    
    id: Optional[ObjectId] = Field(description="The object id.", alias="_id", default=None)
    
    project: ObjectId = Field(description="The associated object's object id.", default_factory=default_project_factory) 

    def model_dump(self, **kwargs):
        """
        This method overloads the model dump method to return the Enum values themselves, when printing the model object.
        """
        model_dump = super().model_dump(**kwargs)

        for key, value in model_dump.items():
            if isinstance(value, Enum):
                model_dump[key] = value.value
                
        return model_dump