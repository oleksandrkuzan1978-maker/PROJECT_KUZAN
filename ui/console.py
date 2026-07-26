from collections.abc import Callable
from typing import Any
from tabulate import tabulate
from colorama import Fore, init, Style
from config.local_settings import dbconfig
from utils.logger_config import funclog
from database.mongo_history_write import (save_query, get_top_queries, get_last_queries)
from database.film_service import (
    count_films_by_genre_and_years,
    count_films_by_name,
    get_films_by_genre_and_years,
    get_films_by_name,
    get_genres,
)
import mysql.connector
import logging
import os
import platform

logger = logging.getLogger(__name__)

db_name = dbconfig.get("database", "unknown")  # По умолчанию get возвращает "unknown"

logger.info("Запуск консольного интерфейса")

PAGE_SIZE = 10
MIN_YEAR = 1901
MAX_YEAR = 2155

init(autoreset=True)  # Для разноцветного ввода


# ui/console.py
@funclog
def input_with_exit(prompt: str) -> str:
    """
    Запрашивает ввод пользователя и завершает программу,
    если введена команда выхода.
    """
    value = input(prompt).strip().lower()

    if value == "q":
        print(Fore.CYAN + "\nВыход из программы.")
        raise SystemExit()

    return value


@funclog
def input_number(message: str) -> int | str | None:
    """
    Запрашивает у пользователя целое число.
    """
    while True:

        value = input_with_exit(message)

        if value.isdigit():
            return int(value)

        print(Fore.RED + "Введите число.")


# Ф-ция очистки экрана
def clear_screen() -> None:
    # Если ОС Windows, берем 'cls', иначе (macOS/Linux) — 'clear'
    command = 'cls' if platform.system().lower() == 'windows' else 'clear'
    os.system(command)


@funclog
def get_navigation(pages: int) -> tuple[str, None | int] | None:
    # Вариант для input
    """
      Запрашивает у пользователя команду навигации по страницам результатов.

      Пользователь может перейти к следующей или предыдущей странице,
      начать новый поиск, завершить работу программы либо перейти
      на страницу с указанным номером.

      Args:
          pages:
              Общее количество страниц результатов поиска.

      Returns:
          Кортеж вида (action, value), где:

          - "next", None   — перейти к следующей странице;
          - "prev", None   — перейти к предыдущей странице;
          - "search", None — начать новый поиск;
          - "exit", None   — завершить программу;
          - "goto", page   — перейти на страницу с номером page.

      Notes:
          Функция повторяет запрос до тех пор, пока пользователь
          не введёт корректную команду.
      """
    while True:
        print("\nНажмите " + Fore.YELLOW + "[n]" + Style.RESET_ALL + Fore.WHITE + "- далее " + Fore.YELLOW + "[p]"
              + Style.RESET_ALL + Fore.WHITE + "- назад, " + Fore.YELLOW + "[f]" + Style.RESET_ALL + Fore.WHITE +
              "- новый поиск, " + Fore.YELLOW + "[q]" + Style.RESET_ALL + Fore.WHITE + "- выход или введите"
              + Fore.YELLOW + " номер страницы: " + Style.RESET_ALL + Fore.WHITE, end="")
        command = input().strip().lower()

        if command == "n":
            return "next", None

        if command == "p":
            return "prev", None

        if command == "f":
            return "search", None

        if command == "q":
            return "exit", None

        if command.isdigit():
            page = int(command)

            if 1 <= page <= pages:
                return "goto", page

            print(Fore.RED + f"\n\tСтраница {page} отсутствует.")
            continue

        print(Fore.RED + "\n\tВвод некорректного значения.")


