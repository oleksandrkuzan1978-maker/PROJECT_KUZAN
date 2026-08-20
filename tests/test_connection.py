"""Изолированные тесты обработки ошибок MySQL и MongoDB."""

from unittest.mock import MagicMock, patch

import pytest
from mysql.connector.errors import OperationalError
from pymongo.errors import ServerSelectionTimeoutError

import database.mongo_connection as mongo_connection
from database.connection import get_connection
from database.mongo_connection import (
    close_mongo_connections,
    open_mongo_connections,
)
from database.mongo_history_write import (
    get_last_queries,
    get_top_queries,
    save_query,
)
from ui.console import save_query_safely
from utils.exceptions import ServiceUnavailableError


def test_mysql_connection_error_is_converted() -> None:
    """Ошибка соединения MySQL преобразуется в ошибку приложения."""

    original_error = OperationalError("MySQL server is unavailable")

    with patch(
        "database.connection.mysql.connector.connect",
        side_effect=original_error,
    ):
        with pytest.raises(ServiceUnavailableError) as exc_info:
            get_connection()

    assert exc_info.value.service == "MySQL"
    assert exc_info.value.__cause__ is original_error


def test_mongodb_connection_error_is_converted() -> None:
    """Ошибка соединения MongoDB преобразуется в ошибку приложения."""

    original_error = ServerSelectionTimeoutError(
        "MongoDB server is unavailable"
    )
    write_collection = MagicMock()
    atlas_collection = MagicMock()
    write_collection.insert_one.side_effect = original_error

    with patch(
        "database.mongo_history_write.get_write_collections",
        return_value=[write_collection, atlas_collection],
    ):
        with pytest.raises(ServiceUnavailableError) as exc_info:
            save_query(
                "by_name",
                {"keyword": "Alien"},
                1,
            )

    assert exc_info.value.service == "MongoDB"
    assert exc_info.value.__cause__ is original_error
    atlas_collection.insert_one.assert_not_called()


def test_atlas_disabled_does_not_create_client() -> None:
    """При выключенном Atlas создаётся только основной клиент."""

    with (
        patch.object(mongo_connection, "USE_MAIN_MONGODB", True),
        patch.object(mongo_connection, "USE_MONGODB_ATLAS", False),
        patch.object(mongo_connection, "MongoClient") as client_mock,
    ):
        open_mongo_connections()

        assert client_mock.call_count == 1
        assert mongo_connection.collection_write is not None
        assert mongo_connection.client_atlas is None
        assert mongo_connection.collection_atlas is None

    close_mongo_connections()


def test_atlas_enabled_creates_both_clients() -> None:
    """При включённом Atlas создаются оба клиента и коллекции."""

    write_client = MagicMock()
    atlas_client = MagicMock()

    with (
        patch.object(mongo_connection, "USE_MAIN_MONGODB", True),
        patch.object(mongo_connection, "USE_MONGODB_ATLAS", True),
        patch.object(
            mongo_connection,
            "MongoClient",
            side_effect=(write_client, atlas_client),
        ) as client_mock,
    ):
        open_mongo_connections()

        assert client_mock.call_count == 2
        assert mongo_connection.collection_write is not None
        assert mongo_connection.collection_atlas is not None
        assert (
            mongo_connection.get_read_collection()
            is mongo_connection.collection_write
        )

    close_mongo_connections()


def test_save_query_skips_atlas_when_disabled() -> None:
    """История пишется в основную базу без обращения к Atlas."""

    write_collection = MagicMock()

    with patch(
        "database.mongo_history_write.get_write_collections",
        return_value=[write_collection],
    ):
        save_query(
            "by_name",
            {"keyword": "Alien"},
            1,
        )

    write_collection.insert_one.assert_called_once()


def test_main_disabled_uses_only_atlas() -> None:
    """При выключенной основной базе создаётся только клиент Atlas."""

    with (
        patch.object(mongo_connection, "USE_MAIN_MONGODB", False),
        patch.object(mongo_connection, "USE_MONGODB_ATLAS", True),
        patch.object(mongo_connection, "MongoClient") as client_mock,
    ):
        open_mongo_connections()

        client_mock.assert_called_once_with(
            mongo_connection.MONGODB_URL_ATLAS,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        assert mongo_connection.client_write is None
        assert mongo_connection.collection_write is None
        assert mongo_connection.collection_atlas is not None
        assert (
            mongo_connection.get_read_collection()
            is mongo_connection.collection_atlas
        )

    close_mongo_connections()


def test_all_mongodb_connections_can_be_disabled() -> None:
    """При отключении обеих баз клиенты MongoDB не создаются."""

    with (
        patch.object(mongo_connection, "USE_MAIN_MONGODB", False),
        patch.object(mongo_connection, "USE_MONGODB_ATLAS", False),
        patch.object(mongo_connection, "MongoClient") as client_mock,
    ):
        open_mongo_connections()

        client_mock.assert_not_called()
        assert mongo_connection.get_write_collections() == []
        assert mongo_connection.get_read_collection() is None


def test_history_is_empty_when_all_connections_are_disabled() -> None:
    """Отключённая история не мешает приложению работать."""

    with (
        patch(
            "database.mongo_history_write.get_write_collections",
            return_value=[],
        ),
        patch(
            "database.mongo_history_write.get_read_collection",
            return_value=None,
        ),
    ):
        save_query(
            "by_name",
            {"keyword": "Alien"},
            1,
        )

        assert get_top_queries() == []
        assert get_last_queries() == []


def test_mongodb_error_does_not_interrupt_console_search() -> None:
    """Ошибка сохранения истории не прерывает консольный поиск."""

    with patch(
        "ui.console.save_query",
        side_effect=ServiceUnavailableError("MongoDB"),
    ):
        result = save_query_safely(
            "by_name",
            {"keyword": "Alien"},
            1,
        )

    assert result is None
