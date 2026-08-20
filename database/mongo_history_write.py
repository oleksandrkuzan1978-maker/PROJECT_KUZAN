"""
Хранение и чтение истории поисковых запросов в MongoDB.

Модуль сохраняет параметры выполненных поисков, возвращает
наиболее популярные запросы и последние записи истории.
Ошибки MongoDB передаются вызывающему уровню для обработки.
"""

import logging
from datetime import datetime

from database.mongo_connection import (
    get_read_collection,
    get_write_collections,
    mongo_errors,
)

logger = logging.getLogger(__name__)


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

    document = {
        "search_type": search_type,
        "query": query,
        "results_count": total,
        "created_at": datetime.now(),
    }

    collections = get_write_collections()

    for collection in collections:
        collection.insert_one(document)

    if collections:
        logger.info("Поисковый запрос сохранён в MongoDB")
    else:
        logger.info("История поиска отключена в настройках")


"""************************ Возвращаем запросы ***************************"""


@mongo_errors
def get_top_queries(limit: int = 5):
    """Возвращает наиболее популярные поисковые запросы."""

    collection = get_read_collection()

    if collection is None:
        return []

    return list(
        collection.aggregate([
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


@mongo_errors
def get_last_queries(limit: int = 5):
    """Возвращает последние уникальные поисковые запросы."""

    collection = get_read_collection()

    if collection is None:
        return []

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
