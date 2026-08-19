"""Получение и проверка данных, вводимых пользователем.

Модуль содержит функции для ввода команд, непустого текста, целых
чисел, диапазона лет и выбора жанра из ранее полученного списка.
Команда ``q`` при вводе команды завершает работу приложения.
"""

from colorama import Fore, Style
from database.film_service import get_release_year_category

MIN_YEAR = 1901
MAX_YEAR = 2155


def input_any(prompt: str) -> str:
    """Запрашивает непустой текст и обрабатывает команду вывода."""
    while True:
        value = input(prompt).strip().lower()

        if value == "q":
            print(Fore.CYAN + "\nExit the program.\n")
            raise SystemExit()
        elif value:
            return value

        print(Fore.RED + "\nThe value must not be empty.")


def input_number(message: str) -> int:
    """Запрашивает у пользователя целое число."""
    while True:
        value = input_any(message)

        if value.isdigit():
            return int(value)

        print(Fore.RED + "\nEnter a number.")


def input_year_range(genre_id, genre) -> tuple[int, int] | None:
    """Запрашивает и проверяет диапазон годов."""

    print(Fore.CYAN + "\nGenre:" + Style.RESET_ALL + Fore.WHITE, genre)

    year_min, year_max = get_release_year_category(genre_id)

    print(f"\nYear range for the selected genre: " + Fore.YELLOW +
          f"{year_min}-{year_max}"
          + Style.RESET_ALL + Fore.WHITE)

    while True:
        year_from = input_number("\nEnter the start year of the range (4 digits): ")
        if len(str(year_from)) != 4:
            print(Fore.RED + "\n\tInvalid year input")
            continue
        year_to = input_number("Enter the end year of the range (4 digits): ")

        if len(str(year_to)) == 4 and year_from <= year_to:

            if year_from < year_min:
                year_from = year_min
            if year_to > year_max:
                year_to = year_max

            return year_from, year_to

        else:
            print(Fore.RED + "\n\tInvalid year input")
            continue


def select_genre(rows: list[tuple], ) -> tuple[int, str]:
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
                           if current_id == genre_id), None, )

        if genre_name is not None:
            return genre_id, genre_name

        print(
            Fore.RED
            + "\nThe selected genre is not in the list.\n"
        )

def clear_screen() -> None:
    """Очищает экран терминала."""

    print("\033[2J\033[3J\033[H", end="", flush=True)
