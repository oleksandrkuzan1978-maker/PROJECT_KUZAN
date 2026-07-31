"""Постраничный вывод результатов поиска в консоли.

Модуль получает отдельные страницы результатов через переданную
функцию выборки, кеширует уже просмотренные страницы и отображает
их в виде таблицы. Также он обрабатывает команды перехода между
страницами, возврата к поиску или главному меню и выхода из приложения.
"""

from collections.abc import Callable
from utils.logger_config import funclog
from colorama import Fore, Style
from typing import Any
from tabulate import tabulate
import logging

logger = logging.getLogger(__name__)

PAGE_SIZE = 10

def clear_screen() -> None:
    """Очищает экран терминала."""

    print("\033[2J\033[H", end="")


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

    page_cache = {} # Кеш для просмотренных страниц (для сокращения кол-ва SQL-запросов при пагинации)

    total, title, genre = info_args
    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    page = 1

    while True:
        # Очистка экрана
        clear_screen()

        print(Fore.YELLOW + title)
        offset = (page - 1) * PAGE_SIZE

        if page not in page_cache: # Кеширование страниц с результатами
            page_cache[page] = fetch_function(*fetch_args, PAGE_SIZE, offset)
        rows, headers = page_cache[page]  #fetch_function(*fetch_args, PAGE_SIZE, offset)

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
