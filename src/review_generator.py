"""AI-powered game review generator using OpenAI's chat completion API."""

import os
from typing import Any, Dict, Optional

from openai import OpenAI

_SYSTEM_PROMPT = (
    "You are an expert video game journalist writing detailed, engaging, and balanced "
    "game reviews. Your reviews should cover gameplay, story, visuals, audio, and "
    "overall value. Write in a professional yet approachable style."
)

_REVIEW_STRUCTURE = """
Structure the review with the following sections:
1. Overview
2. Gameplay
3. Story & Setting
4. Visuals & Audio
5. Value & Verdict

End with a numerical score out of 10 and a brief recommendation.
"""


def _build_prompt(game_info: Dict[str, Any], user_experience: Optional[str]) -> str:
    genres = ", ".join(game_info.get("genres", []))
    available_platforms = ", ".join(
        p for p, available in game_info.get("platforms", {}).items() if available
    )

    lines = [
        f"Please write a comprehensive game review for:",
        f"",
        f"**Game:** {game_info.get('name', 'Unknown')}",
        f"**Developer:** {game_info.get('developer', 'Unknown')}",
        f"**Publisher:** {game_info.get('publisher', 'Unknown')}",
        f"**Genre:** {genres}",
        f"**Release Date:** {game_info.get('release_date', 'Unknown')}",
        f"**Price:** {game_info.get('price', 'Unknown')}",
        f"**Platforms:** {available_platforms}",
        f"",
        f"**Game Description:**",
        game_info.get("short_description", ""),
    ]

    if game_info.get("metacritic_score") is not None:
        lines.append(f"**Metacritic Score:** {game_info['metacritic_score']}")

    if user_experience:
        lines += [
            "",
            "**Player's Personal Experience:**",
            user_experience,
            "",
            "Please incorporate the player's personal experience into the review "
            "where appropriate.",
        ]

    lines.append(_REVIEW_STRUCTURE)
    return "\n".join(lines)


def generate_review(
    game_info: Dict[str, Any],
    user_experience: Optional[str] = None,
    client: Optional[OpenAI] = None,
) -> str:
    """Generate an AI-driven game review.

    Args:
        game_info: Normalised game information dict (from :func:`steam_fetcher.extract_game_info`).
        user_experience: Optional personal gaming experience provided by the user.
        client: OpenAI client instance. If *None*, one is created from the
            ``OPENAI_API_KEY`` environment variable.

    Returns:
        Generated review text as a string.
    """
    if client is None:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    prompt = _build_prompt(game_info, user_experience)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1500,
        temperature=0.7,
    )

    return response.choices[0].message.content
