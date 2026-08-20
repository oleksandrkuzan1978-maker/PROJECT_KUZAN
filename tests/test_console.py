"""Тесты консольного поиска по жанру и годам."""

from unittest.mock import ANY, patch

import pytest

from ui.console import get_films_by_genre, handle_genre_search
from ui.input_helpers import input_year_range


def test_input_year_range_preserves_four_digit_values() -> None:
    """Проверка ввода не заменяет годы диапазоном базы данных."""

    with (
        patch(
            "ui.input_helpers.get_release_year_category",
            return_value=(1992, 2025),
        ),
        patch(
            "builtins.input",
            side_effect=("1200", "2000"),
        ),
    ):
        result = input_year_range("Action", 1)

    assert result == (1200, 2000)


def test_genre_search_uses_available_years_and_saves_user_input() -> None:
    """SQL получает годы жанра, а MongoDB — введённые годы."""

    with (
        patch(
            "ui.console.get_genres",
            return_value=(
                [(1, "Action")],
                ["number", "name_genre"],
            ),
        ),
        patch(
            "ui.console.get_release_year_range",
            return_value=(1992, 2025),
        ),
        patch(
            "ui.console.get_release_year_category",
            return_value=(1992, 2025),
        ),
        patch(
            "ui.console.select_genre",
            return_value=(1, "Action"),
        ),
        patch(
            "ui.console.input_year_range",
            return_value=(1200, 2000),
        ),
        patch("ui.console.display_genres"),
        patch(
            "ui.console.count_films_by_genre",
            return_value=1,
        ) as count_mock,
        patch("ui.console.save_query_safely") as save_mock,
        patch(
            "ui.console.show_paginated_results",
            return_value="menu",
        ) as pagination_mock,
    ):
        result = handle_genre_search()

    assert result is None
    count_mock.assert_called_once_with(1, 1992, 2000)
    save_mock.assert_called_once_with(
        "by_genre_years",
        {
            "genre": "Action",
            "years": "1200-2000",
        },
        1,
    )
    pagination_mock.assert_called_once_with(
        get_films_by_genre,
        (1, 1992, 2000),
        total=1,
        title=ANY,
        genre="Action",
    )


@pytest.mark.parametrize(
    ("year_from", "year_to"),
    (
        (1200, 1250),
        (2030, 2200),
    ),
)
def test_genre_search_outside_available_years_returns_no_films(
    year_from: int,
    year_to: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Полностью внешний диапазон не превращается в граничный год."""

    with (
        patch(
            "ui.console.get_genres",
            return_value=([(1, "Action")], ["id", "genre"]),
        ),
        patch(
            "ui.console.get_release_year_range",
            return_value=(1992, 2025),
        ),
        patch(
            "ui.console.get_release_year_category",
            return_value=(1992, 2025),
        ),
        patch(
            "ui.console.select_genre",
            return_value=(1, "Action"),
        ),
        patch(
            "ui.console.input_year_range",
            return_value=(year_from, year_to),
        ),
        patch("ui.console.display_genres"),
        patch("ui.console.count_films_by_genre") as count_mock,
        patch("ui.console.save_query_safely") as save_mock,
        patch("ui.console.show_paginated_results") as pagination_mock,
        patch("ui.console.input_any", return_value="m"),
    ):
        result = handle_genre_search()

    assert result is None
    assert (
        "No films were found matching the specified parameters."
        in capsys.readouterr().out
    )
    count_mock.assert_not_called()
    pagination_mock.assert_not_called()
    save_mock.assert_called_once_with(
        "by_genre_years",
        {
            "genre": "Action",
            "years": f"{year_from}-{year_to}",
        },
        0,
    )
