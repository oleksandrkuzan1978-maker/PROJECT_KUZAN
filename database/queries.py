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

# ЗАПРОС из БД по общему количеству совпадений по имени
NAME_TOTAL = """
              SELECT COUNT(*)
              FROM film
              WHERE title LIKE %s """

# ЗАПРОС из БД по наименованию
GET_BY_NAME = """
              SELECT title, description, release_year
              FROM film
              WHERE title LIKE %s
              ORDER BY title, film_id
                  LIMIT %s
                  OFFSET %s """


# ЗАПРОС из БД по общему кол-ву совпадений по жанрам и годам
GENRES_TOTAL = """
                          SELECT COUNT(*)
                          FROM film AS f
                                   JOIN film_category AS fc USING (film_id)
                          WHERE category_id = %s
                            AND release_year BETWEEN %s AND %s """

# ЗАПРОС из БД по жанрам и годам
GET_BY_GENRES_AND_YEARS = """
                          SELECT title, description, release_year, category_id
                          FROM film AS f
                                   JOIN film_category AS fc USING (film_id)
                          WHERE category_id = %s
                            AND release_year BETWEEN %s AND %s 
                              ORDER BY f.title, f.film_id
                              LIMIT %s
                              OFFSET %s """

# ЗАПРОС жанров из БД 'sakila'
GET_GENRES = """
              SELECT category_id as number, name as name_genre
              FROM category
              ORDER BY category_id"""