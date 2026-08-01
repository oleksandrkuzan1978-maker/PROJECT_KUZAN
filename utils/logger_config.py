"""
Настройка системы журналирования приложения.

Модуль создаёт обработчики для информационных, отладочных
и ошибочных сообщений, задаёт формат записей и предоставляет
декоратор для журналирования вызовов функций.
"""

from colorlog import ColoredFormatter  # Для настройки цвета лог-сообщений в консоли
from typing import Callable, Any
from functools import wraps
import logging
import os
import sys

logger = logging.getLogger(__name__)


# Универсальный класс фильтров обработчиков
class ExactLevelFilter(logging.Filter):
    """Пропускает записи только указанного уровня."""

    def __init__(self, level: int) -> None:
        super().__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        """Возвращает True, если уровень записи точно совпадает."""
        return record.levelno == self.level


def setup_logging() -> None:
    """
    Настраивает систему логирования приложения.

    Создаёт обработчики для записи логов в файл и вывода в консоль,
    назначает соответствующие форматтеры и регистрирует обработчики
    через logging.basicConfig().

    Returns:
        None
    """

    # Оформляем запись Пути к лог-файлам так, чтобы эти пути читались в любой системе
    base_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))  # __file__ пайтон подставляет имя logger_config.py

    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    debug_log = os.path.join(log_dir, "debug.log")
    info_log = os.path.join(log_dir, "info.log")
    error_log = os.path.join(log_dir, "errors.log")

    # Создаю обработчик лог-сообщений для записи в лог-файл
    debug_handler = logging.FileHandler(
        debug_log,
        mode="w",
        encoding="utf-8",
    )

    info_handler = logging.FileHandler(
        info_log,
        mode="w",
        encoding="utf-8"
    )
    error_handler = logging.FileHandler(
        error_log,
        mode="w",  # режим перезаписи содержимого файла errors.log
        encoding="utf-8"
    )
    # -//- для вывода в консоль
    #
    console_handler = logging.StreamHandler(sys.stdout)

    # В форматерах задаем формат вывода лог-сообщений
    # Для вывода в файл
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | module: %(filename)s | line № %(lineno)d: | %(message)s")
    # Для вывода в консоль
    console_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s | %(levelname)s | %(name)s | module: %(filename)s | line № %(lineno)d: | %(message)s",
        log_colors={
            "DEBUG": "green",
            "INFO": "cyan",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red"
        }
    )
    # Назначаю уровни
    debug_handler.setLevel(logging.DEBUG)
    info_handler.setLevel(logging.INFO)
    error_handler.setLevel(logging.ERROR)
    console_handler.setLevel(logging.DEBUG)

    # Добавление универсальных фильтров
    debug_handler.addFilter(ExactLevelFilter(logging.DEBUG))
    info_handler.addFilter(ExactLevelFilter(logging.INFO))

    # связываю обработчики с форматерами:
    # «Когда *_handler записывает сообщение в файл, оформляю его по шаблону file_formatter»
    debug_handler.setFormatter(file_formatter)
    info_handler.setFormatter(file_formatter)
    error_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Создаю неявно логгер
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[  # Все сообщения логирования отправлять одновременно в файл и на экран терминала
            debug_handler,
            info_handler,
            error_handler
            # , console_handler
        ], force=True,
    )


# Декоратор, который записывает в info.log
# все вызовы функции с её аргументами и результатом.

def funclog(func: Callable) -> Callable:
    """
       Логирует вызов и успешное завершение функции.

       Декоратор не перехватывает исключения: если функция завершится
       ошибкой, сообщение об успешном завершении записано не будет.

       Args:
           func: Декорируемая функция.

       Returns:
           Функция-обёртка с сохранёнными метаданными исходной функции.
       """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.debug(
            "Вызов функции: %s",
            func.__name__,
        )

        result = func(*args, **kwargs)

        logger.debug(
            "Функция завершена: %s",
            func.__name__,
        )

        return result

    return wrapper
