"""State schema for the paper analyzer workflow.

This module defines the PaperState TypedDict that flows through the LangGraph
workflow. Each node reads from and writes to fields in this state.
"""

from typing import List, TypedDict


class GameState(TypedDict, total=False):
    """State object that flows through the paper analyzer workflow.

    The workflow processes academic papers from arXiv URLs or DOIs,
    fetching metadata and optionally generating summaries when full text
    is available.

    Fields are organized into logical groups:
    - Input: What the user provided
    - Identifiers: Normalized paper identifiers
    - Metadata: Bibliographic information
    - Full text: Content for summarization
    - Links: URLs to paper resources
    - Output: Generated content and status
    """

    # === Input ===
    game_url: str  # Original game URL provided by the user
    identifier: str | None # game id

    # === Steam Data ===
    game_title: str | None
    developer: str | None
    publisher: str | None
    release_date: str | None
    official_description: str | None
    steam_rating: str | None
    hardware_requirement: str | None
    official_image: List[str] | None
    official_gif: List[str] | None

    # === User Input ===
    user_exp: str | None
    review_rating: str | None
    user_images: List[str] | None
    user_birthdate: tuple[int, str, int] | None  # (day, month, year)

    # === Output ===
    review: str | None  # LLM-generated review based on all available data
    merged_context: str | None  # Combined context from official data and user input for review generation

    # === Warnings ===
    warnings: List[str]
