from pydantic import field_validator, Field, BaseModel, ConfigDict
from typing import Any
import json
from utils.validation import ObjectId

class Project(BaseModel):
    
    id: ObjectId = Field(description="The project object id.", serialization_alias="_id", default=None)
    
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
