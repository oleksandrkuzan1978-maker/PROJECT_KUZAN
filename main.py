"""
Точка входа консольного приложения поиска фильмов.

Модуль настраивает журналирование, запускает пользовательский
интерфейс и выполняет финальную обработку необработанных ошибок.
"""
import logging
import sys

import mysql.connector

from utils.logger_config import setup_logging

setup_logging()
from ui.console import get_user_input
from utils.exceptions import ServiceUnavailableError
from config.local_settings import dbconfig

logger = logging.getLogger(__name__)  # Создаю логгер с именем "main".


# Метод getLogger возвращает объект логгера с именем этого модуля
def main() -> None:
    # Достаю из переменной (словаря) название БД
    db_name = dbconfig.get("database", "unknown")  # По умолчанию get возвращает "unknown"
    logger.info(f"=== Запуск приложения {db_name} Film Query ===")
    try:

        get_user_input()

        logger.info("=== Все запросы выполнены успешно ===")

    except ServiceUnavailableError as error:
        logger.exception(
            "Приложение не может обратиться к сервису %s",
            error.service,
        )
        print(
            f"{error.service} is unavailable. "
            "Check your network connection and try again."
        )
        sys.exit(1)

    except mysql.connector.Error:
        logger.exception("Приложение завершено из-за ошибки работы с БД")
        print("Database error.")
        sys.exit(1)

    except (KeyboardInterrupt, EOFError):
        logger.info("Приложение завершено пользователем")
        print("\nThe application has finished running.")

    except Exception:
        logger.critical(
            "Необработанное исключение достигло main().",
            exc_info=True
        )
        print("A critical error has occurred.")
        sys.exit(1)
    else:
        logger.info("Завершение приложения")


if __name__ == "__main__":
    main()
