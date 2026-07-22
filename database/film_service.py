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
from database.connection import get_connection
from utils.logger_config import funclog
from database.executor import execute_query
from typing import Any
#import mysql.connector
import logging

# Метод getLogger возвращает объект логгера с именем этого модуля.
logger = logging.getLogger(__name__)  # Создаю логгер с именем "file_service".
# Приватная ф-ция осуществляет соединение
def _execute(query, *params):

    connection = get_connection()

    try:
        cursor = connection.cursor()
        return execute_query(
            cursor,
            query,
            *params)
    finally:
        connection.close()
        logger.info("Соединение для SQL-запросов закрыто")


# Ф-ция возвращает результаты различных запросов
@funclog
def get_by(query: str, *params: Any) -> tuple[list[tuple[Any, ...]], list[str]]:

    return _execute(query, *params)
    # except mysql.connector.Error:
    #     logger.exception("Ошибка подключения при SQL-запросе")
    #     raise

#
# # Ф-ция возвращает общее кол-во совпадений по запросу
# @funclog
# def get_total_count(query: str, *params: None | int | str) -> int:
#
#     rows, _ = _execute(query, *params)
#
#     return rows[0][0]

