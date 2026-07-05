from pprint import pprint
from datetime import datetime
from pymongo import MongoClient  # pip install pymongo

from config.local_settings import MONGODB_URL_READ

# with MongoClient(MONGODB_URL_READ) as client:
#     TIMES = 5  # число документов на печать по умолчанию
#     task_statement = []  # список условий задач
#     data = []  # список документов по каждому решению задачи

# сохранить поисковый запрос.

def save_query(name_genre, year_from, year_to):

    if not year_from:
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

    with MongoClient(MONGODB_URL_READ) as client:
        collection = client["ich-edit"]["final_project_060326_ptm_oleksandr_kuzan"]
        collection.insert_one(document)


# вернуть 5 самых популярных запросов.
def get_top_queries():
    pass


# вернуть последние 5 запросов.
def get_last_queries():
    pass