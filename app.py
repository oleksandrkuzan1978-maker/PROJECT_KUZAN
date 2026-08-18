"""Веб-интерфейс приложения поиска фильмов на FastAPI."""
# Запуск для разработки: python -m uvicorn app:app --reload
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import mysql.connector
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pymongo.errors import PyMongoError

from database.film_service import (
    count_films_by_genre,
    count_films_by_name,
    get_films_by_genre,
    get_films_by_name,
    get_genres,
    get_release_year_range,
)
from database.mongo_history_write import (
    close_mongo_connections,
    get_last_queries,
    get_top_queries,
    open_mongo_connections,
    save_query,
)
from utils.exceptions import ServiceUnavailableError

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

PAGE_SIZE = 10

logger = logging.getLogger(__name__)

# Асинхронная ф-ция для управления жизненным циклом приложения
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Управляет клиентами MongoDB в течение работы веб-приложения."""

    open_mongo_connections()

    try:
        yield
    finally:
        close_mongo_connections()


# Объект приложения
app = FastAPI(
    title="Sakila Movie Search",
    description="Searching for films in the Sakila database",
    lifespan=lifespan,
)

# Cоздание объекта templates (шаблонизатора), через который Python-код может
# передавать html-шаблонам в директории TEMPLATES_DIR данные для формирования HTML.
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def render_error_page(
    request: Request,
    *,
    status_code: int,
    title: str,
    message: str,
):
    """Формирует HTML-страницу с сообщением об ошибке."""

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "status_code": status_code,
            "error_title": title,
            "error_message": message,
        },
        status_code=status_code,
    )

# Благодаря декоратору app.exception_handler FastAPI автоматически использует ф-цию при возникновении ошибки
@app.exception_handler(HTTPException)
def handle_http_exception(
    request: Request,
    exception: HTTPException,
):
    """Отображает ошибки пользовательского HTTP-запроса."""

    return render_error_page(
        request,
        status_code=exception.status_code,
        title="Ошибка запроса",
        message=str(exception.detail),
    )


@app.exception_handler(RequestValidationError)
def handle_validation_error(
    request: Request,
    exception: RequestValidationError,
):
    """Обрабатывает неверные типы и значения параметров."""

    logger.warning(
        "Некорректные параметры веб-запроса: %s",
        exception.errors(),
    )

    return render_error_page(
        request,
        status_code=422,
        title="Некорректные параметры",
        message=(
            "Проверьте введённые значения и повторите запрос."
        ),
    )


@app.exception_handler(ServiceUnavailableError)
def handle_service_unavailable(
    request: Request,
    exception: ServiceUnavailableError,
):
    """Обрабатывает недоступность MySQL или MongoDB."""

    logger.error(
        "Внешний сервис недоступен: %s",
        exception.service,
    )

    return render_error_page(
        request,
        status_code=503,
        title="Сервис временно недоступен",
        message=(
            f"Не удалось обратиться к сервису "
            f"{exception.service}. Попробуйте позже."
        ),
    )


@app.exception_handler(mysql.connector.Error)
def handle_mysql_error(
    request: Request,
    exception: mysql.connector.Error,
):
    """Обрабатывает ошибки выполнения операций MySQL."""

    logger.error(
        "Ошибка MySQL в веб-приложении: %s",
        exception,
    )

    return render_error_page(
        request,
        status_code=500,
        title="Ошибка базы данных",
        message=(
            "Не удалось выполнить запрос к базе фильмов."
        ),
    )


@app.exception_handler(PyMongoError)
def handle_mongodb_error(
    request: Request,
    exception: PyMongoError,
):
    """Обрабатывает ошибки чтения истории из MongoDB."""

    logger.error(
        "Ошибка MongoDB в веб-приложении: %s",
        exception,
    )

    return render_error_page(
        request,
        status_code=503,
        title="История временно недоступна",
        message=(
            "Не удалось получить историю поисковых запросов."
        ),
    )


def save_query_safely(*args) -> None:
    """Сохраняет историю, не прерывая поиск при ошибке MongoDB."""

    try:
        save_query(*args)
    except (ServiceUnavailableError, PyMongoError):
        logger.exception("Не удалось сохранить историю поиска")


def format_genre_history_query(
        genre: str,
        year_from: int,
        year_to: int,
) -> dict[str, str]:
    """Формирует описание поиска по жанру и годам для сохранения в истории.

        Если границы диапазона совпадают, формирует описание одного года.
        В остальных случаях указывает начальный и конечный годы.

        Args:
            genre:
                Название выбранного жанра.
            year_from:
                Начальный год диапазона.
            year_to:
                Конечный год диапазона.

        Returns:
            Словарь с названием жанра и выбранным периодом.
        """

    if year_from == year_to:
        years = str(year_from)
    else:
        years = f"{year_from}-{year_to}"

    return {
        "genre": genre,
        "years": years,
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Отображает главную страницу с параметрами поиска."""

    genre_rows, _ = get_genres()
    min_year, max_year = get_release_year_range()

    genres = [
        {
            "id": genre_id,
            "name": genre_name,
        }
        for genre_id, genre_name in genre_rows
    ]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "genres": genres,
            "min_year": min_year,
            "max_year": max_year,
        },
    )


