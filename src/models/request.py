def get_validator():
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["title", "authors", "publication_date", \
            "type", "copies"],
            "properties": {
                "title": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "authors": {
                    "bsonType": "array",
                    "description": "must be an array and is required",
                    "items": {
                        "bsonType": "objectId",
                        "description": "must be an objectId and is required"
                    },
                    "minItems": 1,
                },
                "publication_date": {
                    "bsonType": "date",
                    "description": "must be a date and is required"
                },
                "type": {
                    "enum": ["hardcover", "paperback"],
                    "description": "can only be one of the enum values and \
                    is required"
                },
                "copies": {
                    "bsonType": "int",
                    "description": "must be an integer greater than 0 and \
                    is required",
                    "minimum": 0
                }
            }
        }
    }
    return validator