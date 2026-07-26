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
from config.local_settings import dbconfig  # импорт словаря с настройками подключения
# from config.local_settings import dbconfig_write
from mysql.connector.connection import MySQLConnectionAbstract
import logging
from utils.logger_config import funclog

logger = logging.getLogger(__name__)

@funclog
def get_connection() -> MySQLConnectionAbstract: # None | PooledMySQLConnection | MySQLConnectionAbstract
    logger.debug("Попытка подключения к БД '%s'.\n"
                 "Используются параметры подключения из local_settings.py."
                 , dbconfig.get("database"))

    conn = mysql.connector.connect(
        **dbconfig)  # функция из библиотеки mysql.connector устанавливает соединение с сервером MySQL.
    logger.info("Успешное подключение к БД '%s'", dbconfig.get("database"))
    return conn  # это объект соединения (MySQLConnection)


# неверный пароль;
# сервер MySQL не запущен;
# база данных отсутствует;
# неправильный host.