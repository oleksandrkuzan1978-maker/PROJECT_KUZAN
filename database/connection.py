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
from config.local_settings import dbconfig

import logging

logger = logging.getLogger(__name__)


def get_connection():
    logger.debug("Параметры подключения загружены")
    try:
        conn = mysql.connector.connect(**dbconfig)
        logger.info("Успешное подключение к БД '%s'", dbconfig.get("database"))
        return conn
    except mysql.connector.Error:
        logger.exception("Ошибка подключения к MySQL")
        raise
