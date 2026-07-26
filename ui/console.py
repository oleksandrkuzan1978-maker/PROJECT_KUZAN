from collections.abc import Callable
from typing import Any
from tabulate import tabulate
from colorama import Fore, init, Style
from pymongo.errors import PyMongoError
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
def input_command(prompt: str) -> str:
    """Запрашивает команду и обрабатывает команду выхода."""
    value = input(prompt).strip().lower()

    if value == "q":
        print(Fore.CYAN + "\nВыход из программы.")
        raise SystemExit()

    return value


def input_text(prompt: str) -> str:
    """Запрашивает непустой текст без изменения регистра."""
    while True:
        value = input(prompt).strip()

        if value:
            return value

        print(Fore.RED + "Значение не должно быть пустым.")


def input_number(message: str) -> int:
    """Запрашивает у пользователя целое число."""
    while True:
        value = input_command(message)

        if value.isdigit():
            return int(value)

        print(Fore.RED + "Введите число.")


def input_year_range() -> tuple[int, int]:
    """Запрашивает и проверяет диапазон годов."""
    while True:
        year_from = input_number("Введите начальный год диапазона (4 цифры): ")
        year_to = input_number("Введите конечный год диапазона (4 цифры): ")

        if not MIN_YEAR <= year_from <= MAX_YEAR:
            print(
                Fore.RED
                + f"Начальный год должен быть от {MIN_YEAR} до {MAX_YEAR}."
            )
            continue

        if not MIN_YEAR <= year_to <= MAX_YEAR:
            print(
                Fore.RED
                + f"Конечный год должен быть от {MIN_YEAR} до {MAX_YEAR}."
            )
            continue

        if year_from > year_to:
            print(
                Fore.RED
                + "Начальный год не может быть больше конечного."
            )
            continue

        return year_from, year_to


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


def save_query_safely(search_type: str, query: str) -> None:
    """Сохраняет историю, не прерывая основной поиск при ошибке MongoDB."""
    try:
        save_query(search_type, query=query)
    except PyMongoError:
        logger.exception("Не удалось сохранить историю поиска в MongoDB")
        print(
            Fore.YELLOW
            + "Предупреждение: историю поиска сохранить не удалось."
        )


def handle_name_search() -> str | None:
    """Выполняет поиск фильмов по названию."""
    logger.info("Пользователь выбрал поиск по названию фильма")

    name = input_text("\nВведите название фильма: ")
    total = count_films_by_name(name)

    if total == 0:
        print("По данному запросу фильмы не найдены.")
        return None

    title = (
        f"\n========= Вывод фильмов из БД '{db_name}' по названию =========="
    )

    save_query_safely("by_name", name)

    return show_paginated_results(
        get_films_by_name,
        (name,),
        (total, title, None),
    )


def handle_genre_search() -> str | None:
    """Выполняет поиск фильмов по жанру и диапазону годов."""
    logger.info(
        "Пользователь выбрал поиск по жанру и диапазону лет выпуска"
    )

    rows, headers = get_genres()

    print(Fore.YELLOW + "\n======== Список жанров =======")
    print(tabulate(rows, headers=headers, tablefmt="psql"))

    while True:
        genre_id = input_number(
            Fore.GREEN
            + "Введите номер жанра: "
            + Style.RESET_ALL
            + Fore.WHITE
        )
        genre = next(
            (
                genre_name
                for current_id, genre_name in rows
                if current_id == genre_id
            ),
            None,
        )

        if genre is not None:
            break

        print(
            Fore.RED
            + "\n\tВыбранный жанр отсутствует в списке.\n"
        )

    year_from, year_to = input_year_range()
    total = count_films_by_genre_and_years(
        genre_id,
        year_from,
        year_to,
    )

    if total == 0:
        print("По данному запросу фильмы не найдены.")
        return None

    title = (
        f"\n========= Вывод фильмов по жанрам и годам "
        f"из БД '{db_name}' ========="
    )

    if year_from == year_to:
        history_query = f"Genre: {genre}, year: {year_from}"
    else:
        history_query = (
            f"Genre: {genre}, years: {year_from}-{year_to}"
        )

    save_query_safely("by_genre_years", history_query)

    return show_paginated_results(
        get_films_by_genre_and_years,
        (genre_id, year_from, year_to),
        (total, title, genre),
    )


def get_user_input() -> None:
    """Показывает главное меню и запускает выбранное действие."""
    logger.info("Запущен модуль пользовательского ввода")

    print(
        Fore.YELLOW
        + f"\n=== Application {db_name.upper()} Film Query ==="
    )
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
                + "\nВы ввели некорректный символ для выбора.\n"
            )
            continue

        try:
            result = action()

            if result == "exit":
                return

        except mysql.connector.ProgrammingError:
            logger.exception("Ошибка в SQL-запросе приложения")
            print(Fore.RED + "Внутренняя ошибка приложения.")
            return

        except mysql.connector.Error:
            logger.exception("Ошибка БД в консольном интерфейсе")
            print(
                Fore.RED
                + "Ошибка при обращении к базе данных. Попробуйте позже."
            )

        except PyMongoError:
            logger.exception("Ошибка чтения MongoDB")
            print(
                Fore.RED
                + "Не удалось получить историю поиска из MongoDB."
            )


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


"""Реализовано:
input_command() — команды приводятся к нижнему регистру, q завершает приложение;
input_text() — обычный текст сохраняет регистр и не воспринимает q как выход;
input_number() теперь корректно объявлен как возвращающий int;
input_year_range() проверяет оба года без их скрытой подмены;
handle_name_search() содержит поиск по названию;
handle_genre_search() содержит поиск по жанру и годам;
get_user_input() теперь представляет собой компактное главное меню;
save_query_safely() перехватывает PyMongoError, поэтому ошибка сохранения истории
                    не мешает показать найденные фильмы;
ошибки чтения истории MongoDB обрабатываются отдельно;
удалены все обращения к старой input_with_exit()."""
