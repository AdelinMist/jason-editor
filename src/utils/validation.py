from pydantic import BaseModel
from enum import Enum

class CustomBaseModel(BaseModel):
    """
    Custom base model with method overloads. This is for generic service objects!
    """

    def model_dump(self, **kwargs):
        """
        This method overloads the model dump method to return the Enum values themselves, when printing the model object.
        """
        model_dump = super().model_dump(**kwargs)
            
        for key, value in model_dump.items():
            if isinstance(value, Enum):
                model_dump[key] = value.value
                
        return model_dump