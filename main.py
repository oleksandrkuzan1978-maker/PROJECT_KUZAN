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
from ui.console import get_user_input
import mysql.connector
from utils.logger_config import setup_logging
from config.local_settings import dbconfig
from database.film_service import (
    show_films_by_name,
    show_films_by_genre
)
import logging

setup_logging()

logger = logging.getLogger(__name__) # Создаю логгер с именем "main".
                                     # Метод getLogger возвращает объект логгера с именем этого модуля"


def main():
    # Достаю из переменной (словаря) название БД

    db_name = dbconfig.get("database", "unknown")  # По умолчанию get возвращает "unknown"
    logger.info(f"=== Запуск приложения {db_name} Film Query ===")
    try:
        first, year_from, year_to, offset = get_user_input()
        if not year_from:
            result = show_films_by_name(f"%{first}%", offset)
            print(f"\n========= Вывод фильмов из БД '{db_name}' по названию и году выпуска ==========")
            print(result,"\n")
        else:
            result = show_films_by_genre(first, year_from, year_to, offset)
            print(f"\n========= Вывод фильмов по жанрам и годам из БД '{db_name}' =========")
            print(result)
        logger.info("=== Все запросы выполнены успешно ===")
        logger.info("Завершение приложения")



    except mysql.connector.Error:
        print("Не удалось подключиться к БД")
        exit(1)
    except Exception:
        logger.exception("Критическая ошибка в main()")
        print("Произошла ошибка выполнения программы. Проверьте логи.")
        exit(1)


if __name__ == "__main__":
    main()


