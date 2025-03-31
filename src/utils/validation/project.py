from enum import Enum
from pydantic import field_validator, Field, BaseModel, ConfigDict
from typing import Any, Optional
import json
from bson import ObjectId as _ObjectId
from utils.validation.types import ObjectId

class Project(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True
    )
    
    id: Optional[ObjectId] = Field(description="The project object id.", alias="_id", default=None)
    
    name: str = Field(description="The project name.")  # the previous defined Enum class
    
    groups: list[str] = Field(description="The LDAP groups mapped to the project.")

    @field_validator('name', mode='after')  
    @classmethod
    def is_valid_name(cls, value: str) -> str:
        return value 

    @field_validator('groups', mode='before')  
    @classmethod
    def is_valid_groups(cls, value: Any) -> Any:
        """
        Casts a json-type list to python list.
        """
        if isinstance(value, str):  
            try:
                groups_list = json.loads(value)
            except Exception as err:
                raise ValueError(f'{value} is not valid json array! Error: {err}')
            return list(groups_list)
        elif not isinstance(value, list):
            return [value]
        else:
            return value
        
    def model_dump(self, object_id_to_str = False, groups_to_str = True, **kwargs):
        """
        This method overloads the model dump method to return the Enum values themselves, when printing the model object.
        """
        model_dump = super().model_dump(**kwargs)

        # if field is None, dont return it!
        none_fields = []
        none_fields = list(set(none_fields) & set(model_dump.keys()))
        for field in none_fields:
            if model_dump[field] == None:
                del model_dump[field]
            
        if not object_id_to_str:
            object_id_fields = ['id', '_id']
            object_id_fields = list(set(object_id_fields) & set(model_dump.keys()))
            for field in object_id_fields:
                model_dump[field] = _ObjectId(model_dump[field])
                
        if groups_to_str:
            model_dump['groups'] = json.dumps(model_dump['groups'])
            
        for key, value in model_dump.items():
            if isinstance(value, Enum):
                model_dump[key] = value.value
                
        return model_dump
