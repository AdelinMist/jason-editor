from pydantic.functional_validators import AfterValidator, BeforeValidator
from bson import ObjectId as _ObjectId
from typing import Annotated, Union, Any


def before_object_id(value: Any) -> str:
    if not _ObjectId.is_valid(value) and not isinstance(value, str):
        raise ValueError('Invalid ObjectId, not str nor ObjectId!')
    return str(value)

def after_object_id(value: str) -> str:
    if not _ObjectId.is_valid(value):
        raise ValueError('Invalid ObjectId')
    return value

AnyToStr = Annotated[Any, BeforeValidator(before_object_id)]
ObjectId = Annotated[AnyToStr, AfterValidator(after_object_id)]