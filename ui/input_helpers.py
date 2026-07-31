"""Получение и проверка данных, вводимых пользователем.

Модуль содержит функции для ввода команд, непустого текста, целых
чисел, диапазона лет и выбора жанра из ранее полученного списка.
Команда ``q`` при вводе команды завершает работу приложения.
"""

from colorama import Fore, Style

MIN_YEAR = 1901
MAX_YEAR = 2155

def input_command(prompt: str) -> str:
    """Запрашивает команду и обрабатывает команду выхода."""

    value = input(prompt).strip().lower()

    if value == "q":
        print(Fore.CYAN + "\nExit the program.\n")
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



