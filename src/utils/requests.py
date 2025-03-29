from mongo_db import get_request_by_id

def execute_request(id):
    request = get_request_by_id(id)
    
    return True

def get_request_status(id):
    pass