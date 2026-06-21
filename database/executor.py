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
from typing import Any

# database/executor.py
from config.local_settings import dbconfig
from tabulate import tabulate
import logging
logger = logging.getLogger(__name__)

def execute_query(cursor, query: str, *params) -> str:
    db_name = dbconfig.get("database", "unknown")
    if len(params)<3:
        print(f"\nВывод фильмов из БД '{db_name}' по названию и году выпуска :")
    else:
        print(f"\nВывод фильмов по жанрам и годам из БД '{db_name}':")

    cursor.execute(query, params)

    rows = cursor.fetchall()

    headers = [col[0] for col in cursor.description]

    return tabulate(rows, headers=headers, tablefmt="psql")