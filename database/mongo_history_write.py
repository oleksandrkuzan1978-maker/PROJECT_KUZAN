"""
Хранение и чтение истории поисковых запросов в MongoDB.

Модуль сохраняет параметры выполненных поисков, возвращает
наиболее популярные запросы и последние записи истории.
Ошибки MongoDB передаются вызывающему уровню для обработки.
"""

from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import (PyMongoError, ConnectionFailure,)
from utils.exceptions import ServiceUnavailableError
from functools import wraps
from config.local_settings import (MONGODB_URL_ATLAS, MONGODB_URL_WRITE, MONGODB_URL_READ)
import logging

logger = logging.getLogger(__name__)

"""*********************** Создаем коллекцию ***************************"""

DB_NAME = "ich_edit"
COLLECTION_NAME = "final_project_060326_ptm_oleksandr_kuzan"
MONGODB_URL = MONGODB_URL_WRITE
MONGODB_URL_1 = MONGODB_URL_ATLAS

client_write = MongoClient(MONGODB_URL_WRITE)
client_atlas = MongoClient(MONGODB_URL_ATLAS)
#client_read = MongoClient(MONGODB_URL_READ)

collection_write = client_write[DB_NAME][COLLECTION_NAME]
collection_atlas = client_atlas[DB_NAME][COLLECTION_NAME]
#collection_read = client_read[DB_NAME][COLLECTION_NAME]

def close_mongo_connections() -> None:
    """Закрывает все клиенты MongoDB."""

    client_write.close()
    client_atlas.close()

def mongo_errors(func):
    """ Декоратор. Перехватывает ошибки подключения к MongoDB. """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except ConnectionFailure as error:
            logger.exception("Не удалось подключиться к MongoDB")
            raise ServiceUnavailableError("MongoDB") from error

        except PyMongoError:
            logger.exception("Ошибка при выполнении операции в MongoDB")
            raise

    return wrapper


# def get_mongo_collection(mongodb_url):
#     """Создаёт клиент MongoDB и возвращает клиент и коллекцию."""
#
#     client = MongoClient(mongodb_url)
#     collection = client[DB_NAME][COLLECTION_NAME]
#
#     return client, collection


# Ф-ция сохранения результата SQL-запроса в базе данных MongoDB
@mongo_errors
def save_query(*args) -> None:
    """
    Сохраняет поисковый запрос в MongoDB.
  Args:
        search_type:
            Вид поиска, например ``by_name`` или
            ``by_genre_years``.
        query:
            Словарное представление параметров поиска.
        total:
            Количество найденных по запросу фильмов.
    """
    search_type, query, total = args

    document = {"search_type": search_type,
                "query": query,
                "results_count": total,
                "created_at": datetime.now()}


    # Запись запроса в основную MongoDB и в Atlas.
    collection_write.insert_one(document)
    collection_atlas.insert_one(document)

        # Если сильно хочется проверить результат записи в коллекцию:
        # print("Inserted ID:", result.inserted_id)  # result = collection_write.insert_one(document)

    logger.info("Поисковый запрос сохранён в MongoDB")


"""************************ Возвращаем запросы ***************************"""


# вернуть 5 самых популярных запросов.
@mongo_errors
def get_top_queries(limit: int = 5):
    """Возвращает наиболее популярные поисковые запросы."""

    return list(
        collection_write.aggregate([
            {"$group": {"_id": {"search_type": "$search_type",
                                "query": "$query"},
                        "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "search_type": "$_id.search_type",
                    "query": "$_id.query",
                    "count": 1,
                }
            }
        ]))


# вернуть последние 5 запросов.
@mongo_errors
def get_last_queries(limit: int = 5):
    """Возвращает последние уникальные поисковые запросы."""

    return list(
        collection_write.aggregate([
            # Сначала новые запросы
            {
                "$sort": {
                    "created_at": -1,
                }
            },

            # Объединяем одинаковые запросы
            {
                "$group": {
                    "_id": "$query",
                    "search_type": {"$first": "$search_type"},
                    "query": {"$first": "$query"},
                    "created_at": {"$first": "$created_at"},
                }
            },

            # После группировки порядок не гарантирован,
            # поэтому снова сортируем
            {
                "$sort": {
                    "created_at": -1,
                }
            },

            # Берём пять последних уникальных запросов
            {
                "$limit": limit,
            },

            # Не возвращаем техническое поле _id
            {
                "$project": {
                    "_id": 0,
                    "search_type": 1,
                    "query": 1,
                    "created_at": 1,
                }
            },
        ])
    )
