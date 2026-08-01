# В корневом каталоге проекта запустить эту строку для проверки работоспособности
# самого класса пользовательского исключения

# python -c "from utils.exceptions import ServiceUnavailableError; raise ServiceUnavailableError('MongoDB')"


# 2. Автоматический тест MySQL

# """Тесты подключения к MySQL. Запустите: python -m pytest tests/test_connection.py -v"""
#
# from unittest.mock import patch
#
# import pytest
# from mysql.connector.errors import OperationalError
#
# from database.connection import get_connection
# from utils.exceptions import ServiceUnavailableError
#
#
# def test_mysql_connection_error_is_converted() -> None:
#     original_error = OperationalError("MySQL server is unavailable")
#
#     with patch(
#         "database.connection.mysql.connector.connect",
#         side_effect=original_error,
#     ):
#         with pytest.raises(ServiceUnavailableError) as exc_info:
#             get_connection()
#
#     assert exc_info.value.service == "MySQL"
#     assert exc_info.value.__cause__ is original_error
#




# #3. Проверка MongoDB
# """Тесты обработки недоступности MongoDB.
# Запуск: python -m pytest tests/test_connection.py -v
# """
#
# from unittest.mock import MagicMock, patch
#
# import pytest
# from pymongo.errors import ServerSelectionTimeoutError
#
# from database.mongo_history_write import save_query
# from utils.exceptions import ServiceUnavailableError
#
#
# def test_mongodb_connection_error_is_converted() -> None:
#     """Преобразует ошибку подключения MongoDB в исключение приложения."""
#     original_error = ServerSelectionTimeoutError(
#         "MongoDB server is unavailable"
#     )
#
#     mock_client = MagicMock()
#     mock_collection = (
#         mock_client.__enter__.return_value
#         .__getitem__.return_value
#         .__getitem__.return_value
#     )
#     mock_collection.insert_one.side_effect = original_error
#
#     with patch(
#         "database.mongo_history_write.MongoClient",
#         return_value=mock_client,
#     ):
#         with pytest.raises(ServiceUnavailableError) as exc_info:
#             save_query("by_name", "Alien")
#
#     assert exc_info.value.service == "MongoDB"
#     assert exc_info.value.__cause__ is original_error


# #4. Проверьте, что поиск не прерывается из-за MongoDB
#
# from unittest.mock import patch
#
# from ui.console import save_query_safely
# from utils.exceptions import ServiceUnavailableError
#
#
# def test_mongodb_error_does_not_interrupt_search() -> None:
#     with patch(
#         "ui.console.save_query",
#         side_effect=ServiceUnavailableError("MongoDB"),
#     ):
#         result = save_query_safely("by_name", "Alien")
#
#     assert result is None




#5. Ручная проверка MySQL
#Временно измените в dbconfig адрес сервера на заведомо недоступный:
# "host": "192.0.2.1",
# Затем запустите приложение и начните поиск.
# Ожидаемое сообщение: MySQL is unavailable. Please try again later.
# После проверки обязательно верните настоящий host.
# Адрес 192.0.2.1 относится к диапазону,
# зарезервированному для примеров, поэтому подходит для имитации недоступного узла.

