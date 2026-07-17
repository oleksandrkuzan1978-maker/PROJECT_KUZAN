from pprint import pprint
from datetime import datetime
from collections import Counter
from pathlib import Path
from pymongo import MongoClient  # pip install pymongo
from pymongo.errors import PyMongoError
from config.local_settings import MONGODB_URL_WRITE
import logging
import json


logger = logging.getLogger(__name__)

DB_NAME = "ich_edit"
COLLECTION_NAME = "final_project_060326_ptm_oleksandr_kuzan"

HISTORY_FILE = Path("data\search_history.json")


def load_history():

    if not HISTORY_FILE.exists():
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def write_history(history):

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=4)


def save_query(name_genre, year_from=None, year_to=None):

    if year_from is None:
        document = {
            "search_type": "by_name",
            "query": name_genre,
            "created_at": datetime.now().isoformat() #isoformat() - для записи в json-файл
    }
    else:
        document = {
            "search_type": "by_genre_years",
            "genre_id": name_genre,
            "year_from": year_from,
            "year_to": year_to,
            "created_at": datetime.now().isoformat()
        }
    # try:
    #     with MongoClient(MONGODB_URL_WRITE) as client:
    #         collection = client[DB_NAME][COLLECTION_NAME]
    #         collection.insert_one(document)
    #     logger.info("Поисковый запрос сохранён в MongoDB")
    #
    # except PyMongoError:
    #     logger.exception("Ошибка записи поискового запроса в MongoDB")
    try:
        history = load_history()
        history.append(document)
        write_history(history)
        logger.info("Поисковый запрос сохранён в JSON-файл")
    except OSError:
        logger.exception("Ошибка записи поискового запроса в JSON-файл")
        raise


# вернуть 5 самых популярных запросов.
def get_top_queries():
    pass


# вернуть последние 5 запросов.
def get_last_queries():
    pass