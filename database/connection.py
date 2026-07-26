"""
Создание соединений с базой данных MySQL.

Параметры подключения загружаются из config.local_settings.
Модуль не выполняет SQL-запросы и не обрабатывает ошибки
на уровне пользовательского интерфейса.
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
