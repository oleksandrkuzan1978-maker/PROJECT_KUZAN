"""Тесты основных маршрутов FastAPI."""
# Запуск теста: python -m pytest tests/test_web.py -v -W default
import re
from collections.abc import Iterator
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError

from app import app, save_query_safely
from utils.exceptions import ServiceUnavailableError


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Создаёт тестовый клиент без реальных подключений к MongoDB."""

    with (
        patch("app.open_mongo_connections"),
        patch("app.close_mongo_connections"),
        TestClient(app) as test_client,
    ):
        yield test_client


def test_mongo_connections_follow_application_lifespan() -> None:
    """FastAPI открывает и закрывает MongoDB вместе с приложением."""

    with (
        patch("app.open_mongo_connections") as open_mock,
        patch("app.close_mongo_connections") as close_mock,
        TestClient(app),
    ):
        open_mock.assert_called_once_with()
        close_mock.assert_not_called()

    close_mock.assert_called_once_with()


def test_index_displays_genres_and_years(client: TestClient) -> None:
    """Главная страница получает жанры и диапазон годов."""

    with (
        patch(
            "app.get_genres",
            return_value=(
                [(1, "Action"), (2, "Comedy")],
                ["number", "name_genre"],
            ),
        ),
        patch(
            "app.get_release_year_range",
            return_value=(1990, 2026),
        ),
    ):
        response = client.get("/")

    assert response.status_code == 200
    assert "Action" in response.text
    assert "Comedy" in response.text
    assert "1990" in response.text
    assert "2026" in response.text


def test_search_by_name_returns_films(client: TestClient) -> None:
    """Поиск по названию отображает полученные фильмы."""

    rows = [
        (
            "ACADEMY DINOSAUR",
            "A film description",
            2006,
        ),
    ]
    headers = [
        "title",
        "description",
        "release_year",
    ]

    with (
        patch(
            "app.count_films_by_name",
            return_value=1,
        ),
        patch(
            "app.get_films_by_name",
            return_value=(rows, headers),
        ),
        patch("app.save_query_safely") as save_mock,
    ):
        response = client.get(
            "/search",
            params={
                "search_type": "name",
                "title": "academy",
                "page": 1,
            },
        )

    assert response.status_code == 200
    assert "ACADEMY DINOSAUR" in response.text
    assert "Найдено:" in response.text
    save_mock.assert_called_once_with(
        "by_name",
        {"keyword": "academy"},
        1,
    )


def test_genre_search_uses_available_years_and_saves_requested_years(
    client: TestClient,
) -> None:
    """SQL использует доступные годы, а история — введённые."""

    with (
        patch(
            "app.get_release_year_category",
            return_value=(1990, 2026),
        ),
        patch(
            "app.get_genres",
            return_value=(
                [(1, "Action")],
                ["number", "name_genre"],
            ),
        ),
        patch(
            "app.count_films_by_genre",
            return_value=1,
        ) as count_mock,
        patch(
            "app.get_films_by_genre",
            return_value=(
                [("TEST FILM", "Description", 2000, 1)],
                [
                    "title",
                    "description",
                    "release_year",
                    "category_id",
                ],
            ),
        ) as fetch_mock,
        patch("app.save_query_safely") as save_mock,
    ):
        response = client.get(
            "/search",
            params={
                "search_type": "genre_years",
                "genre_id": 1,
                "year_from": "1980",
                "year_to": "2000",
                "page": 1,
            },
        )

    assert response.status_code == 200
    assert 'name="genre_id"' in response.text
    assert 'value="1"' in response.text
    assert 'name="year_from"' in response.text
    assert 'value="1980"' in response.text
    assert 'name="year_to"' in response.text
    assert 'value="2000"' in response.text
    assert "годы: 1980-2000" in response.text

    count_mock.assert_called_once_with(
        1,
        1990,
        2026,
    )

    fetch_mock.assert_called_once_with(
        1,
        1990,
        2026,
        10,
        0,
    )
    save_mock.assert_called_once_with(
        "by_genre_years",
        {
            "genre": "Action",
            "years": "1980-2000",
        },
        1,
    )


def test_reversed_year_range_returns_error(client: TestClient) -> None:
    """Начальный год не может быть больше конечного."""

    response = client.get(
        "/search",
        params={
            "search_type": "genre_years",
            "genre_id": 1,
            "year_from": "2026",
            "year_to": "1990",
        },
    )

    assert response.status_code == 400
    assert "Начальный год" in response.text
    assert "Вернуться к поиску" in response.text
    assert "Вернуться назад" not in response.text


def test_year_must_contain_four_digits(client: TestClient) -> None:
    """Год должен состоять ровно из четырёх цифр."""

    response = client.get(
        "/search",
        params={
            "search_type": "genre_years",
            "genre_id": 1,
            "year_from": "123",
            "year_to": "2026",
        },
    )

    assert response.status_code == 400
    assert "четырёх цифр" in response.text
    assert "Вернуться назад" not in response.text


def test_genre_year_range_returns_selected_genre_years(
    client: TestClient,
) -> None:
    """Веб-форма получает минимальный и максимальный годы жанра."""

    with patch(
        "app.get_release_year_category",
        return_value=(1998, 2006),
    ) as range_mock:
        response = client.get("/genres/3/year-range")

    assert response.status_code == 200
    assert response.json() == {
        "min_year": 1998,
        "max_year": 2006,
    }
    range_mock.assert_called_once_with(3)


def test_genre_without_films_returns_not_found(
    client: TestClient,
) -> None:
    """Пустой жанр не возвращает форме некорректные годы."""

    with patch(
        "app.get_release_year_category",
        return_value=(None, None),
    ):
        response = client.get("/genres/99/year-range")

    assert response.status_code == 404
    assert "Вернуться к поиску" in response.text
    assert "Вернуться назад" not in response.text

def test_second_page_uses_correct_offset(client: TestClient) -> None:
    """Вторая страница использует LIMIT 10 и OFFSET 10."""

    with (
        patch(
            "app.count_films_by_name",
            return_value=25,
        ),
        patch(
            "app.get_films_by_name",
            return_value=(
                [("SECOND PAGE FILM", "Description", 2006)],
                ["title", "description", "release_year"],
            ),
        ) as fetch_mock,
        patch("app.save_query_safely") as save_mock,
    ):
        response = client.get(
            "/search",
            params={
                "search_type": "name",
                "title": "film",
                "page": 2,
            },
        )

    assert response.status_code == 200
    assert "SECOND PAGE FILM" in response.text
    assert "Страница 2 из 3" in response.text

    fetch_mock.assert_called_once_with(
        "film",
        10,
        10,
    )

    save_mock.assert_not_called()


def test_results_include_page_number_form(client: TestClient) -> None:
    """Форма перехода сохраняет параметры поиска по названию."""

    with (
        patch("app.count_films_by_name", return_value=25),
        patch(
            "app.get_films_by_name",
            return_value=(
                [("ACADEMY", "Description", 2006)],
                ["title", "description", "release_year"],
            ),
        ),
        patch("app.save_query_safely"),
    ):
        response = client.get(
            "/search",
            params={
                "search_type": "name",
                "title": "academy",
            },
        )

    assert response.status_code == 200
    assert 'name="page"' in response.text
    assert 'max="3"' in response.text
    assert 'name="search_type"' in response.text
    assert 'value="name"' in response.text
    assert 'name="title"' in response.text
    assert 'value="academy"' in response.text
    assert "Перейти к странице" in response.text


def test_search_without_results_is_saved_on_first_page(
    client: TestClient,
) -> None:
    """Поиск без результатов также сохраняется в истории."""

    with (
        patch("app.count_films_by_name", return_value=0),
        patch(
            "app.get_films_by_name",
            return_value=([], ["title", "description", "release_year"]),
        ),
        patch("app.save_query_safely") as save_mock,
    ):
        response = client.get(
            "/search",
            params={
                "search_type": "name",
                "title": "missing",
                "page": 1,
            },
        )

    assert response.status_code == 200
    assert "фильмы не найдены" in response.text
    save_mock.assert_called_once_with(
        "by_name",
        {"keyword": "missing"},
        0,
    )


def test_popular_queries_page(client: TestClient) -> None:
    """Страница популярных запросов отображает данные MongoDB."""

    documents = [
        {
            "search_type": "by_name",
            "query": {"keyword": "academy"},
            "count": 7,
        },
        {
            "search_type": "by_genre_years",
            "query": {
                "genre": "Action",
                "years": "2000-2006",
            },
            "count": 3,
        },
    ]

    with patch(
        "app.get_top_queries",
        return_value=documents,
    ):
        response = client.get("/popular")

    assert response.status_code == 200
    assert "academy" in response.text
    assert "Action" in response.text
    assert re.search(
        r">\s*7\s*<",
        response.text,
    ) is not None


def test_recent_queries_page(client: TestClient) -> None:
    """Страница последних запросов форматирует дату выполнения."""

    documents = [
        {
            "search_type": "by_name",
            "query": {"keyword": "academy"},
            "created_at": datetime(
                2026,
                8,
                2,
                14,
                30,
                15,
            ),
        },
    ]

    with patch(
        "app.get_last_queries",
        return_value=documents,
    ):
        response = client.get("/recent")

    assert response.status_code == 200
    assert "academy" in response.text
    assert "02.08.2026 14:30:15" in response.text


def test_unknown_search_type_fails_validation(client: TestClient) -> None:
    """FastAPI отклоняет вид поиска, отсутствующий в форме."""

    response = client.get(
        "/search",
        params={"search_type": "unknown"},
    )

    assert response.status_code == 422
    assert "Некорректные параметры" in response.text


def test_missing_result_page_returns_not_found(
    client: TestClient,
) -> None:
    """Страница за пределами результата возвращает HTTP 404."""

    with (
        patch("app.count_films_by_name", return_value=1),
        patch(
            "app.get_films_by_name",
            return_value=([], ["title", "description", "release_year"]),
        ),
        patch("app.save_query_safely") as save_mock,
    ):
        response = client.get(
            "/search",
            params={
                "search_type": "name",
                "title": "academy",
                "page": 2,
            },
        )

    assert response.status_code == 404
    assert "Вернуться к поиску" in response.text
    assert "Вернуться назад" not in response.text
    save_mock.assert_not_called()


def test_service_unavailable_returns_503(client: TestClient) -> None:
    """Недоступность MySQL отображается как HTTP 503."""

    with patch(
        "app.get_genres",
        side_effect=ServiceUnavailableError("MySQL"),
    ):
        response = client.get("/")

    assert response.status_code == 503
    assert "MySQL" in response.text


def test_mongodb_read_error_returns_503(client: TestClient) -> None:
    """Ошибка чтения MongoDB отображается как HTTP 503."""

    with patch(
        "app.get_top_queries",
        side_effect=PyMongoError("MongoDB error"),
    ):
        response = client.get("/popular")

    assert response.status_code == 503
    assert "История временно недоступна" in response.text


def test_history_write_error_does_not_interrupt_search() -> None:
    """Ошибка MongoDB при записи истории подавляется веб-обёрткой."""

    with patch(
        "app.save_query",
        side_effect=ServiceUnavailableError("MongoDB"),
    ):
        result = save_query_safely(
            "by_name",
            {"keyword": "academy"},
            1,
        )

    assert result is None
