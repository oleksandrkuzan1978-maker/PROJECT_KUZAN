"""
Хранение и чтение истории поисковых запросов в MongoDB.

Модуль сохраняет параметры выполненных поисков, возвращает
наиболее популярные запросы и последние записи истории.
Ошибки MongoDB передаются вызывающему уровню для обработки.
"""

# from pprint import pprint
from datetime import datetime
from pymongo import MongoClient  # pip install pymongo
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
)
from utils.exceptions import ServiceUnavailableError
from functools import wraps
from config.local_settings import (MONGODB_URL_ATLAS, MONGODB_URL_WRITE, MONGODB_URL_READ)
import logging

logger = logging.getLogger(__name__)

"""*********************** Создаем коллекцию ***************************"""

DB_NAME = "ich_edit"
COLLECTION_NAME = "final_project_060326_ptm_oleksandr_kuzan"
MONGODB_URL = MONGODB_URL_WRITE


# Ф-ция сохранения результата запроса в базе данных MongoDB
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
            Количество найденніх по запросу фильмов

    Raises:
        PyMongoError:
            Если подключиться к MongoDB или сохранить документ
            не удалось.
    """
    search_type, query, total = args

    document = {"search_type": search_type,
                "query": query,
                "results_count": total,
                "created_at": datetime.now()}

    try:

        with MongoClient(MONGODB_URL) as client:

            collection = client[DB_NAME][COLLECTION_NAME]

            collection.insert_one(document)

            # Если сильно хочется проверить результат записи в коллекцию:
            # print("Inserted ID:", result.inserted_id)  # result = collection.insert_one(document)

    except (ConnectionFailure, ServerSelectionTimeoutError) as error:
        raise ServiceUnavailableError("MongoDB") from error

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

        try:

            with MongoClient(MONGODB_URL) as client:
                collection = client[DB_NAME][COLLECTION_NAME]
                return func(collection, *args, **kwargs)

        except (ConnectionFailure, ServerSelectionTimeoutError) as error:
            raise ServiceUnavailableError("MongoDB") from error

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
            {"$limit": limit},]))


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

    return list(
        collection.aggregate([
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
