"""
Модуль с SQL-запросами приложения.

Назначение:
    Хранит текст SQL-запросов в виде констант.
    Используется для централизованного управления
    всеми запросами к базе данных.

Преимущества:
    - SQL-код отделен от бизнес-логики;
    - запросы легко изменять и сопровождать;
    - упрощается повторное использование запросов.

Содержит:

    GET_BY_NAME
        Поиск фильмов по названию.

    GET_BY_GENRES_AND_YEARS
        Поиск фильмов по жанру и диапазону годов.
"""

# database/queries.py
# import logging
# logger = logging.getLogger(__name__)

# ЗАПРОС №1 из БД sakila по дате и наименованию
GET_BY_NAME = """
              SELECT title, description, release_year
              FROM film
              WHERE title LIKE %s LIMIT 10
              OFFSET %s \
              """
# ЗАПРОС №2 из БД 'sakila' по жанрам и годам
GET_BY_GENRES_AND_YEARS = """
                          SELECT title, description, release_year, category_id
                          FROM film f
                                   JOIN film_category fc USING (film_id)
                          WHERE category_id = %s
                            AND release_year BETWEEN %s AND %s \
                          """