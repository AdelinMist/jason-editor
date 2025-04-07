import os
from dotenv import load_dotenv
import pymongo
from json import dumps
from logger import logger
import threading
import queue

def worker(**kwargs):
    queue = kwargs['queue']
    request_id_set = kwargs['request_id_set']
    while True:
        item = queue.get()
        request_id = item['_id']
        
        logger.info(f'Working on {item}')
        logger.info(f'Finished {item}')
        
        queue.task_done()
        request_id_set.remove(request_id)
        logger.info(f"In worker thread {request_id_set}")

load_dotenv()  # take environment variables

# load env variables
MONGO_DB_HOST = os.getenv('MONGO_DB_HOST')
MONGO_DB_PORT = int(os.getenv('MONGO_DB_PORT'))
MONGO_DB_USERNAME = os.getenv('MONGO_DB_USERNAME')
MONGO_DB_PASSWORD = os.getenv('MONGO_DB_PASSWORD')
        
# Initialize connection.
logger.info("Init mongo connection.")
try:
    client = pymongo.MongoClient(host=MONGO_DB_HOST, port=MONGO_DB_PORT, username=MONGO_DB_USERNAME, password=MONGO_DB_PASSWORD, directConnection=True)
    db = client['platform']
except Exception as e:
    logger.exception(e)

pipeline = [{
    '$match': {
        'operationType': { '$in': ['update'] },
    }
}]
#  'fullDocument.action': 'APPROVED'
logger.info("Init queue.")
# init queue for task execution
task_queue = queue.Queue()
# set to keep all request ids, to avoid duplicates in task queue
request_id_set = set()
# Turn-on the worker thread.
threading.Thread(target=worker, kwargs={'queue': task_queue, 'request_id_set': request_id_set}, daemon=True).start()

max_queue_size = 10
logger.info("Start execution.")
resume_token = None
while True:
    change_stream = db['requests'].watch(pipeline, full_document="updateLookup")
    try:
        for change in change_stream:
            print(change)
            doc = change['fullDocument']
            logger.info(doc)
            print(doc)
            print('') # for readability only
            
            request_id = doc['_id']
            if request_id not in request_id_set:
                request_id_set.add(request_id)   
                logger.info(f"In normal thread before worker {request_id_set}")
                task_queue.put(doc)
                task_queue.join()
            
            logger.info(f"In normal thread after worker {request_id_set}")
            resume_token = change_stream.resume_token
    except Exception as e:
        logger.exception(e)
        logger.info("Trying to use resume token to continue...")
