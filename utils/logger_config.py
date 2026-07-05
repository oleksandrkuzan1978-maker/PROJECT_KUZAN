"""
Настройка системы логирования приложения.

Модуль содержит функцию setup_logging(), которая конфигурирует
логирование для всего проекта.

В процессе настройки создаются два обработчика:

FileHandler — записывает сообщения в файл logs/errors.log;
StreamHandler — выводит сообщения в консоль.

Для каждого обработчика используется собственный форматтер:

Formatter — для записи логов в файл;
ColoredFormatter — для цветного отображения сообщений в терминале.

Уровень логирования установлен в DEBUG, поэтому будут
обрабатываться все сообщения уровней:

DEBUG, INFO, WARNING, ERROR и CRITICAL.

Пример использования:

from utils.logger_config import setup_logging
import logging

setup_logging()

logger = logging.getLogger(__name__)
logger.info("Приложение запущено")

"""

# utils/logger_config.py
from colorlog import ColoredFormatter  # Для настройки цвета лог-сообщений в консоли
import logging
import os
import sys


def setup_logging():
    """
    Настраивает систему логирования приложения.

    Создаёт обработчики для записи логов в файл и вывода в консоль,
    назначает соответствующие форматтеры и регистрирует обработчики
    через logging.basicConfig().

    Returns:
        None
    """

    # Оформляем запись Пути к файлу "errors.log" так, чтобы этот путь читался в любой системе
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # __file__ пайтон подставляет имя logger_config.py
    log_file = os.path.join(base_dir, "logs", "errors.log")
    ###
    # Создаю обработчик лог-сообщений для записи в лог-файл
    file_handler = logging.FileHandler(
        log_file,
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
    # связываю обработчики с форматерами:
    # «Когда file_handler записывает сообщение в файл, оформляй его по шаблону file_formatter.»
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    # Создаю неявно логгер
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[      # Все сообщения логирования отправлять одновременно в файл на экран терминала
            file_handler#,
            #console_handler
        ]
    )

# В системе логирования Python есть четыре основных сущности:
#
# Logger — создаёт сообщения.
# Handler — решает, куда их отправить.
# Formatter — определяет внешний вид сообщения.
# Filter — может отбрасывать часть сообщений.