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


def save_query(search_type, query):

    document = {
        "search_type": search_type,
        "query": query,
        "created_at": datetime.now(),
    }
    if search_type == "by_name":
        document["query"] = document["query"].replace("%", "")  # Заменяем в названии фильма % на ""

    try:
        with MongoClient(MONGODB_URL_WRITE) as client:

            collection = client[DB_NAME][COLLECTION_NAME]
            collection.insert_one(document)

            # Если сильно хочется посмотреть, что и как записалось в коллекцию
            # for doc in collection.find():
            #     print(doc)

        logger.info("Поисковый запрос сохранён в MongoDB")
        print(f"Поисковый запрос {COLLECTION_NAME} сохранён в MongoDB")

    except PyMongoError:
        logger.exception("Ошибка записи поискового запроса в MongoDB")
        raise

"""************************ Возвращаем запросы ***************************"""

# Декоратор подключения к МонгоДБ и исключения ошибок
def mongo_reader(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with MongoClient(MONGODB_URL_READ) as client:
                collection = client[DB_NAME][COLLECTION_NAME]
                return func(collection, *args, **kwargs)
        except PyMongoError:
            logger.exception("Ошибка чтения MongoDB")
            raise
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


# # вернуть 5 самых популярных запросов.
# def get_top_queries(limit: int = 5):
#     try:
#         with MongoClient(MONGODB_URL_READ) as client:
#             collection = client[DB_NAME][COLLECTION_NAME]
#             return list(
#                 collection.aggregate([
#                     {"$group": {"_id": {"search_type": "$search_type",
#                                         "query": "$query"},
#                                 "count": {"$sum": 1}}},
#                     {"$sort": {"count": -1}},
#                     {"$limit": limit}]))
#     except PyMongoError:
#         logger.exception("Ошибка чтения MongoDB")
#         raise


# # вернуть последние 5 запросов.
# def get_last_queries(limit: int = 5):
#     try:
#         with MongoClient(MONGODB_URL_READ) as client:
#             collection = client[DB_NAME][COLLECTION_NAME]
#             return list(collection.find({},
#                                         {"_id": 0}).sort("created_at", -1).limit(limit))
#     except PyMongoError:
#         logger.exception("Ошибка чтения MongoDB")
#         raise

# """ ********************** Блок задач **************************** """

# # === Задача 1 (пример решения) ===
# task_statement.append(
#     " 1. Из коллекции customers выяснить из какого города 'Sven Ottlieb'"
#
# )
#
# # ----- в result подставляем решение из mongodb -----
# # Вставляем сюда решение из МонгоДБ, удалив только строку о клиенте
# filter = {
#     'ContactName': 'Sven Ottlieb'
# }
# project = {
#     'ContactName': 1,
#     'City': 1,
#     '_id': 0
# }
#
# result = client['ich']['customers'].find(
#     filter=filter,
#     projection=project
# )
#
# data.append(result)
#
# # ===== Задача 2 =====
# task_statement.append(
#     '2. Из коллекции ich.US_Adult_Income найти возраст самого взрослого человека'
# )
#
# # ----- в result подставляем решение из mongodb -----
# # Requires the PyMongo package.
# #
#
# #client = MongoClient(
# #    'mongodb://ich1:password@mongo.itcareerhub.de/?readPreference=primary&ssl=false&authMechanism=DEFAULT&authSource=ich')
# result = client['ich']['customers'].aggregate([
#     {
#         '$project': {
#             'age': 1,
#             '_id': 0
#         }
#     }, {
#         '$sort': {
#             'age': -1
#         }
#     }, {
#         '$limit': 1
#     }
# ])
#
# data.append(result)


# """ *************** Блок вывода всех результатов на печать *************** """
#
# if len(data) != len(task_statement):
#     raise IndexError("Ошибка!!! Кол-во заданий НЕ РАВНО кол-ву решений!!!")
#
# # Цикл по задачам
# for task_num, result in enumerate(data):
#     print(50 * '=')
#     print(task_statement[task_num])
#     print()
#
#     # Цикл по выводу документов решения
#     docs = list(result)
#     for idx, doc in enumerate(docs[:TIMES]):
#         # print(idx, 50 * '-')
#         pprint(doc)
#
#     print(f"Total: {len(docs)} docs")
