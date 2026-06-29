
from config.local_settings import dbconfig
from database.film_service import (show_total,
                                   show_categories)
import logging

logger = logging.getLogger(__name__)

# ui/console.py

# Ф-ция возвращает значение оffset, требуемое в SQL-запросах и номер страницы вывода результатов page
def offset_page(total: int):
    limit = 10
    pages = (total + limit - 1) // limit  # Общее кол-во страниц для вывода полученных результатов
    # при максимальном кол-ве результатов на одну стр. = limit
    print(f"Общее кол-во совпадений = {total}")
    print(f"Общее кол-во страниц для вывода результатов = {pages}")
    page = int(input("Введите номер страницы, на которой вы хотите "
                     "просмотреть результаты вашего запроса: "))
    offset = (page - 1) * 10  # Вычисляем значение offset требуемое в SQL-запросах
    return offset, page


def get_user_input():
    db_name = dbconfig.get("database", "unknown")  # По умолчанию get возвращает "unknown"

    while True:
        choice = input("Выберите, пожалуйста, критерии подбора фильмов:\n"
                       "    - если вы хотите выбрать фильм по названию, нажмите \"1\"\n"
                       "    - если по жанру и диапазону годов выпуска, нажмите \"2\": ")

        if choice == "1":
            logger.info("Поиск по названию фильма)")
            print()
            name = input("Введите название фильма: ")
            total = show_total(f"%{name}%", None, None)
            offset, page = offset_page(total)
            return name, None, None, offset

        elif choice == "2":
            logger.info("Поиск по жанру и диапазону лет выпуска")
            print()
            # Вывод на экран терминала списка жанров
            logger.info("Вывод списка жанров)")
            result3 = show_categories()
            logger.info("Результат запроса №3 (вывод списка жанров) получен")
            print(f"\n======== Список жанров =======")
            print(result3)

            # Ввод данных для поиска по жанрам и годам
            genre = int(input("Из предложенного списка жанров выберите\n"
                              "по номеру интересующий вас жанр картины: "))
            year_from = int(input("Введите начальный год диапазона (4 цифры): "))
            year_to = int(input("Введите конечный год диапазона (4 цифры): "))
            total = show_total(genre, year_from, year_to)
            offset, page = offset_page(total)

            return genre, year_from, year_to, offset

        else:
            print("\nВы ввели некорректный символ для выбора.\n")

