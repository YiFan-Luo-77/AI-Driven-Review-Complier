"""Tests for src/steam_fetcher.py."""

from unittest.mock import MagicMock, patch

import pytest

from src.steam_fetcher import extract_game_info, get_game_details, search_game


# ---------------------------------------------------------------------------
# extract_game_info
# ---------------------------------------------------------------------------

FULL_RAW_DATA = {
    "name": "Hollow Knight",
    "short_description": "A challenging underground adventure.",
    "detailed_description": "<p>Very detailed description.</p>",
    "developers": ["Team Cherry"],
    "publishers": ["Team Cherry"],
    "genres": [{"description": "Action"}, {"description": "Indie"}],
    "categories": [{"description": "Single-player"}, {"description": "Steam Achievements"}],
    "release_date": {"date": "24 Feb, 2017"},
    "price_overview": {"final_formatted": "$14.99"},
    "metacritic": {"score": 87},
    "screenshots": [
        {"path_full": "https://cdn.steam.example.com/shot1.jpg"},
        {"path_full": "https://cdn.steam.example.com/shot2.jpg"},
        {"path_full": "https://cdn.steam.example.com/shot3.jpg"},
    ],
    "header_image": "https://cdn.steam.example.com/header.jpg",
    "website": "https://www.hollowknight.com",
    "platforms": {"windows": True, "mac": True, "linux": True},
}


def test_extract_game_info_full_data():
    info = extract_game_info(FULL_RAW_DATA)

    assert info["name"] == "Hollow Knight"
    assert info["short_description"] == "A challenging underground adventure."
    assert info["developer"] == "Team Cherry"
    assert info["publisher"] == "Team Cherry"
    assert info["genres"] == ["Action", "Indie"]
    assert info["categories"] == ["Single-player", "Steam Achievements"]
    assert info["release_date"] == "24 Feb, 2017"
    assert info["price"] == "$14.99"
    assert info["metacritic_score"] == 87
    assert len(info["screenshot_urls"]) == 3
    assert info["header_image"] == "https://cdn.steam.example.com/header.jpg"
    assert info["platforms"] == {"windows": True, "mac": True, "linux": True}


def test_extract_game_info_minimal_data():
    """Should return safe defaults for a near-empty raw dict."""
    info = extract_game_info({"name": "Minimal Game"})

    assert info["name"] == "Minimal Game"
    assert info["developer"] == ""
    assert info["publisher"] == ""
    assert info["genres"] == []
    assert info["categories"] == []
    assert info["release_date"] == "Unknown"
    assert info["price"] == "Free"
    assert info["metacritic_score"] is None
    assert info["screenshot_urls"] == []
    assert info["header_image"] == ""
    assert info["platforms"] == {"windows": False, "mac": False, "linux": False}


def test_extract_game_info_caps_screenshots_at_five():
    raw = {
        "screenshots": [{"path_full": f"https://example.com/shot{i}.jpg"} for i in range(10)]
    }
    info = extract_game_info(raw)
    assert len(info["screenshot_urls"]) == 5


def test_extract_game_info_multiple_developers():
    raw = {"developers": ["Studio A", "Studio B"], "publishers": ["Pub X"]}
    info = extract_game_info(raw)
    assert info["developer"] == "Studio A, Studio B"
    assert info["publisher"] == "Pub X"


# ---------------------------------------------------------------------------
# search_game
# ---------------------------------------------------------------------------

@patch("src.steam_fetcher.requests.get")
def test_search_game_returns_items(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {"id": 367520, "name": "Hollow Knight"},
            {"id": 1158310, "name": "Hollow Knight: Silksong"},
        ]
    }
    mock_get.return_value = mock_response

    results = search_game("Hollow Knight")
    assert len(results) == 2
    assert results[0]["name"] == "Hollow Knight"
    assert results[0]["id"] == 367520


@patch("src.steam_fetcher.requests.get")
def test_search_game_empty_result(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}
    mock_get.return_value = mock_response

    results = search_game("xyznonexistent")
    assert results == []


# ---------------------------------------------------------------------------
# get_game_details
# ---------------------------------------------------------------------------

@patch("src.steam_fetcher.requests.get")
def test_get_game_details_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "367520": {
            "success": True,
            "data": {"name": "Hollow Knight", "steam_appid": 367520},
        }
    }
    mock_get.return_value = mock_response

    data = get_game_details(367520)
    assert data is not None
    assert data["name"] == "Hollow Knight"


@patch("src.steam_fetcher.requests.get")
def test_get_game_details_failure(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"999999": {"success": False}}
    mock_get.return_value = mock_response

    data = get_game_details(999999)
    assert data is None
