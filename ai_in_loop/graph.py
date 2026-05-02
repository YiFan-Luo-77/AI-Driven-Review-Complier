"""LangGraph workflow for paper analysis.

This module defines the graph structure for the paper analyzer workflow.

Full Workflow:
    START -> parse_input -> fetch_metadata_apis -> find_full_text
          -> [route_by_fulltext]
               -> fetch_full_text (has full_text_url)
                    -> [route_by_metadata]
                         -> summarize (has metadata) -> END
                         -> llm_extract_metadata (no metadata) -> summarize -> END
               -> format_citation_only (no full text, has metadata) -> END
               -> partial_result_warning (no full text, no metadata) -> END
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .config import Config
from .llm import get_llm
from .nodes import (
    set_llm,
    parse_input,
    fetch_game_info,
    route_user_input,
    merge_exp,
    merge_image,
    merge_both,
    prepare_official,

    summarize,
)
from .state import GameState

if TYPE_CHECKING:
    pass


def build_graph(cfg: Config) -> CompiledStateGraph:
    """Build and compile the game review workflow graph."""

    llm = get_llm(cfg)
    set_llm(llm)

    graph = StateGraph(GameState)

    # Nodes
    graph.add_node("parse_input", parse_input)
    graph.add_node("fetch_game_info", fetch_game_info)

    graph.add_node("prepare_official", prepare_official)
    graph.add_node("merge_exp", merge_exp)
    graph.add_node("merge_image", merge_image)
    graph.add_node("merge_both", merge_both)

    graph.add_node("summarize", summarize)

    # Linear edges at the start
    graph.add_edge(START, "parse_input")
    graph.add_edge("parse_input", "fetch_game_info")

    graph.add_conditional_edges(
        "fetch_game_info",
        route_user_input,
        {
            "no_input": "prepare_official",
            "exp_only": "merge_exp",
            "image_only": "merge_image",
            "both": "merge_both",
        },
    )
    graph.add_edge("prepare_official", "summarize")
    graph.add_edge("merge_exp", "summarize")
    graph.add_edge("merge_image", "summarize")
    graph.add_edge("merge_both", "summarize")
    return graph.compile()

def analyze_game(url: str, cfg: Config) -> GameState:
    """Analyze a game from a Steam URL."""

    graph = build_graph(cfg)

    initial_state: GameState = {
        "game_url": url,
        "identifier": None,

        # Steam data
        "game_title": None,
        "developer": None,
        "publisher": None,
        "release_date": None,
        "official_description": None,
        "steam_rating": None,
        "hardware_requirement": None,

        # User input
        "user_exp": None,
        "review_rating": None,
        "user_images": None,

        # Merge
        "merged_context": None,

        # Output
        "review": None,

        # Warnings
        "warnings": [],
    }

    result = graph.invoke(initial_state)
    return result