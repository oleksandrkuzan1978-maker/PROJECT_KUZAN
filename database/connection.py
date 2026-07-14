"""
Модуль для создания соединения с базой данных MySQL.

Назначение:
    Инкапсулирует логику подключения к СУБД MySQL и
    предоставляет функцию получения объекта соединения.

Использование:
    from database.connection import get_connection

    connection = get_connection()

Требования:
    - установлен пакет mysql-connector-python;
    - настроен словарь dbconfig в файле config/local_settings.py.

Содержит:
    get_connection() -> mysql.connector.MySQLConnection
"""

# database/connection.py
import mysql.connector
from config.local_settings import dbconfig # импорт словаря с настройками подключения
#from config.local_settings import dbconfig_write
from mysql.connector.connection import MySQLConnectionAbstract
import logging
from utils.logger_config import funclog


logger = logging.getLogger(__name__)

@funclog
def get_connection() ->MySQLConnectionAbstract:
    logger.debug("Параметры подключения загружены")
    try: # В этом модуле стоит ловить ошибки подключения
        conn = mysql.connector.connect(**dbconfig) # функция из библиотеки mysql.connector
                                                    # пытается установить соединение с сервером MySQL.
        logger.info("Успешное подключение к БД '%s'", dbconfig.get("database"))
        return conn # это объект соединения (MySQLConnection)
    except mysql.connector.Error:
        logger.exception("Ошибка подключения к MySQL")
        raise


# def get_connection_111():
#     logger.debug("Параметры подключения загружены")
#     try: # В этом модуле стоит ловить ошибки подключения
#         conn1 = mysql.connector.connect(**dbconfig_write) # функция из библиотеки mysql.connector
#                                                     # пытается установить соединение с сервером MySQL.
#         logger.info("Успешное подключение к БД '%s'", dbconfig_write.get("database"))
#         return conn1 # это объект соединения (MySQLConnection)
#     except mysql.connector.Error:
#         logger.exception("Ошибка подключения к MySQL")
#         raise