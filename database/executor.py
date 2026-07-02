"""
Модуль выполнения SQL-запросов.

Назначение:
    Содержит универсальные функции для работы
    с объектом курсора MySQL.

Функции модуля:
    - выполнение параметризованных SQL-запросов;
    - получение результатов;
    - форматирование результатов в табличный вид.

Используемые библиотеки:
    - mysql.connector
    - tabulate

Модуль не содержит бизнес-логики и не зависит
от конкретных таблиц базы данных.
"""
#from typing import Any

# database/executor.py
# from config.local_settings import dbconfig
# from tabulate import tabulate
import mysql.connector
import logging

logger = logging.getLogger(__name__)  # Создаю логгер с именем "executor".
                                      # Метод getLogger возвращает объект логгера с именем этого модуля".

def execute_query(cursor, query: str, *params):

    try:  #В этом модуле стоит ловить ошибки выполнения SQL
        logger.info("Выполнение SQL-запроса к БД")
        cursor.execute(query, params) # Выполняется SQL-запрос. Результат хранится внутри курсора

        rows = cursor.fetchall() # Методом курсора достаем сразу весь результат запроса из курсора.
                                 # rows - список тюплов. Каждый тюпл - это одна строка таблицы
        return rows, [col[0] for col in cursor.description] # второй эл-нт - это шапка таблицы рез-тов
#
###

    except TypeError as te:  # Подумать, стоит ли ловить эту ошибку здесь
        logger.exception("Неверное количество параметров: %s", te) # передано в params не то кол-во параметров,
                                                                               # чем нужно для передачи в запрос
        raise
    except mysql.connector.ProgrammingError as pe:
        logger.exception("Неверный запрос: %s", pe)  # ошибки в запросе query
        raise
    except mysql.connector.Error as err:  # отлавливает ошибки, связанные с MySQL: не верный пароль,
                                          # не верное имя БД, ошибки в запросе, неверное количество параметров,
                                          # потеря соединения...
        logger.exception("Ошибка при выполнении SQL-запроса: %s", err)
        raise # raise нужен здесь, чтобы сообщение об ошибке, возникшей при вызове этого модуля
              # передалось дальше, в модуль, который будет вызывать эту функцию
    except Exception:
        logger.exception("Неожиданная ошибка")
        raise