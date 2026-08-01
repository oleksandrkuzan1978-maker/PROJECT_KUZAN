"""
Выполнение параметризованных SELECT-запросов MySQL.

Модуль содержит низкоуровневую функцию, которая выполняет
переданный запрос через открытый курсор и возвращает полученные
строки вместе с названиями столбцов.
"""

from typing import Any
from mysql.connector.cursor import MySQLCursorAbstract
from utils.logger_config import funclog
import logging

logger = logging.getLogger(__name__)  # Создаю логгер с именем "executor".


# Метод getLogger возвращает объект логгера с именем этого модуля.
@funclog
def execute_query(
        cursor: MySQLCursorAbstract,
        query: str,
        *params: Any,
) -> tuple[list[tuple[Any, ...]], list[str]]:
    """
        Выполняет параметризованный SELECT-запрос.

        Args:
            cursor:
                Открытый курсор MySQL.
            query:
                SQL-запрос с параметрами в формате драйвера MySQL.
            *params:
                Значения параметров SQL-запроса.

        Returns:
            Кортеж из списка полученных строк и списка названий
            столбцов результата.

        Raises:
            mysql.connector.Error:
                Если выполнить запрос или получить результат не удалось.
        """

    logger.debug(
        "Выполняется SQL-запрос: operation=%s, params_count=%d",
        query.lstrip().split(maxsplit=1)[0].upper(),
        len(params), )

    cursor.execute(query, params)  # Выполняется SQL-запрос. Результат хранится внутри курсора

    rows = cursor.fetchall()  # Методом курсора достаем сразу весь результат запроса из курсора.
    # Cписок кортежей. Каждый кортеж - это одна строка таблицы
    headers = [col[0] for col in cursor.description or ()]  # второй эл-нт - это шапка таблицы рез-тов

    logger.debug(
        "SQL-запрос выполнен: rows=%d, columns=%d",
        len(rows),
        len(headers),
    )
    return rows, headers
