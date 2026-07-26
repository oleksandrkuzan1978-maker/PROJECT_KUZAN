# from pprint import pprint
from datetime import datetime
from typing import Any

# from collections import Counter
# from pathlib import Path
from pymongo import MongoClient  # pip install pymongo
from pymongo.errors import PyMongoError
from functools import wraps
from config.local_settings import (MONGODB_URL_WRITE, MONGODB_URL_READ)
import logging

logger = logging.getLogger(__name__)

"""*********************** Создаем коллекцию ***************************"""

DB_NAME = "ich_edit"
COLLECTION_NAME = "final_project_060326_ptm_oleksandr_kuzan"

# Ф-ция сохранения результата запроса в базе данных MongoDB
def save_query(search_type, query):

    document = {
        "search_type": search_type,
        "query": query,
        "created_at": datetime.now(),
    }
    if search_type == "by_name":
        document["query"] = document["query"].replace("%", "")  # Заменяем в названии фильма % на ""

    with MongoClient(MONGODB_URL_WRITE) as client:

        collection = client[DB_NAME][COLLECTION_NAME]

        collection.insert_one(document)

        # Если сильно хочется посмотреть, что и как записалось в коллекцию
        # for doc in collection.find():
        #     print(doc)

    logger.info("Поисковый запрос сохранён в MongoDB")

"""************************ Возвращаем запросы ***************************"""

# Декоратор подключения к МонгоДБ и исключения ошибок
def mongo_reader(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        with MongoClient(MONGODB_URL_READ) as client:
            collection = client[DB_NAME][COLLECTION_NAME]
            return func(collection, *args, **kwargs)

    return wrapper

# вернуть 5 самых популярных запросов.
@mongo_reader
def get_top_queries(collection, limit: int = 5):
    return list(
        collection.aggregate([
            {"$group": {"_id": {"search_type": "$search_type",
                                "query": "$query"},
                        "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}]))


# вернуть последние 5 запросов.
@mongo_reader
def get_last_queries(collection, limit: int = 5):
    return list(collection.find({},
                                {"_id": 0}).sort("created_at", -1).limit(limit))

