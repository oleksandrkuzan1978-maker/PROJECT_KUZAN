"""
Модуль для выполнения параметризованных SQL-запросов к базе данных sakila.

Перед использованием необходимо:

1. Установить пакет mysql-connector-python:

       pip install mysql-connector-python

2. Установить пакет tabulate:

       pip install tabulate

3. Создать файл local_settings.py и определить в нем словарь
   параметров подключения к базе данных:

       dbconfig = {
           "host": "localhost",
           "user": "root",
           "password": "password",
           "database": "sakila"
       }

Модуль выполняет следующие задачи:

- устанавливает соединение с БД MySQL;
- создает объект курсора для выполнения SQL-запросов;
- содержит шаблоны параметризованных SQL-запросов;
- позволяет получать данные из БД и выводить их
  в виде красиво отформатированной таблицы.

Используемые запросы:

1. Поиск фильмов по названию с поддержкой пагинации.
2. Поиск фильмов по жанру и диапазону годов выпуска.

Результаты запросов выводятся с использованием библиотеки tabulate.
"""

from typing import Any

import mysql.connector
from tabulate import tabulate  # pip install tabulate
from config.local_settings import dbconfig


connection = mysql.connector.connect(**dbconfig)

cursor = connection.cursor()

# ЗАПРОС №1 из БД sakila по дате и наименованию
get_by_name = """
              SELECT title, description, release_year
              FROM film
              WHERE title LIKE %s LIMIT 10
              OFFSET %s; \
              """

# ЗАПРОС №1 из БД 'sakila' по жанрам и годам
get_by_genres_and_years = """
                          SELECT title, description, release_year, category_id
                          FROM film as f
                                   JOIN film_category fc USING (film_id)
                          WHERE category_id = %s
                            AND release_year BETWEEN %s AND %s; \
                          """


# 2. Вывод результата запроса get_by_genres_and_years
def output_results_of_queries(cursor, query: str, *params: tuple[int]) -> str:
    """
    Выполняет SQL-запрос к базе данных и возвращает результат
    в виде форматированной таблицы.

    Функция принимает текст параметризованного SQL-запроса
    и произвольное количество параметров для подстановки
    в плейсхолдеры (%s).

    Алгоритм работы:

    1. Выполняет SQL-запрос через объект курсора.
    2. Получает все строки результата.
    3. Извлекает имена столбцов из cursor.description.
    4. Форматирует результат с помощью библиотеки tabulate.
    5. Возвращает готовую строку таблицы.

    :param query:
        SQL-запрос с параметрами вида %s.

    :param params:
        Значения, которые будут подставлены в SQL-запрос.
        Количество и порядок параметров должны соответствовать
        плейсхолдерам в запросе.

    :return:
        Строка с таблицей, содержащей результаты запроса.

    :rtype:
        str

    Примеры использования:

        output_results_of_queries(
            get_by_name,
            "%a%",
            10
        )

        output_results_of_queries(
            get_by_ganres_and_years,
            1,
            1994,
            2006
        )

    :raises mysql.connector.Error:
        Если при выполнении SQL-запроса возникла ошибка.
    """
    if len(params)<3:
        print("\nВывод фильмов из БД 'sakila' по названию и году выпуска :")
    else:
        print("\nВывод фильмов по жанрам и годам из БД 'sakila':")


    cursor.execute(query, params)  # 333333333333333333333 видать, параметры через импут вводим
    rows = cursor.fetchall()
    headers = [col[0] for col in cursor.description]

    return tabulate(rows, headers=headers, tablefmt="psql")  #


print(output_results_of_queries(cursor, get_by_name, "%a%", 10))
print(output_results_of_queries(cursor, get_by_genres_and_years, 1, 1994, 2006))
