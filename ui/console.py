"""Управление консольным интерфейсом приложения поиска фильмов.

Модуль отображает главное меню, запускает поиск фильмов по названию
или по жанру и диапазону лет и связывает пользовательский интерфейс
с сервисами MySQL и MongoDB.

Получение и проверка пользовательского ввода, постраничный вывод
результатов и отображение истории запросов делегированы отдельным
модулям пакета :mod:`ui`.
"""

from collections.abc import Callable
from tabulate import tabulate
from colorama import Fore, init, Style
from pymongo.errors import PyMongoError
from config.local_settings import dbconfig
from ui.pagination import show_paginated_results, clear_screen
from ui.input_helpers import input_command, input_text, select_genre, input_year_range
from ui.history_view import output_top_queries, output_last_queries
from database.mongo_history_write import save_query
from utils.exceptions import ServiceUnavailableError

from database.film_service import (
    count_films_by_genre,
    count_films_by_name,
    get_films_by_genre,
    get_films_by_name,
    get_genres,
)
import mysql.connector
import logging

logger = logging.getLogger(__name__)

db_name = dbconfig.get("database", "unknown")  # По умолчанию get возвращает "unknown"

logger.info("Запуск консольного интерфейса")

init(autoreset=True)  # Для разноцветного ввода


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

        # Очистка экрана
        clear_screen()

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

        except ServiceUnavailableError as error:
            logger.exception(
                "Внешний сервис недоступен: %s",
                error.service,
            )
            print(
                Fore.RED
                + f"{error.service} is unavailable. Check the connection "
                  "and try again."
            )

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



def save_query_safely(search_type: str, query: str) -> None:
    """Сохраняет историю, не прерывая основной поиск при ошибке MongoDB."""
    try:

        save_query(search_type, query=query)

    except ServiceUnavailableError:
        logger.exception("MongoDB недоступна: история не сохранена")
        print(
            Fore.YELLOW
            + "Warning: MongoDB is unavailable. "
              "Search history was not saved."
        )

    except PyMongoError:
        logger.exception("Не удалось сохранить историю поиска в MongoDB")
        print(
            Fore.YELLOW
            + "Warning: Could not save search history."
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