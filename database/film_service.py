"""
Сервисные операции для поиска фильмов.

Модуль предоставляет пользовательскому интерфейсу предметные
функции поиска и скрывает SQL-запросы, управление соединениями
и извлечение результатов из курсора.
"""

from typing import Any, TypeAlias

from database.connection import get_connection
from database.executor import execute_query
from utils.logger_config import funclog
from database.queries import (
    GENRES_TOTAL,
    GET_BY_GENRES_AND_YEARS,
    GET_BY_NAME,
    GET_GENRES,
    GET_RELEASE_YEAR_RANGE,
    NAME_TOTAL,
)

QueryResult: TypeAlias = tuple[
    list[tuple[Any, ...]],
    list[str],
]


# Приватная ф-ция осуществляет соединение
@funclog
def _execute(query: str, *params: Any) -> QueryResult:
    """Выполняет SELECT-запрос и возвращает строки с заголовками."""

    with get_connection() as connection:
        with connection.cursor() as  cursor:

            return execute_query(
                                cursor,
                                query,
                                *params)


def _get_count(
    query: str,
    *params: Any,
) -> int:
    """Возвращает COUNT(*) из переданного запроса."""

    rows, _ = _execute(query, *params)

    return rows[0][0]


def get_genres() -> QueryResult:
    """Возвращает список жанров."""

    return _execute(GET_GENRES)


def count_films_by_name(name: str) -> int:
    """Возвращает количество фильмов, найденных по названию."""

    name_pattern = f"%{name}%"

    return _get_count(NAME_TOTAL, name_pattern)

@funclog
def get_films_by_name(
    name: str,
    limit: int,
    offset: int,
) -> QueryResult:
    """Возвращает страницу фильмов, найденных по названию."""

    name_pattern = f"%{name}%"

    return _execute(
        GET_BY_NAME,
        name_pattern,
        limit,
        offset,
    )


def count_films_by_genre(
    genre_id: int,
    year_from: int,
    year_to: int,
) -> int:
    """Возвращает количество фильмов по жанру и годам."""

    return _get_count(
        GENRES_TOTAL,
        genre_id,
        year_from,
        year_to,
    )

@funclog
def get_films_by_genre(
    genre_id: int,
    year_from: int,
    year_to: int,
    limit: int,
    offset: int,
) -> QueryResult:
    """Возвращает страницу фильмов по жанру и годам."""

    return _execute(
        GET_BY_GENRES_AND_YEARS,
        genre_id,
        year_from,
        year_to,
        limit,
        offset,
    )

def get_release_year_range() -> tuple[int, int]:
    """Возвращает минимальный и максимальный годы выпуска фильмов."""

    rows, _ = _execute(GET_RELEASE_YEAR_RANGE)
    min_year, max_year = rows[0]

    return min_year, max_year

