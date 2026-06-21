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
    GET_BY_NAME,
    GET_BY_GENRES_AND_YEARS
)

import logging

logger = logging.getLogger(__name__)


def show_films_by_name(
        name: str,
        offset: int):
    try:
        connection = get_connection()
    except mysql.connector.Error:
        print("Не удалось подключиться к БД")
        exit(1)

    cursor = connection.cursor()

    result = execute_query(
        cursor,
        GET_BY_NAME,
        name,
        offset)

    connection.close()

    return result


def show_films_by_genre(
        genre_id: int,
        year_from: int,
        year_to: int):
    connection = get_connection()
    try:
        cursor = connection.cursor()
    except mysql.connector.Error:
        print("Не удалось подключиться к БД")
        exit(1)
    result = execute_query(
        cursor,
        GET_BY_GENRES_AND_YEARS,
        genre_id,
        year_from,
        year_to
    )

    connection.close()

    return result
