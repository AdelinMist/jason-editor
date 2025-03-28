def get_validator():
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["first_name", "last_name"],
            "properties": {
                "first_name": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "last_name": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "date_of_birth": {
                    "bsonType": "date",
                    "description": "must be a date"
                }
            }
        }
    }
    return validator