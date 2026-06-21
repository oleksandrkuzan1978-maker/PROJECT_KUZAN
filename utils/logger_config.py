# utils/logger_config.py
from colorlog import ColoredFormatter  # Для настройки цвета лог-сообщений в консоли
import logging
import os


def setup_logging():
    # Оформляем запись Пути к файлу "errors.log" так, чтобы этот путь читался в любой системе
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(base_dir, "logs", "errors.log")
    ###

    file_handler = logging.FileHandler(
        log_file,
        mode="w",  # режим перезаписи содержимого файла errors.log
        encoding="utf-8"
    )

    console_handler = logging.StreamHandler()
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | module: %(filename)s | line № %(lineno)d: | %(message)s")
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

    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            file_handler,
            console_handler
        ]
    )
