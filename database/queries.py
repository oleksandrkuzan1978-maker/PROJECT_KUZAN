"""
SQL-запросы приложения поиска фильмов.

Модуль содержит параметризованные запросы для получения фильмов,
подсчёта результатов и чтения списка жанров. Запросы выполняются
функциями слоя database и не должны форматироваться посредством
строковой конкатенации.
"""

# database/queries.py

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
                          SELECT title, description, release_year
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

GET_RELEASE_YEAR_RANGE = """
    SELECT MIN(release_year), MAX(release_year)
    FROM film
"""

GET_RELEASE_YEAR_CATEGORY = """
    SELECT MIN(release_year), MAX(release_year)
    FROM film AS f
    JOIN film_category AS fc
    ON f.film_id = fc.film_id
    WHERE fc.category_id = %s"""