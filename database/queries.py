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

# ЗАПРОС #1_1 из БД по общему количеству совпадений по имени
NAME_TOTAL = """
              SELECT COUNT(*)
              FROM film
              WHERE title LIKE %s """

# ЗАПРОС №1_2 из БД по наименованию
GET_BY_NAME = """
              SELECT title, description, release_year
              FROM film
              WHERE title LIKE %s LIMIT 10
              OFFSET %s """


# ЗАПРОС №2_1 из БД по общему кол-ву совпадений по жанрам и годам
GENRES_TOTAL = """
                          SELECT COUNT(*)
                          FROM film AS f
                                   JOIN film_category AS fc USING (film_id)
                          WHERE category_id = %s
                            AND release_year BETWEEN %s AND %s """

# ЗАПРОС №2_2 из БД по жанрам и годам
GET_BY_GENRES_AND_YEARS = """
                          SELECT title, description, release_year, category_id
                          FROM film AS f
                                   JOIN film_category AS fc USING (film_id)
                          WHERE category_id = %s
                            AND release_year BETWEEN %s AND %s 
                              LIMIT 10
                              OFFSET %s """

# ЗАПРОС №3 жанров из БД 'sakila'
GET_GENRES = """
              SELECT category_id as "number", name as "name of genre"
              FROM category """