import logging
from ..config import USER, MONGO_DB,PW, HOST
from pymongo import MongoClient
from functools import lru_cache
from .indexes import create_indexes
logger = logging.getLogger(__name__)
@lru_cache()
def get_client():
    logger.debug("Creating new MongoDB client. (singleton)")
    client = MongoClient(
        f"mongodb+srv://{HOST}/",
        username=USER,
        password=PW,
        retryWrites=True,
        w="majority",
    )
    try:
        client.admin.command('ping')
        logger.debug("MongoDB connection successful.")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise
    return client
def get_db():
    client = get_client()
    db = client[MONGO_DB]
    return db   
def ensure_indexes(db):
    create_indexes(db)