@funclog
def show_paginated_results(fetch_function: Callable
                           , fetch_args: tuple[str | int, ...]
                           , info_args: tuple[int, str, Any]) -> str:
    """
       Отображает результаты поиска постранично и организует навигацию
       между страницами.

       Функция запрашивает очередную страницу данных через переданную
       функцию выборки, выводит результаты в виде таблицы и позволяет
       пользователю:

       - перейти к следующей странице;
       - перейти к предыдущей странице;
       - открыть страницу по её номеру;
       - начать новый поиск;
       - завершить работу программы.

       Args:
           fetch_function:
               Функция, получающая очередную страницу результатов
               из базы данных.

           fetch_args:
               Аргументы, передаваемые функции fetch_function
               (без параметра offset).

           info_args:
               Кортеж, содержащий:

               - общее количество найденных фильмов;
               - заголовок окна результатов;
               - название жанра (или None).

       Returns:
           str:
               Возвращает:

               - "search" — если пользователь решил выполнить новый поиск;
               - "exit" — если пользователь завершил работу программы.
       """
    total, title, genre = info_args
    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    page = 1

    while True:
        # Очистка экрана
        clear_screen()

        print(Fore.YELLOW + title)
        offset = (page - 1) * PAGE_SIZE
        rows, headers = fetch_function(*fetch_args, PAGE_SIZE, offset)

        print(tabulate(rows, headers=headers, tablefmt="psql"))
        print()
        if genre is not None:
            print(Fore.CYAN + "Жанр:" + Style.RESET_ALL + Fore.WHITE, genre)
        print(f"Найдено: {total} фильма(ов)")
        print(f"Страница {page} из {pages}")

        action, value = get_navigation(pages)

        if action == "next":
            page = page + 1 if page < pages else 1

        elif action == "prev":
            page = page - 1 if page > 1 else pages

        elif action == "goto":
            page = value

        elif action == "search":
            break

        elif action == "exit":
            print(Fore.CYAN + "\nСпасибо за использование программы!\n")
            return "exit"
    return "search"


