from pydantic.functional_validators import AfterValidator
from bson import ObjectId as _ObjectId
from typing import Annotated


def check_object_id(value: str) -> str:
    if not _ObjectId.is_valid(value) and value != '':
        raise ValueError('Invalid ObjectId')
    return value

ObjectId = Annotated[str, AfterValidator(check_object_id)]