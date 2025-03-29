def get_validator():
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["title", "subject", "request_date", "project", "status", "request_objects"],
            "properties": {
                "title": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "project": {
                    "bsonType": "objectId",
                    "description": "must be an objectId and is required",
                },
                "request_date": {
                    "bsonType": "date",
                    "description": "must be a date and is required"
                },
                "status": {
                    "enum": ["APPROVAL_PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"],
                    "description": "can only be one of the enum values and \
                    is required"
                },
                "subject": {
                    "bsonType": "string",
                    "description": "must be a string and is required",
                },
                "request_objects": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object"
                    },
                    "description": "must be an array of objects and is required, this is the json request body we will send to the backend",
                    "minItems": 1,
                }
            }
        }
    }
    return validator