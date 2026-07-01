
from config.local_settings import dbconfig
from database.film_service import (show_total,
                                   show_categories,
                                   show_films_by)
import logging
import keyboard
import os
import platform

logger = logging.getLogger(__name__)

# ui/console.py

def input_number(message):
    while True:
        value = input(message)

        if value.isdigit():
            return int(value)

        print("Введите число.")


# Ф-ция очистки экрана
def clear_screen():
    # Если ОС Windows, берем 'cls', иначе (macOS/Linux) — 'clear'
    command = 'cls' if platform.system().lower() == 'windows' else 'clear'
    return os.system(command)




def get_navigation(page, pages):
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

            if page < pages:
                return "next", None
            else:
                return "next", 1
            #print("\nЭто последняя страница.")


        elif key == "left":

            if page > 1:
                return "prev", None
            else:
                return "prev", pages
            #print("\nЭто первая страница.")


        # ---------- Новый поиск ----------

        elif key == "f":

            return "search", None

        # ---------- Выход ----------

        elif key == "esc":

            return "exit", None



def get_user_input():
    PAGE_SIZE = 10
    db_name = dbconfig.get("database", "unknown")  # По умолчанию get возвращает "unknown"

    while True:
        print("\nВыберите, пожалуйста, критерии подбора фильмов:\n"
                       "    - выбрать фильм по названию, нажмите \"1\"\n"
                       "    - выбрать фильм по жанру \n"
                       "      и диапазону годов выпуска, нажмите \"2\": ", end="")
        # print("Для выхода из программы нажмите 'q' и 'Enter'")
        choice = input()

        year_from = None
        year_to = None

        if choice == "1":
            logger.info("Поиск по названию фильма)")
            print()
            first = f"%{input("\nВведите название фильма: ")}%"
            total = show_total(first, None, None)
            print(f"\n========= Вывод фильмов из БД '{db_name}' по названию и году выпуска ==========")

        elif choice == "2":
            logger.info("Поиск по жанру и диапазону лет выпуска")
            print()
            # Вывод на экран терминала списка жанров

            result3 = show_categories() #, number_genres

            print(f"\n======== Список жанров =======")
            print(result3)


            # Ввод данных для поиска по жанрам и годам
            while True:
                first = input_number("Введите номер жанра: ")
                if 1 <= first <= 16: #number_genres:
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


            total = show_total(first, year_from, year_to)

            print(f"\n========= Вывод фильмов по жанрам и годам из БД '{db_name}' =========")
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

            result = show_films_by(
                first,
                year_from,
                year_to,
                offset
            )

            print(result)
            print()

            print(f"Найдено: {total} фильма(ов)")
            print(f"Страница {page} из {pages}")

            print("\nНажмите [→] - далее, [←] - назад, [f] - новый поиск, [Esc] - выход")
            print("Или введите номер страницы и нажмите [Enter]: ", end="")

            action, value = get_navigation(page, pages)

            if action == "next":
                if value == 1:
                    page = 1
                else:
                    page += 1

            elif action == "prev":
                if value == pages:
                    page = pages
                else:
                    page -= 1

            elif action == "goto":
                page = value

            elif action == "search":

                break

            elif action == "exit":

                print("\nСпасибо за использование программы!")
                return







