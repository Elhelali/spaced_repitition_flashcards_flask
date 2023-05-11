from config import mongo_username,mongo_password,mongo_url
import pymongo
from functools import wraps
def mongo(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        with pymongo.MongoClient(
            f"mongodb+srv://{mongo_username}:{mongo_password}@{mongo_url}"
        ) as database:
            return f(database["flashcards"], *args, **kwargs)

    return wrap
