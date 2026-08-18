"""Изолированные тесты обработки ошибок MySQL и MongoDB."""

from unittest.mock import MagicMock, patch

import pytest
from mysql.connector.errors import OperationalError
from pymongo.errors import ServerSelectionTimeoutError

from database.connection import get_connection
from database.mongo_history_write import save_query
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

    with (
        patch(
            "database.mongo_history_write.collection_write",
            write_collection,
        ),
        patch(
            "database.mongo_history_write.collection_atlas",
            atlas_collection,
        ),
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
