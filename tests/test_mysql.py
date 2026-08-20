"""Необязательный тест реального подключения к MySQL.

Для запуска задайте ``RUN_MYSQL_TESTS=1`` и выполните:

    python -m pytest tests/test_mysql.py -v
"""

import os

import pytest

from database.connection import get_connection


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_MYSQL_TESTS") != "1",
    reason="Для запуска требуется RUN_MYSQL_TESTS=1",
)


def test_mysql_connection() -> None:
    """Проверяет создание и последующее закрытие соединения MySQL."""

    connection = get_connection()

    try:
        assert connection.is_connected()
    finally:
        connection.close()
