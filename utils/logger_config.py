"""
Настройка системы журналирования приложения.

Модуль создаёт обработчики для информационных, отладочных
и ошибочных сообщений, задаёт формат записей и предоставляет
декоратор для журналирования вызовов функций.
"""

# utils/logger_config.py
from colorlog import ColoredFormatter  # Для настройки цвета лог-сообщений в консоли
from typing import Callable, Any
from functools import wraps
import logging
import os
import sys

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
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # __file__ пайтон подставляет имя logger_config.py

    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    info_log = os.path.join(log_dir, "info.log")
    error_log = os.path.join(log_dir, "errors.log")

    # Создаю обработчик лог-сообщений для записи в лог-файл
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
    #Назначаю уровни
    info_handler.setLevel(logging.INFO)
    error_handler.setLevel(logging.ERROR)
    console_handler.setLevel(logging.DEBUG)

    # Создаем фильтр для info_handler чтобы в файл info.log попадали только сообщения уровня INFO
    class InfoFilter(logging.Filter):
        """Пропускает только сообщения уровня INFO."""
        def filter(self, record) -> bool:
            """Возвращает True только для записи уровня INFO."""
            return record.levelno == logging.INFO

    # Добавляем фильтр
    info_handler.addFilter(InfoFilter())

    # связываю обработчики с форматерами:
    # «Когда *_handler записывает сообщение в файл, оформляю его по шаблону file_formatter»
    info_handler.setFormatter(file_formatter)
    error_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Создаю неявно логгер
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[ # Все сообщения логирования отправлять одновременно в файл и на экран терминала
            info_handler,
            error_handler
            #, console_handler
        ]
    )

# Декоратор, который записывает в info.log
# все вызовы функции с её аргументами и результатом.
def funclog(func: Callable) -> Callable:
    """
    Журналирует успешный вызов функции.

    После выполнения записывает имя функции, переданные
    позиционные аргументы и возвращённый результат. Исключения
    не перехватывает и не логирует.

    Args:
        func:
            Декорируемая функция.

    Returns:
        Функцию-обёртку с журналированием успешного вызова.
    """
    logger = logging.getLogger(func.__module__)

    @wraps(func)
    def wrapper(*args: Any) -> Any:

        result = func(*args)
        msg = f"function {func.__name__}"
        args_string = ", ".join(str(arg) for arg in args) if args else None
        #kwargs_string = ", ".join(f'{k}="{v}"' for k,v in kwargs.items()) if kwargs else None

        msg += f" | args: {args_string} | return: {result}" #kwargs: {kwargs_string}

        logger.info(msg)

        return result

    return wrapper


# В системе логирования Python есть четыре основных сущности:
#
# Logger — создаёт сообщения.
# Handler — решает, куда их отправить.
# Formatter — определяет внешний вид сообщения.
# Filter — может отбрасывать часть сообщений.