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


def _format_query(index: int, query_data: dict) -> str:
    """Форматирует поисковый запрос для вывода."""
    if query_data["search_type"] == "by_name":
        return (
            f"{index}. Search keyword: "
            f"{query_data['query']['keyword']}"
        )

    return (
        f"{index}. Genre: {query_data['query']['genre']}, "
        f"years: {query_data['query']['years']}"
    )


def _handle_invalid_history_data() -> None:
    logger.exception("Некорректный формат документов истории MongoDB")
    print(Fore.RED + "The search history contains incorrect data.")


@funclog
def output_top_queries() -> None:
    """Выводит наиболее популярные поисковые запросы."""

    queries = get_top_queries()

    print(Fore.YELLOW + "========== Top queries ==========" + Style.RESET_ALL + Fore.WHITE)

    try:
        for i, q in enumerate(queries, start=1):
            print(_format_query(i, q))
            print(f"   Number of requests: {q['count']}\n")

    except (KeyError, TypeError):
        _handle_invalid_history_data()


@funclog
def output_last_queries() -> None:
    """Выводит последние поисковые запросы пользователя."""

    queries = get_last_queries()

    print(Fore.YELLOW + "========== Recent queries ==========" + Style.RESET_ALL + Fore.WHITE)

    try:
        for i, q in enumerate(queries, start=1):
            print(_format_query(i, q))
            print(
                "   Request date: "
                f"{q['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

    except (KeyError, TypeError, AttributeError):
        _handle_invalid_history_data()
