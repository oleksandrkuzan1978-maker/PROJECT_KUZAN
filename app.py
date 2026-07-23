import logging
import math

import mysql.connector
from flask import Flask, render_template, request

from database.film_service import get_by
from database.mongo_history_write import (
    save_query,
    get_top_queries,
    get_last_queries,
)
from database.queries import (
    NAME_TOTAL,
    GENRES_TOTAL,
    GET_BY_NAME,
    GET_BY_GENRES_AND_YEARS,
    GET_GENRES,
)


app = Flask(__name__)

logger = logging.getLogger(__name__)

PAGE_SIZE = 10


@app.route("/")
def index():
    """Показывает главную страницу и загружает список жанров."""

    try:
        genres, _ = get_by(GET_GENRES)

        return render_template(
            "index.html",
            genres=genres,
            error=None,
        )

    except mysql.connector.Error:
        logger.exception("Не удалось загрузить список жанров")

        return render_template(
            "index.html",
            genres=[],
            error=(
                "Не удалось загрузить жанры из базы данных. "
                "Проверьте подключение к MySQL."
            ),
        )


@app.route("/search")
def search():
    """Обрабатывает разные виды поиска фильмов."""

    search_type = request.args.get(
        "search_type",
        "",
    ).strip()

    page = request.args.get(
        "page",
        default=1,
        type=int,
    )

    if page is None or page < 1:
        page = 1

    if search_type == "name":
        return search_by_name(page)

    if search_type == "genre_years":
        return search_by_genre_and_years(page)

    return render_template(
        "results.html",
        search_type=search_type,
        films=[],
        columns=[],
        total=0,
        page=1,
        pages=0,
        error="Неизвестный тип поиска.",
    )


def search_by_name(page: int):
    """Выполняет поиск фильмов по названию."""

    title = request.args.get(
        "title",
        "",
    ).strip()

    if not title:
        return render_template(
            "results.html",
            search_type="name",
            title=title,
            films=[],
            columns=[],
            total=0,
            page=1,
            pages=0,
            error="Введите название фильма.",
        )

    name = f"%{title}%"

    try:
        total_rows, _ = get_by(
            NAME_TOTAL,
            name,
        )

        total = total_rows[0][0]

        if total == 0:
            return render_template(
                "results.html",
                search_type="name",
                title=title,
                films=[],
                columns=[],
                total=0,
                page=1,
                pages=0,
                error=None,
            )

        pages = math.ceil(total / PAGE_SIZE)

        if page > pages:
            page = pages

        offset = (page - 1) * PAGE_SIZE

        films, columns = get_by(
            GET_BY_NAME,
            name,
            offset,
        )

        if page == 1:
            save_search_safely(
                search_type="by_name",
                query=name,
            )

        return render_template(
            "results.html",
            search_type="name",
            title=title,
            films=films,
            columns=columns,
            total=total,
            page=page,
            pages=pages,
            error=None,
        )

    except mysql.connector.Error:
        logger.exception(
            "Ошибка MySQL при поиске по названию: %s",
            title,
        )

        return render_template(
            "results.html",
            search_type="name",
            title=title,
            films=[],
            columns=[],
            total=0,
            page=1,
            pages=0,
            error="Не удалось выполнить поиск по названию.",
        )


def search_by_genre_and_years(page: int):
    """Выполняет поиск по жанру и диапазону годов."""

    genre_id = request.args.get(
        "genre_id",
        type=int,
    )

    year_from = request.args.get(
        "year_from",
        type=int,
    )

    year_to = request.args.get(
        "year_to",
        type=int,
    )

    genre_name = request.args.get(
        "genre_name",
        "",
    ).strip()

    validation_error = validate_genre_years(
        genre_id=genre_id,
        year_from=year_from,
        year_to=year_to,
    )

    if validation_error:
        return render_template(
            "results.html",
            search_type="genre_years",
            genre_id=genre_id,
            genre_name=genre_name,
            year_from=year_from,
            year_to=year_to,
            films=[],
            columns=[],
            total=0,
            page=1,
            pages=0,
            error=validation_error,
        )

    try:
        # Дополнительно получаем настоящее название жанра из БД.
        genres, _ = get_by(GET_GENRES)

        genre_names = {
            genre[0]: genre[1]
            for genre in genres
        }

        if genre_id not in genre_names:
            return render_template(
                "results.html",
                search_type="genre_years",
                genre_id=genre_id,
                genre_name="",
                year_from=year_from,
                year_to=year_to,
                films=[],
                columns=[],
                total=0,
                page=1,
                pages=0,
                error="Выбранный жанр отсутствует.",
            )

        genre_name = genre_names[genre_id]

        total_rows, _ = get_by(
            GENRES_TOTAL,
            genre_id,
            year_from,
            year_to,
        )

        total = total_rows[0][0]

        if total == 0:
            return render_template(
                "results.html",
                search_type="genre_years",
                genre_id=genre_id,
                genre_name=genre_name,
                year_from=year_from,
                year_to=year_to,
                films=[],
                columns=[],
                total=0,
                page=1,
                pages=0,
                error=None,
            )

        pages = math.ceil(total / PAGE_SIZE)

        if page > pages:
            page = pages

        offset = (page - 1) * PAGE_SIZE

        films, columns = get_by(
            GET_BY_GENRES_AND_YEARS,
            genre_id,
            year_from,
            year_to,
            offset,
        )

        if page == 1:
            if year_from == year_to:
                query_text = (
                    f"Genre: {genre_name}, "
                    f"year: {year_from}"
                )
            else:
                query_text = (
                    f"Genre: {genre_name}, "
                    f"years: {year_from}-{year_to}"
                )

            save_search_safely(
                search_type="by_genre_years",
                query=query_text,
            )

        return render_template(
            "results.html",
            search_type="genre_years",
            genre_id=genre_id,
            genre_name=genre_name,
            year_from=year_from,
            year_to=year_to,
            films=films,
            columns=columns,
            total=total,
            page=page,
            pages=pages,
            error=None,
        )

    except mysql.connector.Error:
        logger.exception(
            "Ошибка MySQL при поиске: жанр=%s, годы=%s-%s",
            genre_id,
            year_from,
            year_to,
        )

        return render_template(
            "results.html",
            search_type="genre_years",
            genre_id=genre_id,
            genre_name=genre_name,
            year_from=year_from,
            year_to=year_to,
            films=[],
            columns=[],
            total=0,
            page=1,
            pages=0,
            error="Не удалось выполнить поиск по жанру и годам.",
        )


