from mongo_db import get_requests_by_id

def execute_requests(ids):
    requests = get_requests_by_id(ids)
    
    return False

def get_request_status(id):
    pass