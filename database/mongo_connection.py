from pymongo import MongoClient

from config.local_settings import (MONGODB_URL_ATLAS, MONGODB_URL_WRITE, MONGODB_URL_READ)


DB_NAME = "ich_edit"
COLLECTION_NAME = "final_project_060326_ptm_oleksandr_kuzan"
MONGODB_URL = MONGODB_URL_WRITE
MONGODB_URL_1 = MONGODB_URL_ATLAS

def get_collection():
    """Создаёт подключение для чтения и возвращает клиент и коллекцию."""

    client = MongoClient(MONGODB_URL)
    collection = client[DB_NAME][COLLECTION_NAME]

    return client, collection

