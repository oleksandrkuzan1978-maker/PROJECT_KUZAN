"""
Консольный интерфейс приложения поиска фильмов.

Модуль отвечает за ввод и проверку пользовательских данных, запуск
сервисных функций поиска, постраничный вывод результатов и отображение
истории запросов из MongoDB. Детали SQL-запросов и подключения к MySQL
скрыты в модулях слоя database.

Команда q завершает приложение в меню и при вводе числовых значений.
Ошибка сохранения истории в MongoDB не прерывает успешный поиск фильмов.
"""

from collections.abc import Callable
from typing import Any
from tabulate import tabulate
from colorama import Fore, init, Style
from pymongo.errors import PyMongoError
from config.local_settings import dbconfig
from utils.logger_config import funclog
from database.mongo_history_write import (save_query, get_top_queries, get_last_queries)
from database.film_service import (
    count_films_by_genre,
    count_films_by_name,
    get_films_by_genre,
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
def input_command(prompt: str) -> str:
    """Запрашивает команду и обрабатывает команду выхода."""

    value = input(prompt).strip().lower()

    if value == "q":
        print(Fore.CYAN + "\nExit the program.")
        raise SystemExit()

    return value


def input_text(prompt: str) -> str:
    """Запрашивает непустой текст без изменения регистра."""
    while True:
        value = input(prompt).strip()

        if value:
            return value

        print(Fore.RED + "\nThe value must not be empty.")


def input_number(message: str) -> int:
    """Запрашивает у пользователя целое число."""
    while True:
        value = input_command(message)

        if value.isdigit():
            return int(value)

        print(Fore.RED + "\nEnter a number.")


def input_year_range() -> tuple[int, int] | None:
    """Запрашивает и проверяет диапазон годов."""
    while True:
        year_from = input_number("\nEnter the start year of the range (4 digits): ")
        year_to = input_number("Enter the end year of the range (4 digits): ")

        if year_from < MIN_YEAR:
            year_from = MIN_YEAR
        if year_to > MAX_YEAR:
            year_to = MAX_YEAR

        if len(str(year_from)) == len(str(year_to)) == 4 and year_from <= year_to:
            return year_from, year_to

        else:
            print(Fore.RED + "\n\tInvalid year input")
            continue




# Ф-ция очистки экрана
def clear_screen() -> None:
    """ Очищает экран терминала.
        Для Windows выполняет команду «cls»,
        для Linux и macOS — команду «clear»."""

    command = 'cls' if platform.system().lower() == 'windows' else 'clear'
    os.system(command)


@funclog
def get_navigation(pages: int) -> tuple[str, None | int] | None:
    """
       Запрашивает команду постраничной навигации.

       Позволяет перейти вперёд или назад, открыть страницу по
       номеру, вернуться к новому поиску либо завершить приложение.
       Некорректный ввод запрашивается повторно.

       Args:
           pages: Общее количество доступных страниц.

       Returns:
           Кортеж (action, value), где action принимает значение:

           - «next» — следующая страница;
           - «prev» — предыдущая страница;
           - «goto» — переход к странице с номером value;
           - «search» — возврат к новому поиску;
           - "menu", None — вернуться в главное меню;
           - «exit» — завершение приложения.

           Для всех действий, кроме «goto», значение value равно None.
       """
    while True:

        print(
            "\nНажмите "
            + Fore.YELLOW + "[n]"
            + Style.RESET_ALL + Fore.WHITE + " — next, "
            + Fore.YELLOW + "[p]"
            + Style.RESET_ALL + Fore.WHITE + " — back, "
            + Fore.YELLOW + "[f]"
            + Style.RESET_ALL + Fore.WHITE + " — change search, "
            + Fore.YELLOW + "[m]"
            + Style.RESET_ALL + Fore.WHITE + " — main menu, "
            + Fore.YELLOW + "[q]"
            + Style.RESET_ALL + Fore.WHITE
            + " — Exit or enter page number: ",
            end="",
        )

        command = input().strip().lower()

        if command == "n":
            return "next", None

        if command == "p":
            return "prev", None

        if command == "f":
            return "search", None

        if command == "m":
            return "menu", None

        if command == "q":
            return "exit", None

        if command.isdigit():
            page = int(command)

            if 1 <= page <= pages:
                return "goto", page

            print(Fore.RED + f"\n\tPage {page} not found.")
            continue

        print(Fore.RED + "\n\tInvalid value entered.")


@funclog
def show_paginated_results(fetch_function: Callable
                           , fetch_args: tuple[str | int, ...]
                           , info_args: tuple[int, str, Any]) -> str:
    """
     Выводит результаты поиска с постраничной навигацией.

     Для текущей страницы вычисляет смещение, передаёт функции
     выборки постоянные аргументы, размер страницы и смещение,
     после чего отображает полученные строки в виде таблицы.

     Args:
         fetch_function:
             Функция получения одной страницы результатов.
             После аргументов из fetch_args она должна принимать
             параметры limit и offset.

         fetch_args:
             Постоянные аргументы функции выборки без параметров
             limit и offset.

         info_args:
             Кортеж (total, title, genre), содержащий общее
             количество найденных фильмов, заголовок результатов
             и название жанра либо None.

     Returns:
         «search», если пользователь вернулся к новому поиску,
         или «exit», если пользователь завершил приложение.
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
            print(Fore.CYAN + "Genre:" + Style.RESET_ALL + Fore.WHITE, genre)
        print(f"\nMovie(s) found: {total} ")
        print(f"Page {page} of {pages}")

        logger.debug(
            "Показана страница результатов: "
            "page=%d, pages=%d, rows=%d, offset=%d",
            page,
            pages,
            len(rows),
            offset,
        )

        action, value = get_navigation(pages)

        logger.debug(
            "Получена команда навигации: action=%s, value=%s",
            action,
            value,
        )

        if action == "next":
            page = page + 1 if page < pages else 1

        elif action == "prev":
            page = page - 1 if page > 1 else pages

        elif action == "goto":
            page = value

        elif action == "search":
            return "search"

        elif action == "menu":
            return "menu"

        elif action == "exit":
            print(
                Fore.CYAN
                + "\nThank you for using the program!\n"
            )
            return "exit"


def save_query_safely(search_type: str, query: str) -> None:
    """Сохраняет историю, не прерывая основной поиск при ошибке MongoDB."""
    try:
        save_query(search_type, query=query)
    except PyMongoError:
        logger.exception("Не удалось сохранить историю поиска в MongoDB")
        print(
            Fore.YELLOW
            + "Warning: Could not save search history."
        )


def select_genre(rows: list[tuple],) -> tuple[int, str]:
    """
    Запрашивает жанр из ранее полученного списка.

    Returns:
        Кортеж (genre_id, genre_name).
    """

    while True:
        genre_id = input_number(
            Fore.GREEN
            + "\nEnter the genre number: "
            + Style.RESET_ALL
            + Fore.WHITE
        )

        genre_name = next((name for current_id, name in rows
                           if current_id == genre_id), None,)

        if genre_name is not None:
            return genre_id, genre_name

        print(
            Fore.RED
            + "\nThe selected genre is not in the list.\n"
        )


def handle_name_search() -> str | None:
    """Выполняет полный сценарий поиска фильмов по названию.

    Запрашивает название, получает количество совпадений,
    сохраняет запрос в истории и запускает постраничный вывод
    найденных фильмов.

    Returns:
        «search» при возврате к новому поиску, «exit» при
        завершении приложения или None, если фильмы не найдены.

    Raises:
        mysql.connector.Error:
            Если произошла ошибка обращения к MySQL.
    """

    logger.info("Пользователь выбрал поиск по названию фильма")

    name = input_text("\nEnter the movie title: ")
    total = count_films_by_name(name)

    logger.info(
        "Поиск по названию выполнен: total=%d",
        total,
    )

    if total == 0:
        print("\nNo films were found for this query.")
        return None

    title = (
        f"\n========= Displaying movies from DB '{db_name}' by name =========="
    )

    save_query_safely("by_name", name)

    return show_paginated_results(
        get_films_by_name,
        (name,),
        (total, title, None),
    )


def handle_genre_search() -> str | None:
    """
       Управляет поиском фильмов по жанру и годам.

       Список жанров загружается один раз при входе в обработчика.
       Пользователь может изменять жанр и годы, не запрашивая
       список жанров повторно.
       """
    logger.info("Пользователь выбрал поиск по жанру и годам")

    # Единственный запрос списка жанров в рамках этого меню
    rows, headers = get_genres()

    print(Fore.YELLOW + "\n======== List of genres =======")
    print(
        tabulate(
            rows,
            headers=headers,
            tablefmt="psql",
        )
    )

    genre_id, genre = select_genre(rows)
    year_from, year_to = input_year_range()

    while True:
        total = count_films_by_genre(
            genre_id,
            year_from,
            year_to,
        )

        logger.info(
            "Поиск по жанру и годам выполнен: "
            "genre_id=%d, years=%d-%d, total=%d",
            genre_id,
            year_from,
            year_to,
            total,
        )

        if total == 0:
            print(
                Fore.RED
                + "\nNo films were found matching the specified parameters."
            )
        else:
            title = (
                f"\n========= Movies from DB '{db_name}' "
                f"by genre and year ========="
            )

            if year_from == year_to:
                history_query = (
                    f"Genre: {genre}, year: {year_from}"
                )
            else:
                history_query = (
                    f"Genre: {genre}, "
                    f"years: {year_from}-{year_to}"
                )

            save_query_safely(
                "by_genre_years",
                history_query,
            )

            result = show_paginated_results(
                get_films_by_genre,
                (genre_id, year_from, year_to),
                (total, title, genre),
            )

            if result == "exit":
                return "exit"

            if result == "menu":
                return None

        while True:
            command = input_command(
                Fore.GREEN
                + "\n[y] — change the years, "
                  "[g] — change genre, "
                  "[a] — change genre and years, "
                  "[m] — main menu, "
                  "[q] — exit: "
                + Style.RESET_ALL
                + Fore.WHITE
            )

            if command == "y":
                year_from, year_to = input_year_range()
                break

            if command == "g":
                print(
                    tabulate(
                        rows,
                        headers=headers,
                        tablefmt="psql",
                    )
                )

                genre_id, genre = select_genre(rows)
                break

            if command == "a":
                print(
                    tabulate(
                        rows,
                        headers=headers,
                        tablefmt="psql",
                    )
                )

                genre_id, genre = select_genre(rows)
                year_from, year_to = input_year_range()
                break

            if command == "m":
                return None

            print(
                Fore.RED
                + "\nUnknown command."
            )


def get_user_input() -> None:
    """
        Запускает главное меню консольного приложения.

        Показывает доступные действия, получает команду пользователя
        и запускает соответствующий обработчик поиска или просмотра
        истории. Обрабатывает ошибки MySQL и MongoDB, показывая
        пользователю понятное сообщение.

        Raises:
            SystemExit:
                Если пользователь ввёл команду «q».
        """

    logger.info("Запущен модуль пользовательского ввода")

    print(Fore.YELLOW + f"\n=== Application {db_name.upper()} Film Query ===")
    print(Fore.YELLOW + "___ Find movies for every taste ___")

    actions: dict[str, Callable[[], str | None]] = {
        "1": handle_name_search,
        "2": handle_genre_search,
        "3": output_top_queries,
        "4": output_last_queries,
    }

    while True:
        print(Fore.GREEN + "\n==== MOVIE SEARCH DASHBOARD ====")
        print(
            """1 - 🔍  Search by keyword
2 - 🎭  Search by genre and years
3 - ⭐  Show popular searches
4 - 🕒  Show recent searches
q - 🚪   Exit """
        )

        choice = input_command(
            Fore.GREEN
            + "\tMake a choice: "
            + Style.RESET_ALL
            + Fore.WHITE
        )
        print()

        action = actions.get(choice)

        if action is None:
            print(
                Fore.RED
                + "\nYou entered an invalid character for the selection.\n"
            )
            continue

        try:
            result = action()

            if result == "exit":
                return

        except mysql.connector.ProgrammingError:
            logger.exception("Ошибка в SQL-запросе приложения")
            print(Fore.RED + "Internal application error.")
            return

        except mysql.connector.Error:
            logger.exception("Ошибка БД в консольном интерфейсе")
            print(
                Fore.RED
                + "Error accessing the database. Please try again later."
            )

        except PyMongoError:
            logger.exception("Ошибка чтения MongoDB")
            print(
                Fore.RED
                + "Failed to retrieve search history from MongoDB."
            )

@funclog
def output_top_queries() -> None:
    """
        Выводит наиболее популярные поисковые запросы.

        Получает из MongoDB пять самых часто выполнявшихся запросов
        и показывает их вид, содержимое и количество выполнений.

        Raises:
            PyMongoError:
                Если не удалось получить историю из MongoDB.
        """

    queries = get_top_queries()

    print(Fore.YELLOW + "========== Top queries ==========" + Style.RESET_ALL + Fore.WHITE)
    try:
        for i, q in enumerate(queries, start=1):

            if q["_id"]["search_type"] == "by_name":
                print(f"{i}. Search keyword: {q["_id"]["query"]}")
            else:
                print(f"{i}. {q["_id"]["query"]}")
            print(f"   Number of requests: {q["count"]}\n")
    except (KeyError, TypeError):
        logger.exception("Некорректный формат документов истории MongoDB")
        print(
            Fore.RED
            + "The search history contains incorrect data."
        )

@funclog
def output_last_queries() -> None:
    """
    Выводит последние поисковые запросы пользователя.

    Получает из MongoDB пять последних записей истории и
    показывает содержимое каждого запроса и дату его выполнения.

    Raises:
        PyMongoError:
            Если не удалось получить историю из MongoDB.
    """

    queries = get_last_queries()

    print(Fore.YELLOW + "========== Recent queries ==========" + Style.RESET_ALL + Fore.WHITE)
    try:
        for i, q in enumerate(queries, start=1):

            if q["search_type"] == "by_name":
                print(f"{i}. Search keyword: {q["query"]}")
            else:
                print(f"{i}. {q["query"]}")
            print(f"   Request date: {q["created_at"].strftime("%Y-%m-%d %H:%M:%S")}\n")
    except (KeyError, TypeError, AttributeError):
        logger.exception(
            "Некорректный формат документов истории MongoDB"
        )
        print(
            Fore.RED
            + "The search history contains incorrect data."
        )


