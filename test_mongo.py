from pymongo import MongoClient
from pymongo.errors import PyMongoError

from config.local_settings import MONGODB_URL_WRITE

# Проверка на подключение к MongoDB
try:
    with MongoClient(MONGODB_URL_WRITE, serverSelectionTimeoutMS=5000) as client:
        print(client.server_info())
        print("Подключение успешно")
except PyMongoError as err:
    print("Ошибка подключения:")
    print(err)

# Проверка на права доступа для записи
with MongoClient(MONGODB_URL_WRITE) as client:
    db = client["ich_edit"]
    collection = db["final_project_060326_ptm_oleksandr_kuzan"]

    result = collection.insert_one({"test": "hello"})
    print(result.inserted_id)