# В корневом каталоге проекта запустить эту строку для проверки работоспособности пользовательского исключения на случай
# недоступности сервиса MongoDB
# python -c "from utils.exceptions import ServiceUnavailableError; raise ServiceUnavailableError('MongoDB')"


# Автоматический тест MySQL

"""Тесты подключения к MySQL. Запустите: python -m pytest tests/test_connection.py -v"""

from unittest.mock import patch

import pytest
from mysql.connector.errors import OperationalError

from database.connection import get_connection
from utils.exceptions import ServiceUnavailableError


def test_mysql_connection_error_is_converted() -> None:
    original_error = OperationalError("MySQL server is unavailable")

    with patch(
        "database.connection.mysql.connector.connect",
        side_effect=original_error,
    ):
        with pytest.raises(ServiceUnavailableError) as exc_info:
            get_connection()

    assert exc_info.value.service == "MySQL"
    assert exc_info.value.__cause__ is original_error