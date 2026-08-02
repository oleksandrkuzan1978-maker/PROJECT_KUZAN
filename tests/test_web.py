"""Тесты основных маршрутов FastAPI."""
# Запуск теста: python -m pytest tests/test_web.py -v -W default
import re
from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_index_displays_genres_and_years() -> None:
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


def test_search_by_name_returns_films() -> None:
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
        patch("app.save_query_safely"),
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


def test_genre_years_are_limited_to_database_range() -> None:
    """Внешние годы автоматически ограничиваются диапазоном БД."""

    with (
        patch(
            "app.get_release_year_range",
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
        patch("app.save_query_safely"),
    ):
        response = client.get(
            "/search",
            params={
                "search_type": "genre_years",
                "genre_id": 1,
                "year_from": "1234",
                "year_to": "2345",
                "page": 1,
            },
        )

    assert response.status_code == 200

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


def test_reversed_year_range_returns_error() -> None:
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


def test_year_must_contain_four_digits() -> None:
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

def test_second_page_uses_correct_offset() -> None:
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


def test_popular_queries_page() -> None:
    """Страница популярных запросов отображает данные MongoDB."""

    documents = [
        {
            "_id": {
                "search_type": "by_name",
                "query": "academy",
            },
            "count": 7,
        },
        {
            "_id": {
                "search_type": "by_genre_years",
                "query": "Genre: Action, years: 2000-2006",
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


def test_recent_queries_page() -> None:
    """Страница последних запросов форматирует дату выполнения."""

    documents = [
        {
            "search_type": "by_name",
            "query": "academy",
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