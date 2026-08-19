"""Создание, получение и закрытие подключений MongoDB."""

import logging
from functools import wraps

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, PyMongoError

from config.local_settings import (
    MONGODB_URL_ATLAS,
    MONGODB_URL_WRITE,
    USE_MAIN_MONGODB,
    USE_MONGODB_ATLAS,
)
from utils.exceptions import ServiceUnavailableError

DB_NAME = "ich_edit"
COLLECTION_NAME = "final_project_060326_ptm_oleksandr_kuzan"

client_write: MongoClient | None = None
client_atlas: MongoClient | None = None

collection_write: Collection | None = None
collection_atlas: Collection | None = None

logger = logging.getLogger(__name__)


def mongo_errors(func):
    """Перехватывает ошибки операций MongoDB."""

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


@mongo_errors
def open_mongo_connections() -> None:
    """Создаёт только включённые подключения MongoDB."""

    global client_write
    global client_atlas
    global collection_write
    global collection_atlas

    close_mongo_connections()

    if USE_MAIN_MONGODB:
        client_write = MongoClient(
            MONGODB_URL_WRITE,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        collection_write = client_write[DB_NAME][COLLECTION_NAME]

    if USE_MONGODB_ATLAS:
        client_atlas = MongoClient(
            MONGODB_URL_ATLAS,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        collection_atlas = client_atlas[DB_NAME][COLLECTION_NAME]


def close_mongo_connections() -> None:
    """Закрывает созданные клиенты MongoDB и очищает их значения."""

    global client_write
    global client_atlas
    global collection_write
    global collection_atlas

    if client_write is not None:
        client_write.close()

    if client_atlas is not None:
        client_atlas.close()

    client_write = None
    client_atlas = None
    collection_write = None
    collection_atlas = None


def get_write_collections() -> list[Collection]:
    """Возвращает все включённые коллекции для записи."""

    collections = []

    if collection_write is not None:
        collections.append(collection_write)

    if collection_atlas is not None:
        collections.append(collection_atlas)

    return collections


def get_read_collection() -> Collection | None:
    """Возвращает основную коллекцию или Atlas, если основная отключена."""

    if collection_write is not None:
        return collection_write

    return collection_atlas
