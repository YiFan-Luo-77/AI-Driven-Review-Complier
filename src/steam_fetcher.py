"""Steam Store API client for fetching game data."""

import requests
from typing import Any, Dict, List, Optional

STEAM_API_URL = "https://store.steampowered.com/api/appdetails"
STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch"


def search_game(query: str) -> List[Dict[str, Any]]:
    """Search for games by name using the Steam Store search API.

    Args:
        query: Game title or keyword to search for.

    Returns:
        List of matching game items (each has at least 'id' and 'name').
    """
    params = {"term": query, "cc": "us", "l": "en"}
    response = requests.get(STEAM_SEARCH_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("items", [])


def get_game_details(app_id: int) -> Optional[Dict[str, Any]]:
    """Fetch detailed game information from the Steam Store API.

    Args:
        app_id: The Steam application ID.

    Returns:
        Raw game data dict, or None if the request was unsuccessful.
    """
    params = {"appids": app_id, "cc": "us", "l": "en"}
    response = requests.get(STEAM_API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    app_data = data.get(str(app_id), {})
    if not app_data.get("success"):
        return None
    return app_data.get("data")


def extract_game_info(game_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and normalise relevant fields from raw Steam API game data.

    Args:
        game_data: Raw dict returned by :func:`get_game_details`.

    Returns:
        Cleaned and normalised game information dict.
    """
    screenshot_urls = [
        s["path_full"] for s in game_data.get("screenshots", [])[:5]
    ]

    return {
        "name": game_data.get("name", "Unknown"),
        "short_description": game_data.get("short_description", ""),
        "detailed_description": game_data.get("detailed_description", ""),
        "developer": ", ".join(game_data.get("developers", [])),
        "publisher": ", ".join(game_data.get("publishers", [])),
        "genres": [g["description"] for g in game_data.get("genres", [])],
        "categories": [c["description"] for c in game_data.get("categories", [])],
        "release_date": game_data.get("release_date", {}).get("date", "Unknown"),
        "price": game_data.get("price_overview", {}).get("final_formatted", "Free"),
        "metacritic_score": game_data.get("metacritic", {}).get("score"),
        "screenshot_urls": screenshot_urls,
        "header_image": game_data.get("header_image", ""),
        "website": game_data.get("website", ""),
        "platforms": {
            "windows": game_data.get("platforms", {}).get("windows", False),
            "mac": game_data.get("platforms", {}).get("mac", False),
            "linux": game_data.get("platforms", {}).get("linux", False),
        },
    }
