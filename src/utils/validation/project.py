from pydantic import field_validator, Field, BaseModel
from typing import Any
import json
from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator, BeforeValidator
from bson import ObjectId as _ObjectId


def check_object_id(value: str) -> str:
    if not _ObjectId.is_valid(value) and value != '':
        raise ValueError('Invalid ObjectId')
    return value


ObjectId = Annotated[str, AfterValidator(check_object_id)]

class Project(BaseModel):
    
    id: ObjectId = Field(description="The project object id.", default=None)
    
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
