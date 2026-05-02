"""Tests for the full paper analyzer code (after student extensions).

These tests verify that Activity 1 extensions are correctly implemented:
- DOI input parsing
- input_type field in state
- full_text_url field in state
- find_full_text node
- route_by_fulltext routing function
- format_citation_only and partial_result_warning nodes
- --output CLI flag

These tests will FAIL on the starter code and PASS after completing Activity 1.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Literal
from unittest.mock import patch, MagicMock

import pytest

from ai_in_loop.tools import extract_doi
from ai_in_loop.nodes import (
    parse_input,
    find_full_text,
    route_by_fulltext,
    format_citation_only,
    partial_result_warning,
)
from ai_in_loop.state import PaperState


class TestDOIInputParsing:
    """Tests for DOI input support (Activity 1)."""

    def test_parse_doi_url(self):
        """Parse DOI URL correctly and set input_type."""
        state: PaperState = {
            "query_url": "https://doi.org/10.1038/nature12373",
            "warnings": [],
        }
        result = parse_input(state)

        # After Activity 1, these should work:
        assert result.get("input_type") == "doi", "input_type should be 'doi' for DOI URLs"
        assert result["identifier"] == "10.1038/nature12373"
        assert result["doi_link"] == "https://doi.org/10.1038/nature12373"

    def test_parse_bare_doi(self):
        """Parse bare DOI correctly."""
        state: PaperState = {
            "query_url": "10.1038/nature12373",
            "warnings": [],
        }
        result = parse_input(state)

        assert result.get("input_type") == "doi", "input_type should be 'doi' for bare DOIs"
        assert result["identifier"] == "10.1038/nature12373"

    def test_parse_arxiv_sets_input_type(self):
        """Parse arXiv URL sets input_type to 'arxiv'."""
        state: PaperState = {
            "query_url": "https://arxiv.org/abs/1706.03762",
            "warnings": [],
        }
        result = parse_input(state)

        assert result.get("input_type") == "arxiv", "input_type should be 'arxiv' for arXiv URLs"


class TestStateFields:
    """Tests for required state fields (Activity 1)."""

    def test_input_type_field_exists(self):
        """PaperState should have input_type field."""
        # This tests that the field is defined in the TypedDict
        # The typing system will catch this if missing
        state: PaperState = {
            "query_url": "test",
            "input_type": "arxiv",  # This should be valid
            "warnings": [],
        }
        assert state["input_type"] == "arxiv"

    def test_full_text_url_field_exists(self):
        """PaperState should have full_text_url field."""
        state: PaperState = {
            "query_url": "test",
            "full_text_url": "https://example.com/paper.pdf",  # This should be valid
            "warnings": [],
        }
        assert state["full_text_url"] == "https://example.com/paper.pdf"


class TestFindFullTextNode:
    """Tests for the find_full_text node (Activity 1)."""

    def test_find_full_text_with_unpaywall(self, attention_fixture):
        """find_full_text should set full_text_url from Unpaywall."""
        # Mock fetch_unpaywall to return OA URL
        unpaywall_result = {
            "is_oa": True,
            "oa_url": "https://arxiv.org/pdf/1706.03762.pdf",
            "oa_version": "submittedVersion",
            "license": None,
        }

        state: PaperState = {
            "query_url": "https://arxiv.org/abs/1706.03762",
            "doi_link": "https://doi.org/10.48550/arXiv.1706.03762",
            "arxiv_link": "https://arxiv.org/abs/1706.03762",
            "identifier": "1706.03762",
            "warnings": [],
        }

        with patch("ai_in_loop.nodes.fetch_unpaywall", return_value=unpaywall_result):
            result = find_full_text(state)

        # After Activity 1, full_text_url should be set
        assert result.get("full_text_url") is not None, "find_full_text should set full_text_url"
        assert result.get("full_text_url") == "https://arxiv.org/pdf/1706.03762.pdf"

    def test_find_full_text_fallback_to_arxiv(self):
        """find_full_text should fall back to arXiv PDF when no Unpaywall result."""
        # Mock fetch_unpaywall returning no OA URL
        unpaywall_result = {
            "is_oa": False,
            "oa_url": None,
            "oa_version": None,
            "license": None,
        }

        state: PaperState = {
            "query_url": "https://arxiv.org/abs/1706.03762",
            "input_type": "arxiv",
            "doi_link": None,
            "arxiv_link": "https://arxiv.org/abs/1706.03762",
            "identifier": "1706.03762",
            "warnings": [],
        }

        with patch("ai_in_loop.nodes.fetch_unpaywall", return_value=unpaywall_result):
            result = find_full_text(state)

        # Should fall back to arXiv PDF URL
        expected_url = "https://arxiv.org/pdf/1706.03762.pdf"
        assert result.get("full_text_url") == expected_url, \
            "find_full_text should fall back to arXiv PDF URL"


class TestRouteByFulltext:
    """Tests for the route_by_fulltext routing function (Activity 1)."""

    def test_route_by_fulltext_signature(self):
        """route_by_fulltext should return correct Literal type."""
        # Test that the function exists and returns the right type
        state_with_url: PaperState = {
            "query_url": "test",
            "full_text_url": "https://example.com/paper.pdf",
            "warnings": [],
        }
        result = route_by_fulltext(state_with_url)

        # Should return one of the valid literals
        valid_routes = ("fetch_full_text", "format_citation_only", "partial_result_warning")
        assert result in valid_routes, \
            f"route_by_fulltext should return valid Literal value, got {result}"

    def test_route_by_fulltext_with_url(self):
        """route_by_fulltext should route to fetch_full_text when URL exists."""
        state: PaperState = {
            "query_url": "test",
            "full_text_url": "https://example.com/paper.pdf",
            "warnings": [],
        }
        result = route_by_fulltext(state)

        assert result == "fetch_full_text", \
            "Should route to fetch_full_text when full_text_url exists"

    def test_route_by_fulltext_without_url_has_metadata(self):
        """route_by_fulltext should route to format_citation_only when no URL but has metadata."""
        state: PaperState = {
            "query_url": "test",
            "full_text_url": None,
            "metadata": {"title": "Test Paper"},
            "warnings": [],
        }
        result = route_by_fulltext(state)

        assert result == "format_citation_only", \
            "Should route to format_citation_only when no full_text_url but has metadata"

    def test_route_by_fulltext_without_url_no_metadata(self):
        """route_by_fulltext should route to partial_result_warning when no URL and no metadata."""
        state: PaperState = {
            "query_url": "test",
            "full_text_url": None,
            "metadata": None,
            "warnings": [],
        }
        result = route_by_fulltext(state)

        assert result == "partial_result_warning", \
            "Should route to partial_result_warning when no full_text_url and no metadata"


class TestBranchNodes:
    """Tests for the branch nodes (Activity 1)."""

    def test_format_citation_only(self):
        """format_citation_only should set appropriate summary message."""
        state: PaperState = {
            "query_url": "test",
            "metadata": {"title": "Test Paper"},
            "warnings": [],
        }
        result = format_citation_only(state)

        assert result["summary"] is not None, \
            "format_citation_only should set summary"
        assert "citation" in result["summary"].lower() or "full text" in result["summary"].lower(), \
            "Summary should mention citation or full text unavailability"

    def test_partial_result_warning(self):
        """partial_result_warning should add warning about incomplete results."""
        state: PaperState = {
            "query_url": "test",
            "metadata": None,
            "warnings": [],
        }
        result = partial_result_warning(state)

        assert len(result["warnings"]) > 0, \
            "partial_result_warning should add a warning"


class TestCLIOutputFlag:
    """Tests for --output CLI flag (Activity 1)."""

    def test_output_flag_exists(self):
        """CLI should have --output/-o flag."""
        from typer.testing import CliRunner
        from ai_in_loop.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["analyze", "--help"])

        # Check that --output is documented
        assert "--output" in result.output or "-o" in result.output, \
            "CLI should have --output flag"

    def test_output_flag_writes_file(self, mock_all_apis):
        """--output flag should write output to file."""
        from typer.testing import CliRunner
        from ai_in_loop.cli import app

        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(app, [
                "analyze",
                "https://arxiv.org/abs/1706.03762",
                "--format", "json",
                "--output", output_path,
            ])

            # Command should succeed
            assert result.exit_code == 0, f"Command failed: {result.output}"

            # File should exist and contain JSON
            output_file = Path(output_path)
            assert output_file.exists(), "Output file should be created"

            content = output_file.read_text()
            data = json.loads(content)
            assert "query_url" in data, "Output should be valid JSON with expected fields"

        finally:
            # Clean up
            Path(output_path).unlink(missing_ok=True)


class TestGraphConditionalEdges:
    """Tests for graph structure with conditional edges (Activity 1)."""

    def test_graph_has_find_full_text_node(self, test_config):
        """Graph should have find_full_text node."""
        from ai_in_loop.graph import build_graph

        graph = build_graph(test_config)

        # Get the graph structure
        graph_dict = graph.get_graph()

        # Check for the node - nodes may be strings or objects depending on LangGraph version
        node_names = list(graph_dict.nodes)
        assert "find_full_text" in node_names, \
            "Graph should have find_full_text node"

    def test_graph_has_fulltext_conditional_edge(self, test_config):
        """Graph should have conditional edge from find_full_text."""
        from ai_in_loop.graph import build_graph

        graph = build_graph(test_config)
        graph_dict = graph.get_graph()

        # Check that find_full_text has outgoing edges to both branches
        # Edges may be tuples (source, target) or objects with .source/.target
        destinations = set()
        for edge in graph_dict.edges:
            if hasattr(edge, 'source'):
                if edge.source == "find_full_text":
                    destinations.add(edge.target)
            elif isinstance(edge, tuple) and len(edge) >= 2:
                if edge[0] == "find_full_text":
                    destinations.add(edge[1])

        # Should have conditional edges (at least 2 destinations)
        assert len(destinations) >= 2, \
            "find_full_text should have conditional edges to multiple destinations"


class TestWorkflowWithDOI:
    """Tests for workflow execution with DOI input (Activity 1)."""

    def test_workflow_with_doi_input(self, mock_all_apis, test_config, paywalled_fixture):
        """Run workflow with DOI input."""
        from ai_in_loop.graph import analyze_paper

        # Mock to return paywalled fixture data
        def mock_requests_get(url, **kwargs):
            response = MagicMock()
            if "semanticscholar.org" in url:
                ss_data = paywalled_fixture.get("semantic_scholar")
                response.status_code = 200
                response.json.return_value = ss_data
            elif "crossref.org" in url:
                cr_data = paywalled_fixture.get("crossref")
                response.status_code = 200
                response.json.return_value = {"message": cr_data}
            elif "unpaywall.org" in url:
                unpaywall_data = paywalled_fixture.get("unpaywall")
                response.status_code = 200
                response.json.return_value = unpaywall_data
            else:
                response.status_code = 404
            return response

        with patch("ai_in_loop.tools.requests.get", side_effect=mock_requests_get):
            result = analyze_paper("https://doi.org/10.1038/nature12373", test_config)

        # Should have parsed the DOI
        assert result.get("input_type") == "doi", \
            "Workflow should set input_type to 'doi' for DOI input"
        assert result["identifier"] == "10.1038/nature12373"