@app.get("/search", response_class=HTMLResponse)
def search(
    request: Request,
    search_type: str,
    title: str = "",
    genre_id: int | None = Query(default=None, ge=1),
    year_from: str | None = None,
    year_to: str | None = None,
    page: int = Query(default=1, ge=1),
):
    """Выполняет поиск и отображает страницу результатов."""

    if search_type == "name":
        title = title.strip()

        if not title:
            raise HTTPException(
                status_code=400,
                detail="Название фильма не введено.",
            )

        total = count_films_by_name(title)
        offset = (page - 1) * PAGE_SIZE

        rows, headers = get_films_by_name(
            title,
            PAGE_SIZE,
            offset,
        )

        search_description = f"По названию: {title}"

        if page == 1:
            history_query = {
                "keyword": title,
            }
            save_query_safely(
                "by_name",
                history_query,
                total,
            )

    elif search_type == "genre_years":
        if (
                genre_id is None
                or year_from is None
                or year_to is None
        ):
            raise HTTPException(
                status_code=400,
                detail="Жанр и диапазон годов не указаны.",
            )

        year_from = year_from.strip()
        year_to = year_to.strip()

        if not (
                year_from.isdigit()
                and year_to.isdigit()
                and len(year_from) == 4
                and len(year_to) == 4
        ):
            raise HTTPException(
                status_code=400,
                detail="Каждый год должен состоять ровно из четырёх цифр.",
            )

        requested_year_from = int(year_from)
        requested_year_to = int(year_to)

        if requested_year_from > requested_year_to:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Начальный год не должен быть больше конечного."
                ),
            )

        min_year, max_year = get_release_year_range()

        year_from = min(
            max(requested_year_from, min_year),
            max_year,
        )

        year_to = min(
            max(requested_year_to, min_year),
            max_year,
        )

        genre_rows, _ = get_genres()
        genres = dict(genre_rows)
        genre = genres.get(genre_id)

        if genre is None:
            raise HTTPException(
                status_code=400,
                detail="Выбранный жанр отсутствует.",
            )

        total = count_films_by_genre(
            genre_id,
            year_from,
            year_to,
        )

        offset = (page - 1) * PAGE_SIZE

        rows, headers = get_films_by_genre(
            genre_id,
            year_from,
            year_to,
            PAGE_SIZE,
            offset,
        )

        history_query = format_genre_history_query(
            genre,
            year_from,
            year_to,
        )

        search_description = (
            f"Жанр: {history_query['genre']}, "
            f"годы: {history_query['years']}"
        )

        if page == 1:
            save_query_safely(
                "by_genre_years",
                history_query,
                total,
            )

    else:
        raise HTTPException(
            status_code=400,
            detail="Неизвестный вид поиска.",
        )

    total_pages = max(
        1,
        (total + PAGE_SIZE - 1) // PAGE_SIZE,
    )

    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail="Страница результатов не найдена.",
        )

    previous_url = None
    next_url = None

    if page > 1:
        previous_url = request.url.include_query_params(
            page=page - 1
        )

    if page < total_pages:
        next_url = request.url.include_query_params(
            page=page + 1
        )

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={
            "rows": rows,
            "headers": headers,
            "search_description": search_description,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "previous_url": previous_url,
            "next_url": next_url,
        },
    )


@app.get("/popular", response_class=HTMLResponse)
def popular_queries(request: Request):
    """Отображает пять наиболее популярных поисковых запросов."""

    queries = get_top_queries(limit=5)

    popular = [
        {
            "search_type": document["search_type"],
            "query": document["query"],
            "count": document["count"],
        }
        for document in queries
    ]

    return templates.TemplateResponse(
        request=request,
        name="popular_queries.html",
        context={
            "queries": popular,
        },
    )


@app.get("/recent", response_class=HTMLResponse)
def recent_queries(request: Request):
    """Отображает пять последних поисковых запросов."""

    queries = get_last_queries(limit=5)

    recent = [
        {
            "search_type": document["search_type"],
            "query": document["query"],
            "created_at": document["created_at"].strftime(
                "%d.%m.%Y %H:%M:%S"
            ),
        }
        for document in queries
    ]

    return templates.TemplateResponse(
        request=request,
        name="recent_queries.html",
        context={
            "queries": recent,
        },
    )
