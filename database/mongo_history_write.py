"""
Хранение и чтение истории поисковых запросов в MongoDB.

Модуль сохраняет параметры выполненных поисков, возвращает
наиболее популярные запросы и последние записи истории.
Ошибки MongoDB передаются вызывающему уровню для обработки.
"""

# from pprint import pprint
from datetime import datetime
from typing import Any

# from collections import Counter
# from pathlib import Path
from pymongo import MongoClient  # pip install pymongo
from pymongo.errors import PyMongoError
from functools import wraps
from config.local_settings import (MONGODB_URL_ATLAS, MONGODB_URL_WRITE, MONGODB_URL_READ)
import logging

logger = logging.getLogger(__name__)

"""*********************** Создаем коллекцию ***************************"""

DB_NAME = "ich_edit"
COLLECTION_NAME = "final_project_060326_ptm_oleksandr_kuzan"

# Ф-ция сохранения результата запроса в базе данных MongoDB
def save_query(search_type: str, query: str) -> None:
    """
    Сохраняет поисковый запрос в MongoDB.

    Args:
        search_type:
            Вид поиска, например ``by_name`` или
            ``by_genre_years``.
        query:
            Текстовое представление параметров поиска.

    Raises:
        PyMongoError:
            Если подключиться к MongoDB или сохранить документ
            не удалось.
    """
    document = {
        "search_type": search_type,
        "query": query,
        "created_at": datetime.now(),
    }
    if search_type == "by_name":
        document["query"] = document["query"].replace("%", "")  # Заменяем в названии фильма % на ""

    with MongoClient(MONGODB_URL_ATLAS) as client:

        collection = client[DB_NAME][COLLECTION_NAME]

        collection.insert_one(document)

        # Если сильно хочется посмотреть, что и как записалось в коллекцию
        # for doc in collection.find():
        #     print(doc)

    logger.info("Поисковый запрос сохранён в MongoDB")

"""************************ Возвращаем запросы ***************************"""

# Декоратор подключения к МонгоДБ и исключения ошибок
def mongo_reader(func):
    """
    Предоставляет декорируемой функции коллекцию MongoDB.

    Декоратор открывает соединение для чтения, получает коллекцию,
    передаёт её первым аргументом функции и гарантирует закрытие
    клиента после завершения операции.

    Args:
        func:
            Функция, первым параметром которой является коллекция
            MongoDB.

    Returns:
        Обёрнутую функцию с автоматическим управлением клиентом
        MongoDB.

    Raises:
        PyMongoError:
            Если операция с MongoDB завершилась ошибкой.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):

        with MongoClient(MONGODB_URL_ATLAS) as client:
            collection = client[DB_NAME][COLLECTION_NAME]
            return func(collection, *args, **kwargs)

    return wrapper

# вернуть 5 самых популярных запросов.
@mongo_reader
def get_top_queries(collection, limit: int = 5):
    """
    Возвращает наиболее популярные поисковые запросы.

    Args:
        collection:
            Коллекция истории поисков MongoDB. Передаётся
            автоматически декоратором ``mongo_reader``.
        limit:
            Максимальное количество возвращаемых запросов.

    Returns:
        Список документов с параметрами запросов и количеством
        их выполнений.

    Raises:
        PyMongoError:
            Если получить данные из MongoDB не удалось.
    """
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
    """
        Возвращает последние поисковые запросы.

        Args:
            collection:
                Коллекция истории поисков MongoDB. Передаётся
                автоматически декоратором ``mongo_reader``.
            limit:
                Максимальное количество возвращаемых запросов.

        Returns:
            Список документов, отсортированных от новых к старым.

        Raises:
            PyMongoError:
                Если получить данные из MongoDB не удалось.
        """

    return list(collection.find({},
                                {"_id": 0}).sort("created_at", -1).limit(limit))

