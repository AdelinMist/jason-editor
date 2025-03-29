def get_validator():
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "groups"],
            "properties": {
                "name": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "groups": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "string"
                    },
                    "description": "must be an array of strings and is required, this is the groups that are mapped to the project",
                    "minItems": 1,
                }
            }
        }
    }
    return validator