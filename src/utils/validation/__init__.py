from pydantic.functional_validators import AfterValidator
from pydantic import BaseModel, Field
from bson import ObjectId as _ObjectId
from typing import Annotated, Optional
from enum import Enum

def check_object_id(value: str) -> str:
    if not _ObjectId.is_valid(value) and value != '':
        raise ValueError('Invalid ObjectId')
    return value

ObjectId = Annotated[str, AfterValidator(check_object_id)]

class CustomBaseModel(BaseModel):
    """
    Custom base model with method overloads.
    """
    
    id: Optional[ObjectId] = Field(description="The object id.", alias="_id", default=None)

    def model_dump(self, **kwargs):
        """
        This method overloads the model dump method to return the Enum values themselves, when printing the model object.
        """
        model_dump = super().model_dump(**kwargs)

        for key, value in model_dump.items():
            if isinstance(value, Enum):
                model_dump[key] = value.value
                
        return model_dump