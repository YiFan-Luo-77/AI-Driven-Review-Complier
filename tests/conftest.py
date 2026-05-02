"""Pytest configuration and fixtures for paper analyzer tests.

This module provides:
- Fixtures for loading mock API responses from JSON files
- Fixtures for mocking HTTP requests to academic APIs
- Configuration fixtures for testing with MockChatModel
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# Path to fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "papers"


def load_fixture(name: str) -> dict[str, Any]:
    """Load a fixture JSON file by name.

    Args:
        name: Fixture name (without .json extension)

    Returns:
        Parsed JSON data
    """
    fixture_path = FIXTURES_DIR / f"{name}.json"
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    return json.loads(fixture_path.read_text())


@pytest.fixture
def attention_fixture() -> dict[str, Any]:
    """Load the 'Attention Is All You Need' paper fixture."""
    return load_fixture("attention")


@pytest.fixture
def arxiv_only_fixture() -> dict[str, Any]:
    """Load the arXiv-only paper fixture (no published DOI)."""
    return load_fixture("arxiv_only")


@pytest.fixture
def paywalled_fixture() -> dict[str, Any]:
    """Load the paywalled paper fixture (no open access)."""
    return load_fixture("paywalled")


@pytest.fixture
def mock_semantic_scholar(attention_fixture):
    """Mock Semantic Scholar API responses.

    Returns a function that can be used to set up mocking for specific papers.
    """
    def _create_mock_response(paper_id: str, fixture: dict[str, Any]):
        """Create a mock response object for requests.get."""
        ss_data = fixture.get("semantic_scholar")
        if ss_data:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = ss_data
            return response
        else:
            response = MagicMock()
            response.status_code = 404
            return response

    return _create_mock_response


@pytest.fixture
def mock_arxiv_api(attention_fixture):
    """Mock arXiv API responses.

    Returns a function that creates mock XML responses.
    """
    def _create_mock_response(arxiv_id: str, fixture: dict[str, Any]):
        """Create a mock response object for arXiv API."""
        arxiv_data = fixture.get("arxiv")
        if arxiv_data:
            # Create minimal XML response
            xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>{arxiv_data['title']}</title>
    <summary>{arxiv_data['abstract']}</summary>
    <published>{arxiv_data['year']}-01-01T00:00:00Z</published>
    {''.join(f'<author><name>{a}</name></author>' for a in arxiv_data['authors'])}
    <link title="pdf" href="{arxiv_data.get('pdf_link', '')}"/>
  </entry>
</feed>"""
            response = MagicMock()
            response.status_code = 200
            response.content = xml_content.encode()
            return response
        else:
            response = MagicMock()
            response.status_code = 404
            return response

    return _create_mock_response


@pytest.fixture
def mock_unpaywall(attention_fixture):
    """Mock Unpaywall API responses."""
    def _create_mock_response(doi: str, fixture: dict[str, Any]):
        """Create a mock response object for Unpaywall API."""
        unpaywall_data = fixture.get("unpaywall")
        if unpaywall_data:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = unpaywall_data
            return response
        else:
            response = MagicMock()
            response.status_code = 404
            return response

    return _create_mock_response


@pytest.fixture
def mock_pdf_extraction():
    """Mock PDF extraction to return sample text."""
    sample_text = """
    Abstract

    This paper presents a novel approach to the problem at hand.
    We demonstrate significant improvements over prior work.

    1. Introduction

    The field has seen rapid progress in recent years.
    However, several challenges remain unsolved.

    2. Methods

    Our approach builds upon established techniques.
    We introduce several key innovations.

    3. Results

    Experimental results demonstrate the effectiveness of our method.
    We achieve state-of-the-art performance on multiple benchmarks.

    4. Conclusion

    This work contributes to the field by presenting a new approach.
    Future work will explore additional applications.
    """
    return sample_text.strip()


@pytest.fixture
def mock_all_apis(attention_fixture, mock_pdf_extraction):
    """Mock all external API calls with the attention fixture.

    This fixture patches API functions at the node level to return mock data,
    allowing tests to run without network access.
    """
    ss_data = attention_fixture.get("semantic_scholar")
    arxiv_data = attention_fixture.get("arxiv")
    crossref_data = attention_fixture.get("crossref")
    unpaywall_data = attention_fixture.get("unpaywall")

    # Convert unpaywall fixture to normalized format expected by find_full_text
    unpaywall_normalized = None
    if unpaywall_data and unpaywall_data.get("best_oa_location"):
        loc = unpaywall_data["best_oa_location"]
        unpaywall_normalized = {
            "is_oa": unpaywall_data.get("is_oa", False),
            "oa_url": loc.get("url_for_pdf") or loc.get("url"),
            "oa_version": loc.get("version"),
            "license": loc.get("license"),
        }

    with patch("ai_in_loop.nodes.fetch_semantic_scholar", return_value=ss_data):
        with patch("ai_in_loop.nodes.fetch_arxiv", return_value=arxiv_data):
            with patch("ai_in_loop.nodes.fetch_crossref", return_value=crossref_data):
                with patch("ai_in_loop.nodes.fetch_unpaywall", return_value=unpaywall_normalized):
                    with patch("ai_in_loop.tools.extract_pdf_text", return_value=mock_pdf_extraction):
                        yield


@pytest.fixture
def test_config():
    """Create a test configuration with mock LLM."""
    from ai_in_loop.config import Config

    return Config(
        use_gemini=False,  # Use MockChatModel
        gemini_api_key=None,
        gemini_model="gemini-2.5-flash",
        temperature=0.7,
        thinking_level=None,
        thinking_budget=0,
        api_email="test@example.edu",
    )
