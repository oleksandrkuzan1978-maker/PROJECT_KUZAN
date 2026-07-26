"""
Точка входа в приложение.

Назначение:
    Запускает выполнение программы и демонстрирует
    работу сервисов получения данных из базы данных.

Алгоритм работы:

    1. Импортирует необходимые сервисы.
    2. Вызывает функции бизнес-логики.
    3. Выводит результаты на экран.

Модуль должен содержать только код запуска приложения
и не должен включать SQL-запросы или логику работы
с базой данных.
"""

# main.py
from utils.logger_config import setup_logging
setup_logging()
from ui.console import get_user_input
import mysql.connector
from config.local_settings import dbconfig
import logging
import sys

logger = logging.getLogger(__name__) # Создаю логгер с именем "main".
                                     # Метод getLogger возвращает объект логгера с именем этого модуля
def main() -> None:
    # Достаю из переменной (словаря) название БД
    db_name = dbconfig.get("database", "unknown")  # По умолчанию get возвращает "unknown"
    logger.info(f"=== Запуск приложения {db_name} Film Query ===")
    try:
        get_user_input()

        logger.info("=== Все запросы выполнены успешно ===")

    except mysql.connector.Error:
        logger.error("Приложение завершено из-за ошибки работы с БД")
        print("Ошибка при работе с базой данных.")
        sys.exit(1)

    except (KeyboardInterrupt, EOFError):
        logger.info("Приложение завершено пользователем")
        print("\nРабота приложения завершена.")

    except Exception:
        logger.critical(
            "Необработанное исключение достигло main().",
            exc_info=True
        )
        print("Произошла критическая ошибка.")
        sys.exit(1)
    else:
        logger.info("Завершение приложения")


if __name__ == "__main__":
    main()


