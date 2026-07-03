from tabulate import tabulate
from config.local_settings import dbconfig
from database.film_service import (show_total,
                                   show_categories,
                                   show_films_by_name,
                                   show_films_by_genre)
import logging
import keyboard
import os
import platform

PAGE_SIZE = 10

logger = logging.getLogger(__name__)

# ui/console.py

def check_exit(prompt):
    """Проверяет, не запросил ли пользователь выход."""
    value = input(prompt)
    if value == "q":
        print("Выход из программы.")
        raise SystemExit   # Генерирует исключение. Если это исключение нигде
                           # Не обработано (try ... except), то выполнение программы полностью прекращается.
    return value


def input_number(message):
    # Проверяет, является ли введенное значение - числом
    while True:
        value = input(message)

        if value.isdigit():
            return int(value)
        elif value == "q":
            print("\nВыход из программы.")
            raise SystemExit
        print("Введите число.")


# Ф-ция очистки экрана
def clear_screen():
    # Если ОС Windows, берем 'cls', иначе (macOS/Linux) — 'clear'
    command = 'cls' if platform.system().lower() == 'windows' else 'clear'
    return os.system(command)





def get_navigation(pages):
    """
    Возвращает действие пользователя.

    Возможные значения:
        ("next", None)
        ("prev", None)
        ("search", None)
        ("exit", None)
        ("goto", page_number)
    """

    while True:
        # Ждем первое событие клавиатуры
        event = keyboard.read_event()

        if event.event_type != keyboard.KEY_DOWN:
            continue

        key = event.name  # Проверяем, что клавишу именно НАЖАЛИ, а не отпустили

        # ---------- Ввод номера страницы ----------
        # 1. Если это цифра — собираем число
        if key.isdigit():

            user_input = key
            print(key, end="", flush=True) # Печатаем первую цифру без дублей

            while True:

                next_event = keyboard.read_event()

                if next_event.event_type != keyboard.KEY_DOWN:
                    continue

                next_key = next_event.name # Ловим только нажатия клавиш

                if next_key.isdigit():

                    user_input += next_key
                    print(next_key, end="", flush=True)

                elif next_key == "enter":

                    print()
                    break

            target_page = int(user_input) # Присваиваем собранное число
            #return "goto", target_page
            if 1 <= target_page <= pages:
                return "goto", target_page

            print(f"\nСтраница {target_page} отсутствует.")
            print(f"Введите правильный номер страницы: ", end="")
            continue


        # ---------- Стрелки ----------

        elif key == "right":
            return "next", None

        elif key == "left":
            return "prev", None

        # ---------- Новый поиск ----------

        elif key == "f":

            return "search", None

        # ---------- Выход ----------

        elif key == "q":

            return "exit", None



def get_user_input():

    db_name = dbconfig.get("database", "unknown")  # По умолчанию get возвращает "unknown"


    while True:

        print("\n\nВыберите, пожалуйста, критерии подбора фильмов:\n"
                       "    - выбрать фильм по названию, нажмите \"1\"\n"
                       "    - выбрать фильм по жанру \n"
                       "      и диапазону годов выпуска, нажмите \"2\": ", end="")


        choice = check_exit("")

        if choice == "1":
            logger.info("Поиск по названию фильма)")
            print()
            name = f"%{check_exit("\nВведите название фильма: ")}%"
            rows, _ = show_total(name, None, None)
            total = rows[0][0]

            print(f"\n========= Вывод фильмов из БД '{db_name}' по названию и году выпуска ==========")

            fetch_function = show_films_by_name
            fetch_args = (name,)

        elif choice == "2":
            logger.info("Поиск по жанру и диапазону лет выпуска")
            print()

            # Вывод на экран терминала списка жанров

            rows, headers = show_categories()
            number_genres = len(rows)

            print(f"\n======== Список жанров =======")
            print(tabulate(rows, headers=headers, tablefmt="psql"))


            # Ввод данных для поиска по жанрам и годам
            while True:
                genre = input_number("Введите номер жанра: ")
                if 1 <= genre <= number_genres:
                    break
                else:
                    print("\n\tВыбранный вами жанр отсутствует в списке")
                    continue

            while True:
                year_from = input_number("Введите начальный год диапазона (4 цифры): ")
                year_to = input_number("Введите конечный год диапазона (4 цифры): ")
                if len(str(year_from)) == len(str(year_to)) == 4 and year_from <= year_to:
                    break
                else:
                    print("Некорректный ввод года")
                    continue


            rows, headers = show_total(genre, year_from, year_to)
            total = rows[0][0]

            print(f"\n========= Вывод фильмов по жанрам и годам из БД '{db_name}' =========")

            fetch_function = show_films_by_genre
            fetch_args = (genre, year_from, year_to)



        elif choice == "q":
            print("\nСпасибо за использование программы!")
            return


        else:
            print("\nВы ввели некорректный символ для выбора.\n")
            continue # Возвращаем в начало цикла, если выбор неверный

        if total == 0:
            print("По данному запросу фильмы не найдены.")
            continue


        pages = (total + PAGE_SIZE - 1) // PAGE_SIZE  # Общее кол-во страниц для вывода полученных результатов



        page = 1

        while True:

            clear_screen() # Очистка экрана перед выводом новой страницы

            offset = (page - 1) * PAGE_SIZE


            # Получение результатов выполнения ф-ций show_films_by_name и show_films_by_genre
            rows, headers = fetch_function(
                *fetch_args,
                offset)

            # Вывод результатов в виде таблицы на экран
            print(tabulate(rows, headers=headers, tablefmt="psql"))
            print()

            print(f"Найдено: {total} фильма(ов)")
            print(f"Страница {page} из {pages}")

            print("\nНажмите [→] - далее, [←] - назад, [f] - новый поиск, [Esc] - выход")
            print("Или введите номер страницы и нажмите [Enter]: ", end="")

            action, value = get_navigation(pages)

            if action == "next":
                if page < pages:
                    page += 1
                else:
                    page = 1
            elif action == "prev":
                if page > 1:
                    page -=1
                else:
                    page = pages
            elif action == "goto":
                page = value
            elif action == "search":
                break
            elif action == "exit":
                print("\nСпасибо за использование программы!")
                return







