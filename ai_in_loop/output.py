"""Output formatting for paper analysis results.

This module provides functions to format PaperState results as JSON or
Markdown for CLI output.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .state import PaperState


def format_json(state: "PaperState") -> str:
    """Format paper analysis results as JSON.

    Produces the output structure specified in the assignment:
    {
        "query_url": "...",
        "citation": { "title": "...", "authors": [...], "venue": "...", "year": 2017 },
        "links": { "query": "...", "doi": "...", "arxiv": "...", "full_text": "..." },
        "abstract": "...",
        "summary": "...",
        "warnings": []
    }

    Args:
        state: Final workflow state

    Returns:
        JSON string
    """
    metadata = state.get("metadata") or {}

    output: dict[str, Any] = {
        "query_url": state.get("query_url"),
        "citation": {
            "title": metadata.get("title"),
            "authors": metadata.get("authors", []),
            "venue": metadata.get("venue"),
            "year": metadata.get("year"),
        },
        "links": {
            "query": state.get("query_url"),
            "doi": state.get("doi_link"),
            "arxiv": state.get("arxiv_link"),
            "full_text": state.get("full_text_url"),
        },
        "abstract": metadata.get("abstract"),
        "summary": state.get("summary"),
        "warnings": state.get("warnings", []),
    }

    return json.dumps(output, indent=2, ensure_ascii=False)


def format_markdown(state: "PaperState") -> str:
    """Format paper analysis results as Markdown.

    Produces human-readable output with sections for citation, abstract,
    summary, and links.

    Args:
        state: Final workflow state

    Returns:
        Markdown string
    """
    metadata = state.get("metadata") or {}
    lines: list[str] = []

    # Title
    title = metadata.get("title", "Unknown Title")
    lines.append(f"# {title}")
    lines.append("")

    # Citation info
    authors = metadata.get("authors", [])
    if authors:
        authors_str = ", ".join(authors)
        lines.append(f"**Authors:** {authors_str}")

    venue = metadata.get("venue")
    year = metadata.get("year")
    if venue or year:
        venue_str = venue or "Unknown venue"
        year_str = str(year) if year else "Unknown year"
        lines.append(f"**Published:** {venue_str}, {year_str}")

    lines.append("")

    # Links
    lines.append("## Links")
    arxiv_link = state.get("arxiv_link")
    doi_link = state.get("doi_link")
    full_text_url = state.get("full_text_url")

    if arxiv_link:
        lines.append(f"- arXiv: {arxiv_link}")
    if doi_link:
        lines.append(f"- DOI: {doi_link}")
    if full_text_url:
        lines.append(f"- Full text: {full_text_url}")

    lines.append("")

    # Abstract
    abstract = metadata.get("abstract")
    if abstract:
        lines.append("## Abstract")
        lines.append("")
        lines.append(abstract)
        lines.append("")

    # Summary
    summary = state.get("summary")
    if summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")

    # Warnings
    warnings = state.get("warnings", [])
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    return "\n".join(lines)


def format_output(state: "PaperState", fmt: str = "json") -> str:
    """Format paper analysis results in the specified format.

    Args:
        state: Final workflow state
        fmt: Output format ("json" or "markdown")

    Returns:
        Formatted string

    Raises:
        ValueError: If format is not recognized
    """
    if fmt == "json":
        return format_json(state)
    elif fmt == "markdown":
        return format_markdown(state)
    else:
        raise ValueError(f"Unknown output format: {fmt}")
