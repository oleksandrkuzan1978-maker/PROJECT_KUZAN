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
from database.executor import execute_query
from database.queries import (
    NAME_TOTAL,
    GENRES_TOTAL,
    GET_BY_NAME,
    GET_BY_GENRES_AND_YEARS,
    GET_GENRES
)
from typing import Any
import logging

logger = logging.getLogger(__name__)  # Создаю логгер с именем "file_service".


# Метод getLogger возвращает объект логгера с именем этого модуля.


# Ф-ция возвращает общее кол-во совпадений по запросу
def show_total(name_or_genre: str | int, year_from=None, year_to=None) -> int:
    connection = get_connection()
    try:  # Если нужно преобразовать технические ошибки в бизнес-ошибки:
        cursor = connection.cursor()
        if year_from is None:
            rows, _ = execute_query(cursor,  # Общее кол-во совпадений по запросу
                                    NAME_TOTAL,
                                    name_or_genre)
        else:
            rows, _ = execute_query(cursor,  # Общее кол-во совпадений по запросу
                                    GENRES_TOTAL,
                                    name_or_genre, year_from, year_to)
        return rows[0][0]

    except mysql.connector.Error:
        logger.exception("Ошибка подключения при запросе №1_1 или 2_1")
        raise
    finally:
        connection.close()
        logger.info("Соединение для запросов 1_1, 2_1 закрыто")


def show_films_by_name(
        name: str,
        offset: int) -> tuple[list[tuple[Any, ...]], list[str]]:
    connection = get_connection()
    try:  # Если нужно преобразовать технические ошибки в бизнес-ошибки:
        cursor = connection.cursor()
        return execute_query(
            cursor,
            GET_BY_NAME,
            name,
            offset)

    except mysql.connector.Error:
        logger.exception("Ошибка подключения при запросе №1_2")
        raise
    finally:
        connection.close()
        logger.info("Соединение для запроса №1_2 закрыто")


def show_films_by_genre(
        num_genre: int,
        year_from: int,
        year_to: int,
        offset: int) -> tuple[list[tuple[Any, ...]], list[str]]:
    connection = get_connection()
    try:  # Если нужно преобразовать технические ошибки в бизнес-ошибки:
        cursor = connection.cursor()

        return execute_query(
            cursor,
            GET_BY_GENRES_AND_YEARS,
            num_genre,
            year_from,
            year_to,
            offset)

    except mysql.connector.Error:
        logger.exception("Ошибка подключения при запросе №1_2 или №2_2")
        raise
    finally:
        connection.close()
        logger.info("Соединение для запроса №1_2 и №2_2 закрыто")


def show_categories()-> tuple[list[tuple[Any, ...]], list[str]]:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        return execute_query(
            cursor,
            GET_GENRES)
    except mysql.connector.Error:
        logger.exception("Ошибка подключения при запросе №3")
        raise
    finally:
        connection.close()
        logger.info("Соединение для запроса №3 закрыто")