@funclog
def get_user_input() -> None:
    """
       Организует взаимодействие пользователя с консольным интерфейсом
       приложения.

       Функция отображает главное меню программы, запрашивает критерий
       поиска фильмов и, в зависимости от выбора пользователя,
       выполняет следующие действия:

       - поиск фильмов по названию;
       - поиск фильмов по жанру и диапазону годов выпуска;
       - вывод списка жанров;
       - проверку корректности введённых данных;
       - отображение результатов поиска с постраничной навигацией;
       - сохранение выполненного запроса в базе данных MongoDB.

       При возникновении ошибок доступа к базе данных выводит сообщение
       пользователю и записывает информацию об ошибке в журнал логирования.

       Returns:
           None

       Raises:
           SystemExit:
               Если пользователь завершил работу программы
               командой выхода.
       """
    logger.info("Запущен модуль пользовательского ввода")

    print(Fore.YELLOW + f"\n=== Application {db_name.upper()} Film Query ===")
    print(Fore.YELLOW + "___ Find movies for every taste ___")

    while True:
        print(Fore.GREEN + "\n==== MOVIE SEARCH DASHBOARD ====")
        print("""1 - 🔍  Search by keyword
2 - 🎭  Search by genre and years
3 - ⭐  Show popular searches
4 - 🕒  Show recent searches
q - 🚪   Exit """)
        choice = input_with_exit(Fore.GREEN + "\tMake a choice: " + Style.RESET_ALL + Fore.WHITE)
        print()
        # choice = input_with_exit(Fore.GREEN + "\n\nВыберите критерий поиска:\n" + Style.RESET_ALL + Fore.WHITE +
        #                "    - по названию, нажмите  " + Style.RESET_ALL + Fore.GREEN + "\'1\'\n" + Style.RESET_ALL + Fore.WHITE +
        #                "    - по жанру и диапазону\n"
        #                "    годов выпуска, нажмите " + Style.RESET_ALL + Fore.GREEN + "\'2\': " + Style.RESET_ALL + Fore.WHITE)
        try:
            if choice == "1":

                logger.info("Пользователь выбрал поиск по названию фильма")
                print()
                # Ввод данных для поиска по названию
                name = input_with_exit(
                    "\nВведите название фильма: "
                )

                if not name:
                    print("Название фильма не должно быть пустым.")
                    continue

                total = count_films_by_name(name)

                if total == 0:
                    print("По данному запросу фильмы не найдены.")
                    continue

                title = f"\n========= Вывод фильмов из БД '{db_name}' по названию =========="

                fetch_args = (name,)
                info_args = (total, title, None)

                save_query("by_name", query=name)  # Запись запроса в коллекцию MongoDB

                result = show_paginated_results(get_films_by_name, fetch_args, info_args)
                if result == "exit":
                    return  # exit()

            elif choice == "2":

                logger.info("Пользователь выбрал поиск по жанру и диапазону лет выпуска")
                print()

                # Вывод на экран терминала списка жанров
                rows, headers = get_genres()

                print(Fore.YELLOW + f"\n======== Список жанров =======")
                print(tabulate(rows, headers=headers, tablefmt="psql"))

                # Ввод данных для поиска по жанрам и годам
                while True:
                    num_genre = input_number(Fore.GREEN + "Введите номер жанра: " + Style.RESET_ALL + Fore.WHITE)
                    # Сразу находим нужный жанр из rows
                    genre = next((genre_name for genre_id, genre_name in rows
                                           if genre_id == num_genre), None,)
                    if genre is not None:
                        break
                    print("\n\tВыбранный вами жанр отсутствует в списке\n")

                while True:

                    year_from = input_number(Fore.WHITE + "Введите начальный год диапазона (4 цифры): ")
                    year_to = input_number(Fore.WHITE + "Введите конечный год диапазона (4 цифры): ")
                    # Ограничение диапазона годов для корректного выполнения SQL-запросов
                    if year_from < MIN_YEAR:
                        year_from = MIN_YEAR
                    if year_to > MAX_YEAR:
                        year_to = MAX_YEAR
                    # Проверка корректности ввода диапазона лет
                    if len(str(year_from)) == len(str(year_to)) == 4 and year_from <= year_to:
                        break
                    else:
                        print(Fore.RED + "\n\tНекорректный ввод года")
                        continue
                # Получение общего кол-ва совпадений по запросу
                total = count_films_by_genre_and_years(
                    num_genre,
                    year_from,
                    year_to,
                )

                if total == 0:
                    print("По данному запросу фильмы не найдены.")
                    continue

                title = f"\n========= Вывод фильмов по жанрам и годам из БД '{db_name}' ========="

                # fetch_function = get_films_by_genre_and_years
                fetch_args = (
                    num_genre,
                    year_from,
                    year_to,
                )
                info_args = (total, title, genre)

                if year_from == year_to:
                    save_query("by_genre_years", query=f"Genre: {genre}, year: {year_from}")
                else:
                    save_query("by_genre_years", query=f"Genre: {genre}, years: {year_from}-{year_to}")

                result = show_paginated_results(get_films_by_genre_and_years, fetch_args, info_args)

                if result == "exit":
                    return  # exit()

            elif choice == "3":
                output_top_queries()

            elif choice == "4":
                output_last_queries()

            elif choice == "q":
                print(Fore.CYAN + "\nСпасибо за использование программы!\n")
                return
            else:
                print(Fore.RED + "\nВы ввели некорректный символ для выбора.\n")
                continue  # Возвращаем в начало цикла, если выбор неверный

        except mysql.connector.ProgrammingError:
            logger.exception("Ошибка в SQL-запросе приложения")
            print(Fore.RED + "Внутренняя ошибка приложения.")
            return

        except mysql.connector.Error:
            print(Fore.RED + "Ошибка при обращении к базе данных. Попробуйте позже.")
            logger.exception("Ошибка БД в консольном интерфейсе")
            continue


# Выводим 5 самых часто посылаемых запросов и информацию об их количестве
def output_top_queries() -> None:
    queries = get_top_queries()

    print(Fore.YELLOW + "========== Top queries ==========" + Style.RESET_ALL + Fore.WHITE)

    for i, q in enumerate(queries, start=1):

        if q["_id"]["search_type"] == "by_name":
            print(f"{i}. Search keyword: {q["_id"]["query"]}")
        else:
            print(f"{i}. {q["_id"]["query"]}")
        print(f"   Number of requests: {q["count"]}\n")


# Выводим 5 самых последних запросов
def output_last_queries() -> None:
    queries = get_last_queries()

    print(Fore.YELLOW + "========== Recent queries ==========" + Style.RESET_ALL + Fore.WHITE)

    for i, q in enumerate(queries, start=1):

        if q["search_type"] == "by_name":
            print(f"{i}. Search keyword: {q["query"]}")
        else:
            print(f"{i}. {q["query"]}")
        print(f"   Request date: {q["created_at"].strftime("%Y-%m-%d %H:%M:%S")}\n")