def validate_genre_years(
        genre_id: int | None,
        year_from: int | None,
        year_to: int | None,
) -> str | None:
    """Проверяет параметры поиска по жанру и годам."""

    if genre_id is None:
        return "Выберите жанр."

    if year_from is None or year_to is None:
        return "Введите начальный и конечный годы."

    if len(str(year_from)) != 4 or len(str(year_to)) != 4:
        return "Год должен состоять из четырёх цифр."

    if year_from > year_to:
        return (
            "Начальный год не может быть больше "
            "конечного года."
        )

    return None


def save_search_safely(
        search_type: str,
        query: str,
) -> None:
    """
    Сохраняет историю поиска.

    Ошибка MongoDB не должна мешать показу
    результатов, полученных из MySQL.
    """

    try:
        save_query(
            search_type,
            query=query,
        )

    except Exception:
        logger.exception(
            "Не удалось сохранить запрос в MongoDB"
        )
@app.route("/top-queries")
def top_queries():
    """Показывает самые популярные поисковые запросы."""

    try:
        mongo_queries = get_top_queries() or []

        queries = []

        for item in mongo_queries:
            query_info = item.get("_id", {})

            queries.append(
                {
                    "search_type": query_info.get(
                        "search_type",
                        "",
                    ),
                    "query": query_info.get(
                        "query",
                        "",
                    ),
                    "count": item.get(
                        "count",
                        0,
                    ),
                }
            )

        return render_template(
            "top_queries.html",
            queries=queries,
            error=None,
        )

    except Exception:
        logger.exception(
            "Не удалось получить популярные запросы"
        )

        return render_template(
            "top_queries.html",
            queries=[],
            error=(
                "Не удалось получить популярные запросы. "
                "Проверьте подключение к MongoDB."
            ),
        )


@app.route("/recent-queries")
def recent_queries():
    """Показывает последние поисковые запросы."""

    try:
        mongo_queries = get_last_queries() or []

        queries = []

        for item in mongo_queries:
            created_at = item.get("created_at")

            if created_at is not None:
                created_at_text = created_at.strftime(
                    "%d.%m.%Y %H:%M:%S"
                )
            else:
                created_at_text = "Дата неизвестна"

            queries.append(
                {
                    "search_type": item.get(
                        "search_type",
                        "",
                    ),
                    "query": item.get(
                        "query",
                        "",
                    ),
                    "created_at": created_at_text,
                }
            )

        return render_template(
            "recent_queries.html",
            queries=queries,
            error=None,
        )

    except Exception:
        logger.exception(
            "Не удалось получить последние запросы"
        )

        return render_template(
            "recent_queries.html",
            queries=[],
            error=(
                "Не удалось получить последние запросы. "
                "Проверьте подключение к MongoDB."
            ),
        )

@app.errorhandler(404)
def page_not_found(error):
    """Показывает пользовательскую страницу ошибки 404."""

    logger.warning(
        "Страница не найдена: %s",
        request.path,
    )

    return render_template(
        "errors/404.html",
    ), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Показывает пользовательскую страницу ошибки 500."""

    logger.error(
        "Внутренняя ошибка приложения: %s",
        error,
        exc_info=True,
    )

    return render_template(
        "errors/500.html",
    ), 500

#
# @app.route("/test-500")
# def test_500():
#     raise RuntimeError(
#         "Тестовая ошибка 500"
#     )

if __name__ == "__main__":
    app.run(
        debug=True,
        use_reloader=False,
    )