"""
Точка входа в приложение.

Назначение:
    Запускает выполнение программы и демонстрирует
    работу сервисов получения данных из базы данных.

Алгоритм работы:

    1. Импортирует необходимые сервисы.
    2. Вызывает функции бизнес-логики.
    3. Выводит результаты на экран.

Модуль должен содержать только код запуска приложения
и не должен включать SQL-запросы или логику работы
с базой данных.
"""

# main.py

from utils.logger_config import setup_logging
setup_logging()
# После этого:
# import database.connection
# import database.queries
# import database.executor
# import database.film_service
# import config.local_settings

import logging
logger = logging.getLogger(__name__)


from database.film_service import (
    show_films_by_name,
    show_films_by_genre
)
print()
logger.info("Выполнение SQL-запроса №1")
print(
    show_films_by_name(
        "%a%",
        10
    )
)
print()
logger.info("Выполнение SQL-запроса №2")
print(
    show_films_by_genre(
        1,
        1994,
        2006
    )
)


# def main():
#     print(show_films_by_name("%a%", 10))
#
#     print(
#         show_films_by_genre(
#             1,
#             1994,
#             2006
#         )
#     )
#
#
# if __name__ == "__main__":
#     main()

# def main():
#     logger.info("Приложение запущено")
#
#
# if __name__ == "__main__":
#     main()