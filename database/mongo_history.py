from pprint import pprint
from datetime import datetime
from pymongo import MongoClient  # pip install pymongo
from pymongo.errors import PyMongoError
from config.local_settings import MONGODB_URL_WRITE
import logging
# with MongoClient(MONGODB_URL_WRITE) as client:
#     TIMES = 5  # число документов на печать по умолчанию
#     task_statement = []  # список условий задач
#     data = []  # список документов по каждому решению задачи

# сохранить поисковый запрос.

logger = logging.getLogger(__name__)

DB_NAME = "ich"
COLLECTION_NAME = "final_project_060326_ptm_oleksandr_kuzan"

def save_query(name_genre, year_from=None, year_to=None):


    if year_from is None:
        document = {
            "search_type": "by_name",
            "query": name_genre,
            "created_at": datetime.now()
    }
    else:
        document = {
            "search_type": "by_genre_years",
            "genre_id": name_genre,
            "year_from": year_from,
            "year_to": year_to,
            "created_at": datetime.now()
        }
    try:
        with MongoClient(MONGODB_URL_WRITE) as client:
            collection = client[DB_NAME][COLLECTION_NAME]
            collection.insert_one(document)
        logger.info("Поисковый запрос сохранён в MongoDB")

    except PyMongoError:
        logger.exception("Ошибка записи поискового запроса в MongoDB")



# вернуть 5 самых популярных запросов.
def get_top_queries():
    pass


# вернуть последние 5 запросов.
def get_last_queries():
    pass