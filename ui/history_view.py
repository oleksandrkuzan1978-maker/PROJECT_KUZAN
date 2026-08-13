"""Отображение истории поисковых запросов в консоли.

Модуль получает из MongoDB популярные и последние поисковые запросы,
форматирует полученные документы и выводит их пользователю. Ошибки
структуры документов регистрируются в журнале и преобразуются
в понятные сообщения интерфейса.
"""
import logging
from colorama import Fore, Style

from utils.logger_config import funclog
from database.mongo_history_write import (get_top_queries, get_last_queries)

logger = logging.getLogger(__name__)


@funclog
def output_top_queries() -> None:
    """
        Выводит наиболее популярные поисковые запросы.

        Получает из MongoDB пять самых часто выполнявшихся запросов
        и показывает их вид, содержимое и количество выполнений.

        Raises:
            PyMongoError:
                Если не удалось получить историю из MongoDB.
        """

    queries = get_top_queries()
    print(queries)

    print(Fore.YELLOW + "========== Top queries ==========" + Style.RESET_ALL + Fore.WHITE)
    try:
        for i, q in enumerate(queries, start=1):

            if q["_id"]["search_type"] == "by_name":
                print(f"{i}. Search keyword: {q["_id"]["query"]["keyword"]}")
            else:
                print(f"{i}. Genre: {q["_id"]["query"]["genre"]}, "
                      f"years: {q["_id"]["query"]["years"]}")
            print(f"   Number of requests: {q["count"]}\n")
    except (KeyError, TypeError):
        logger.exception("Некорректный формат документов истории MongoDB")
        print(
            Fore.RED
            + "The search history contains incorrect data."
        )


@funclog
def output_last_queries() -> None:
    """
    Выводит последние поисковые запросы пользователя.

    Получает из MongoDB пять последних записей истории и
    показывает содержимое каждого запроса и дату его выполнения.

    Raises:
        PyMongoError:
            Если не удалось получить историю из MongoDB.
    """

    queries = get_last_queries()

    print(Fore.YELLOW + "========== Recent queries ==========" + Style.RESET_ALL + Fore.WHITE)
    try:
        for i, q in enumerate(queries, start=1):

            if q["search_type"] == "by_name":
                print(f"{i}. Search keyword: {q["query"]["keyword"]}")
            else:
                print(f"{i}. Genre: {q["query"]["genre"]}, "
                      f"years: {q["query"]["years"]}")
            print(f"   Request date: {q["created_at"].strftime("%Y-%m-%d %H:%M:%S")}\n")
    except (KeyError, TypeError, AttributeError):
        logger.exception(
            "Некорректный формат документов истории MongoDB"
        )
        print(
            Fore.RED
            + "The search history contains incorrect data."
        )
