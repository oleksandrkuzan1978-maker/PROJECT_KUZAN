"""
Сервисный модуль для работы с фильмами.

Назначение:
    Реализует бизнес-логику приложения,
    связанную с получением информации о фильмах.

Функции модуля:
    - поиск фильмов по названию;
    - поиск фильмов по жанру и диапазону годов;
    - организация взаимодействия между
      SQL-запросами и пользовательским интерфейсом.

Особенности:
    Модуль использует:
        - database.connection
        - database.executor
        - database.queries

и скрывает детали работы с базой данных
от остальных частей программы.
"""

# services/film_service.py
import mysql.connector
from database.connection import get_connection
from utils.logger_config import funclog
from database.executor import execute_query
from typing import Any
import logging



# Метод getLogger возвращает объект логгера с именем этого модуля.
logger = logging.getLogger(__name__)  # Создаю логгер с именем "file_service".

# Ф-ция возвращает общее кол-во совпадений по запросу
@funclog
def show_total(query: str, *params: None | int | str) -> int:
    connection = get_connection()
    try:  # Если нужно преобразовать технические ошибки в бизнес-ошибки:
        cursor = connection.cursor()

        rows, _ = execute_query(cursor, query, *params)

        return rows[0][0]

    except mysql.connector.Error:
        logger.exception("Ошибка подключения при SQL-запросе")
        raise
    finally:
        connection.close()
        logger.info("Соединение для SQL-запросов закрыто")

@funclog
def show_films_by(query: str, *params:tuple[list[tuple[Any, ...]], list[str]] | None) -> tuple[list[tuple[Any, ...]], list[str]]:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        return execute_query(
            cursor,
            query,
            *params
        )
    except mysql.connector.Error:
        logger.exception("Ошибка подключения при SQL-запросе")
        raise
    finally:
        connection.close()
        logger.info("Соединение для SQL-запроса закрыто")

