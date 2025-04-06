import os
from dotenv import load_dotenv
import pymongo
from json import dumps
from logger import logger
import threading
import queue

load_dotenv()  # take environment variables

# load env variables
MONGO_DB_HOST = os.getenv('MONGO_DB_HOST')
MONGO_DB_PORT = os.getenv('MONGO_DB_PORT')
MONGO_DB_USERNAME = os.getenv('MONGO_DB_USERNAME')
MONGO_DB_PASSWORD = os.getenv('MONGO_DB_PASSWORD')
        
# Initialize connection.
try:
    client = pymongo.MongoClient(host=MONGO_DB_HOST, port=MONGO_DB_PORT, username=MONGO_DB_USERNAME, password=MONGO_DB_PASSWORD, directConnection=True)
    db = client['platform']
except Exception as e:
    logger.exception(e)

pipeline = [{
    '$match': {
        'operationType': { '$in': ['insert'] },
        'fullDocument.action': 'APPROVED'
    }
}]

resume_token = None
while True:
    change_stream = db['requests'].watch(pipeline, full_document="updateLookup", resume_after=resume_token)
    try:
        for change in change_stream:
            logger.info(dumps(change))
            print(dumps(change))
            print('') # for readability only
            resume_token = change_stream.resume_token
    except Exception as e:
        logger.exception(e)
        logger.info("Trying to use resume token to continue...")

q = queue.Queue()

def worker():
    while True:
        item = q.get()
        print(f'Working on {item}')
        print(f'Finished {item}')
        q.task_done()

# Turn-on the worker thread.
threading.Thread(target=worker, daemon=True).start()

# Send thirty task requests to the worker.
for item in range(30):
    q.put(item)

# Block until all tasks are done.
q.join()
print('All work completed')
