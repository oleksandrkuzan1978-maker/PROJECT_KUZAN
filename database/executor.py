"""
Модуль выполнения SQL-запросов.

Назначение:
    Содержит универсальные функции для работы
    с объектом курсора MySQL.

Функции модуля:
    - выполнение параметризованных SQL-запросов;
    - получение результатов;
    - форматирование результатов в табличный вид.

Используемые библиотеки:
    - mysql.connector
    - tabulate

Модуль не содержит бизнес-логики и не зависит
от конкретных таблиц базы данных.
"""
# database/executor.py
# from config.local_settings import dbconfig
# from tabulate import tabulate

from typing import Any
from mysql.connector.cursor import MySQLCursorAbstract
from utils.logger_config import funclog
import logging


logger = logging.getLogger(__name__)  # Создаю логгер с именем "executor".
                                      # Метод getLogger возвращает объект логгера с именем этого модуля.
@funclog
def execute_query(cursor: MySQLCursorAbstract, query: str, *params:Any,) -> tuple[list[tuple[Any, ...]], list[str]]:

    logger.debug("Выполняется SQL-запрос к БД ...")
    cursor.execute(query, params) # Выполняется SQL-запрос. Результат хранится внутри курсора

    rows = cursor.fetchall() # Методом курсора достаем сразу весь результат запроса из курсора.
                             # Cписок кортежей. Каждый кортеж - это одна строка таблицы
    headers = [col[0] for col in cursor.description or ()] # второй эл-нт - это шапка таблицы рез-тов

    return rows, headers


