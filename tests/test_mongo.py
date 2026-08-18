"""Необязательные интеграционные тесты реальной MongoDB.

По умолчанию тесты пропускаются. Для явного запуска задайте переменную
окружения ``RUN_MONGO_TESTS=1`` и выполните:

    python -m pytest tests/test_mongo.py -v
"""

import os
from uuid import uuid4

import pytest
from pymongo import MongoClient

from config.local_settings import MONGODB_URL_WRITE


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_MONGO_TESTS") != "1",
    reason="Для запуска требуется RUN_MONGO_TESTS=1",
)

TEST_DB_NAME = "ich_edit_test"
TEST_COLLECTION_NAME = "connection_test"


def test_mongodb_connection() -> None:
    """Проверяет доступность настроенного сервера MongoDB."""

    with MongoClient(
        MONGODB_URL_WRITE,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    ) as client:
        result = client.admin.command("ping")

    assert result["ok"] == 1.0


def test_mongodb_write_access() -> None:
    """Проверяет запись и удаляет созданный тестовый документ."""

    marker = str(uuid4())
    document = {
        "test": "connection",
        "marker": marker,
    }

    with MongoClient(
        MONGODB_URL_WRITE,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    ) as client:
        collection = client[TEST_DB_NAME][TEST_COLLECTION_NAME]

        try:
            result = collection.insert_one(document)
            saved_document = collection.find_one({"_id": result.inserted_id})

            assert saved_document is not None
            assert saved_document["marker"] == marker
        finally:
            collection.delete_one({"marker": marker})
