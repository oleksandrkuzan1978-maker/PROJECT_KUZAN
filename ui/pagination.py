"""Постраничное отображение результатов поиска в консоли.

Модуль получает страницы результатов через переданную функцию
выборки, кеширует уже просмотренные страницы и выводит данные
в виде таблицы. Также обрабатывает переходы между страницами,
возврат к поиску или главному меню и завершение приложения.
"""

import logging
from typing import Any, TypeAlias
from collections.abc import Callable

from colorama import Fore, Style
from tabulate import tabulate

from ui.input_helpers import input_any, clear_screen
from utils.logger_config import funclog

QueryResult: TypeAlias = tuple[
    list[tuple[Any, ...]],
    list[str],
]

PageFetcher: TypeAlias = Callable[..., QueryResult]

logger = logging.getLogger(__name__)

PAGE_SIZE = 10


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

        command = input_any("")

        clear_screen()

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
def show_paginated_results(
        fetch_function: PageFetcher,
        fetch_args: tuple[str | int, ...],
        *,
        total: int,
        title: str,
        genre: str | None = None,
) -> str:
    """Отображает результаты поиска с постраничной навигацией.

        Для каждой новой страницы вычисляет смещение и вызывает функцию
        выборки с постоянными аргументами, размером страницы и смещением.
        Полученный результат сохраняется в локальном кеше, поэтому при
        повторном открытии просмотренной страницы запрос не выполняется.

        Переход вперёд с последней страницы открывает первую, а переход
        назад с первой страницы — последнюю.

        Args:
            fetch_function:
                Функция получения одной страницы результатов. После
                аргументов из ``fetch_args`` должна принимать значения
                ``limit`` и ``offset``.
            fetch_args:
                Постоянные позиционные аргументы функции выборки без
                значений ``limit`` и ``offset``.
            total:
                Общее количество найденных фильмов.
            title:
                Заголовок, отображаемый перед таблицей результатов.
            genre:
                Название выбранного жанра. Для поиска по названию фильма
                равно ``None``.

        Returns:
            Строку, обозначающую выбранное пользователем действие:

            - ``"search"`` — изменить параметры поиска;
            - ``"menu"`` — вернуться в главное меню;
            - ``"exit"`` — завершить приложение.
        """

    page_cache = {}  # Кеш для просмотренных страниц (для сокращения кол-ва SQL-запросов при пагинации)

    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    page = 1

    while True:
        # Очистка экрана
        clear_screen()

        print(Fore.YELLOW + title)
        offset = (page - 1) * PAGE_SIZE

        if page not in page_cache:  # Кеширование страниц с результатами
            page_cache[page] = fetch_function(*fetch_args, PAGE_SIZE, offset)
        rows, headers = page_cache[page]

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
