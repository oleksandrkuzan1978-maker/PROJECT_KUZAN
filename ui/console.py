"""Управление консольным интерфейсом приложения поиска фильмов.

Модуль отображает главное меню, запускает поиск фильмов по названию
или по жанру и диапазону лет и связывает пользовательский интерфейс
с сервисами MySQL и MongoDB.

Получение и проверка пользовательского ввода, постраничный вывод
результатов и отображение истории запросов делегированы отдельным
модулям пакета :mod:`ui`.
"""

import logging
from collections.abc import Callable

import mysql.connector
from colorama import Fore, Style, init
from pymongo.errors import PyMongoError
from tabulate import tabulate

from config.local_settings import dbconfig
from database.film_service import (
    count_films_by_genre,
    count_films_by_name,
    get_films_by_genre,
    get_films_by_name,
    get_genres,
    get_release_year_range,
)
from database.mongo_history_write import save_query
from ui.history_view import output_last_queries, output_top_queries
from ui.input_helpers import (
    # input_command,
    input_any,
    input_year_range,
    select_genre,
)
from ui.pagination import clear_screen, show_paginated_results
from utils.exceptions import ServiceUnavailableError

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

    print(Fore.YELLOW + f"\n=== Application {db_name.upper()} Film Search ===")
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
        choice = input_any(
            Fore.GREEN
            + "\tMake a choice: "
            + Style.RESET_ALL
            + Fore.WHITE
        )
        clear_screen()  # Очистка экрана
        print()
        action = actions.get(choice) # Выбор ф-ции из actions по команде пользователя

        if action is None:
            print(
                Fore.RED
                + "\nYou entered an invalid character for the selection.\n"
            )
            continue

        try:

            result = action() # Вызов ф-ции, выбранной из словаря actions

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
            raise

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


def save_query_safely(*args) -> None:
    """Сохраняет историю, не прерывая основной поиск при ошибке MongoDB."""
    try:

        save_query(*args)

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
    """Выполняет сценарий поиска фильмов по названию.

        Запрашивает название фильма, получает количество совпадений,
        сохраняет параметры успешного поиска в MongoDB и запускает
        постраничное отображение найденных фильмов.

        Returns:
            Результат постраничной навигации:

            - ``"search"`` — изменить поисковый запрос;
            - ``"menu"`` — вернуться в главное меню;
            - ``"exit"`` — завершить приложение;
            - ``None`` — если фильмы не найдены.

        Raises:
            ServiceUnavailableError:
                Если MySQL недоступен.
            mysql.connector.Error:
                Если при работе с MySQL произошла другая ошибка.
        """

    logger.info("Пользователь выбрал поиск по названию фильма")
    while True:
        name = input_any("\nEnter the movie title: ")

        total = count_films_by_name(name)

        logger.info(
            "Поиск по названию выполнен: total=%d",
            total,
        )
        by_name = {"keyword": f"{name}"}
        save_query_safely("by_name", by_name, total,)

        if total == 0:
            print("\nNo films were found for this query.")
            return None

        title = (
            f"\n========= Displaying movies from DB '{db_name}' by name =========="
        )
        result = show_paginated_results(
            get_films_by_name,
            (name,),
            total=total,
            title=title,
        )
        if result == "search":
            # Повторяется цикл, снова запрашивается название
            continue
        if result == "exit":
            return "exit"
        return None # Команда "menu"



def display_genres(
        rows: list[tuple],
        headers: list[str],
        min_year: int,
        max_year: int,
) -> None:
    """Выводит список доступных жанров в виде таблицы.

    Args:
        rows:
            Строки с идентификаторами и названиями жанров.
        headers:
            Названия столбцов таблицы.
        min_year, max_year:
            Граничные года диапазона поиска в базе данных.
    """
    print(Fore.YELLOW + "\n====== List of genres =====")
    print(tabulate(rows, headers=headers, tablefmt="psql"))

    print(
        "\nДоступный диапазон годов: "
        + Fore.YELLOW
        + f"{min_year}–{max_year}"
        + Style.RESET_ALL
        + Fore.WHITE
    )


def handle_genre_search() -> str | None:
    """Управляет поиском фильмов по жанру и диапазону лет.

        При входе загружает список жанров из MySQL и повторно использует
        его в течение всего сценария. Пользователь может изменять годы,
        жанр либо оба параметра без повторного запроса списка жанров.

        Для каждого набора параметров функция получает количество
        совпадений, сохраняет успешный запрос в истории и запускает
        постраничное отображение результатов.

        Returns:
            ``"exit"``, если пользователь завершил приложение, или
            ``None`` при возврате в главное меню.

        Raises:
            ServiceUnavailableError:
                Если MySQL недоступен.
            mysql.connector.Error:
                Если при работе с MySQL произошла другая ошибка.
        """
    logger.info("Пользователь выбрал поиск по жанру и годам")

    # Единственный запрос списка жанров в рамках этого меню
    rows, headers = get_genres()

    min_year, max_year = get_release_year_range()

    display_genres(
        rows,
        headers,
        min_year,
        max_year,
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

        if year_from == year_to:
            history_query = {"genre": f"{genre}", "years": f"{year_from}"}
        else:
            history_query = {"genre": f"{genre}", "years": f"{year_from}-{year_to}"}

        save_query_safely(
            "by_genre_years",
            history_query, total,
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

            result = show_paginated_results(
                get_films_by_genre,
                (genre_id, year_from, year_to),
                total=total,
                title=title,
                genre=genre,
            )

            if result == "exit":
                return "exit"

            if result == "menu":
                return None

        while True:
            command = input_any(
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
                display_genres(
                    rows,
                    headers,
                    min_year,
                    max_year,
                )

                genre_id, genre = select_genre(rows)
                break

            if command == "a":
                display_genres(
                    rows,
                    headers,
                    min_year,
                    max_year,
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
