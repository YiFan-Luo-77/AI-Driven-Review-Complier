"""Tests for the starter paper analyzer code.

These tests verify that the starter code works correctly:
- arXiv URL parsing
- Metadata fetching from APIs
- Basic workflow execution
- CLI functionality
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from ai_in_loop.tools import extract_arxiv_id, extract_doi
from ai_in_loop.nodes import parse_input, fetch_metadata_apis, route_by_metadata
from ai_in_loop.output import format_json, format_markdown


class TestArXivParsing:
    """Tests for arXiv ID extraction."""

    def test_extract_arxiv_id_from_abs_url(self):
        """Extract ID from arxiv.org/abs/ URL."""
        url = "https://arxiv.org/abs/1706.03762"
        assert extract_arxiv_id(url) == "1706.03762"

    def test_extract_arxiv_id_from_pdf_url(self):
        """Extract ID from arxiv.org/pdf/ URL."""
        url = "https://arxiv.org/pdf/1706.03762.pdf"
        assert extract_arxiv_id(url) == "1706.03762"

    def test_extract_arxiv_id_with_version(self):
        """Extract ID from URL with version number."""
        url = "https://arxiv.org/abs/1706.03762v3"
        assert extract_arxiv_id(url) == "1706.03762"

    def test_extract_arxiv_id_bare(self):
        """Extract bare arXiv ID."""
        assert extract_arxiv_id("1706.03762") == "1706.03762"

    def test_extract_arxiv_id_old_format(self):
        """Extract old-format arXiv ID."""
        url = "https://arxiv.org/abs/hep-th/9901001"
        assert extract_arxiv_id(url) == "hep-th/9901001"

    def test_extract_arxiv_id_invalid(self):
        """Return None for invalid input."""
        assert extract_arxiv_id("not a url") is None
        assert extract_arxiv_id("https://example.com") is None


class TestDOIParsing:
    """Tests for DOI extraction."""

    def test_extract_doi_from_doi_org_url(self):
        """Extract DOI from doi.org URL."""
        url = "https://doi.org/10.1038/nature12373"
        assert extract_doi(url) == "10.1038/nature12373"

    def test_extract_doi_from_dx_doi_org_url(self):
        """Extract DOI from dx.doi.org URL."""
        url = "http://dx.doi.org/10.1038/nature12373"
        assert extract_doi(url) == "10.1038/nature12373"

    def test_extract_doi_bare(self):
        """Extract bare DOI."""
        assert extract_doi("10.1038/nature12373") == "10.1038/nature12373"

    def test_extract_doi_invalid(self):
        """Return None for invalid input."""
        assert extract_doi("not a doi") is None
        assert extract_doi("https://arxiv.org/abs/1706.03762") is None


class TestParseInputNode:
    """Tests for the parse_input node."""

    def test_parse_arxiv_url(self):
        """Parse arXiv URL correctly."""
        state = {"query_url": "https://arxiv.org/abs/1706.03762", "warnings": []}
        result = parse_input(state)

        assert result["identifier"] == "1706.03762"
        assert result["arxiv_link"] == "https://arxiv.org/abs/1706.03762"

    def test_parse_invalid_url(self):
        """Handle invalid URL gracefully."""
        state = {"query_url": "not a valid url", "warnings": []}
        result = parse_input(state)

        assert result["identifier"] is None
        assert len(result["warnings"]) > 0


class TestFetchMetadataNode:
    """Tests for the fetch_metadata_apis node."""

    def test_fetch_metadata_no_identifier(self):
        """Handle missing identifier gracefully."""
        state = {"identifier": None, "warnings": []}
        result = fetch_metadata_apis(state)

        assert result["metadata"] is None
        assert len(result["warnings"]) > 0

    def test_fetch_metadata_with_arxiv(self, mock_all_apis, attention_fixture):
        """Fetch metadata for arXiv paper."""
        state = {
            "identifier": "1706.03762",
            "input_type": "arxiv",  # Used by solutions branch
            "arxiv_link": "https://arxiv.org/abs/1706.03762",
            "doi_link": None,
            "warnings": [],
        }
        result = fetch_metadata_apis(state)

        assert result["metadata"] is not None
        assert result["metadata"]["title"] is not None


class TestMetadataFallbacks:
    """Tests for metadata API fallback behavior."""

    def test_arxiv_semantic_scholar_succeeds(self, attention_fixture):
        """arXiv paper: Semantic Scholar returns data, CrossRef tried for enhancement."""
        ss_data = attention_fixture["semantic_scholar"]

        with patch("ai_in_loop.nodes.fetch_semantic_scholar", return_value=ss_data) as mock_ss, \
             patch("ai_in_loop.nodes.fetch_crossref", return_value=None) as mock_cr, \
             patch("ai_in_loop.nodes.fetch_arxiv") as mock_arxiv:

            state = {
                "identifier": "1706.03762",
                "input_type": "arxiv",  # Used by solutions branch
                "arxiv_link": "https://arxiv.org/abs/1706.03762",
                "doi_link": None,
                "warnings": [],
            }
            result = fetch_metadata_apis(state)

            # Semantic Scholar was called
            mock_ss.assert_called_once_with("1706.03762", "arxiv")
            # CrossRef called to try enhancement (with DOI from SS external_ids)
            mock_cr.assert_called_once()
            # arXiv API should NOT be called (no fallback needed)
            mock_arxiv.assert_not_called()

            assert result["metadata"] is not None
            # SS data used since CrossRef returned None
            assert result["metadata"]["title"] == ss_data["title"]

    def test_arxiv_fallback_to_arxiv_api(self, attention_fixture):
        """arXiv paper: Semantic Scholar fails, falls back to arXiv API."""
        arxiv_data = attention_fixture["arxiv"]

        with patch("ai_in_loop.nodes.fetch_semantic_scholar", return_value=None) as mock_ss, \
             patch("ai_in_loop.nodes.fetch_arxiv", return_value=arxiv_data) as mock_arxiv:

            state = {
                "identifier": "1706.03762",
                "input_type": "arxiv",  # Used by solutions branch
                "arxiv_link": "https://arxiv.org/abs/1706.03762",
                "doi_link": None,
                "warnings": [],
            }
            result = fetch_metadata_apis(state)

            # Both should be called
            mock_ss.assert_called_once_with("1706.03762", "arxiv")
            mock_arxiv.assert_called_once_with("1706.03762")

            # Should have metadata from arXiv API
            assert result["metadata"] is not None
            assert result["metadata"]["title"] == arxiv_data["title"]

    def test_arxiv_all_apis_fail(self):
        """arXiv paper: All APIs fail, warning added."""
        with patch("ai_in_loop.nodes.fetch_semantic_scholar", return_value=None), \
             patch("ai_in_loop.nodes.fetch_arxiv", return_value=None):

            state = {
                "identifier": "1706.03762",
                "input_type": "arxiv",  # Used by solutions branch
                "arxiv_link": "https://arxiv.org/abs/1706.03762",
                "doi_link": None,
                "warnings": [],
            }
            result = fetch_metadata_apis(state)

            assert result["metadata"] is None
            assert any("Could not fetch metadata" in w for w in result["warnings"])

    def test_doi_semantic_scholar_succeeds(self, paywalled_fixture):
        """DOI paper: Semantic Scholar returns data, CrossRef enhances citation."""
        ss_data = paywalled_fixture["semantic_scholar"]
        cr_data = paywalled_fixture["crossref"]

        with patch("ai_in_loop.nodes.fetch_semantic_scholar", return_value=ss_data) as mock_ss, \
             patch("ai_in_loop.nodes.fetch_crossref", return_value=cr_data) as mock_cr:

            state = {
                "identifier": "10.1038/nature12373",
                "input_type": "doi",  # Used by solutions branch
                "arxiv_link": None,  # Not an arXiv paper
                "doi_link": "https://doi.org/10.1038/nature12373",
                "warnings": [],
            }
            result = fetch_metadata_apis(state)

            # Semantic Scholar was called
            mock_ss.assert_called_once_with("10.1038/nature12373", "doi")
            # CrossRef is called to enhance citation data
            mock_cr.assert_called_once()

            assert result["metadata"] is not None
            # CrossRef data preferred for citation fields
            assert result["metadata"]["title"] == cr_data["title"]

    def test_doi_fallback_to_crossref(self, paywalled_fixture):
        """DOI paper: Semantic Scholar fails, falls back to CrossRef."""
        cr_data = paywalled_fixture["crossref"]

        with patch("ai_in_loop.nodes.fetch_semantic_scholar", return_value=None) as mock_ss, \
             patch("ai_in_loop.nodes.fetch_crossref", return_value=cr_data) as mock_cr:

            state = {
                "identifier": "10.1038/nature12373",
                "input_type": "doi",  # Used by solutions branch
                "arxiv_link": None,  # Not an arXiv paper
                "doi_link": "https://doi.org/10.1038/nature12373",
                "warnings": [],
            }
            result = fetch_metadata_apis(state)

            # Both should be called
            mock_ss.assert_called_once_with("10.1038/nature12373", "doi")
            mock_cr.assert_called_once_with("10.1038/nature12373")

            # Should have metadata from CrossRef
            assert result["metadata"] is not None
            assert result["metadata"]["title"] == cr_data["title"]

    def test_doi_all_apis_fail(self):
        """DOI paper: All APIs fail, warning added."""
        with patch("ai_in_loop.nodes.fetch_semantic_scholar", return_value=None), \
             patch("ai_in_loop.nodes.fetch_crossref", return_value=None):

            state = {
                "identifier": "10.1038/nature12373",
                "input_type": "doi",  # Used by solutions branch
                "arxiv_link": None,
                "doi_link": "https://doi.org/10.1038/nature12373",
                "warnings": [],
            }
            result = fetch_metadata_apis(state)

            assert result["metadata"] is None
            assert any("Could not fetch metadata" in w for w in result["warnings"])

    def test_crossref_partial_data_preserves_ss_fields(self, attention_fixture):
        """CrossRef returns partial data: SS fields preserved for missing CR fields."""
        ss_data = attention_fixture["semantic_scholar"]
        # CrossRef returns only venue and year, missing title/authors/abstract
        partial_cr_data = {
            "title": None,
            "authors": [],
            "venue": "NeurIPS 2017",
            "year": 2017,
            "abstract": None,
        }

        with patch("ai_in_loop.nodes.fetch_semantic_scholar", return_value=ss_data), \
             patch("ai_in_loop.nodes.fetch_crossref", return_value=partial_cr_data):

            state = {
                "identifier": "1706.03762",
                "input_type": "arxiv",  # Used by solutions branch
                "arxiv_link": "https://arxiv.org/abs/1706.03762",
                "doi_link": None,
                "warnings": [],
            }
            result = fetch_metadata_apis(state)

            assert result["metadata"] is not None
            # SS fields preserved where CR is falsy
            assert result["metadata"]["title"] == ss_data["title"]
            assert result["metadata"]["authors"] == ss_data["authors"]
            assert result["metadata"]["abstract"] == ss_data["abstract"]
            # CR fields used where truthy
            assert result["metadata"]["venue"] == "NeurIPS 2017"
            assert result["metadata"]["year"] == 2017


class TestRouteByMetadata:
    """Tests for the route_by_metadata routing function."""

    def test_route_with_metadata(self):
        """Route to summarize when metadata exists."""
        state = {"metadata": {"title": "Test Paper", "authors": ["Author"]}}
        assert route_by_metadata(state) == "summarize"

    def test_route_without_metadata(self):
        """Route to llm_extract_metadata when no metadata."""
        state = {"metadata": None}
        assert route_by_metadata(state) == "llm_extract_metadata"

    def test_route_with_empty_metadata(self):
        """Route to llm_extract_metadata when metadata is empty."""
        state = {"metadata": {}}
        assert route_by_metadata(state) == "llm_extract_metadata"


class TestOutputFormatting:
    """Tests for output formatting functions."""

    def test_format_json_basic(self):
        """Format basic state as JSON."""
        state = {
            "query_url": "https://arxiv.org/abs/1706.03762",
            "metadata": {
                "title": "Test Paper",
                "authors": ["Author One"],
                "venue": "Test Venue",
                "year": 2020,
                "abstract": "Test abstract.",
            },
            "arxiv_link": "https://arxiv.org/abs/1706.03762",
            "doi_link": None,
            "summary": "Test summary.",
            "warnings": [],
        }
        output = format_json(state)

        import json
        parsed = json.loads(output)

        assert parsed["query_url"] == "https://arxiv.org/abs/1706.03762"
        assert parsed["citation"]["title"] == "Test Paper"
        assert parsed["summary"] == "Test summary."

    def test_format_markdown_basic(self):
        """Format basic state as Markdown."""
        state = {
            "query_url": "https://arxiv.org/abs/1706.03762",
            "metadata": {
                "title": "Test Paper",
                "authors": ["Author One"],
                "venue": "Test Venue",
                "year": 2020,
                "abstract": "Test abstract.",
            },
            "arxiv_link": "https://arxiv.org/abs/1706.03762",
            "doi_link": None,
            "summary": "Test summary.",
            "warnings": [],
        }
        output = format_markdown(state)

        assert "# Test Paper" in output
        assert "Author One" in output
        assert "Test summary." in output


class TestWorkflowExecution:
    """Tests for end-to-end workflow execution."""

    def test_full_workflow_arxiv(self, mock_all_apis, test_config):
        """Run complete workflow for arXiv paper."""
        from ai_in_loop.graph import analyze_paper

        result = analyze_paper("https://arxiv.org/abs/1706.03762", test_config)

        assert result["identifier"] == "1706.03762"
        assert result["metadata"] is not None
        # Summary should be generated (using mock LLM)
        assert result["summary"] is not None


class TestCLI:
    """Tests for CLI functionality."""

    def test_cli_help(self):
        """CLI shows help without error."""
        from typer.testing import CliRunner
        from ai_in_loop.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "analyze" in result.output

    def test_analyze_command_exists(self):
        """Analyze command is registered."""
        from typer.testing import CliRunner
        from ai_in_loop.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["analyze", "--help"])

        # Should show help for analyze command
        assert result.exit_code == 0
        assert "analyze" in result.output.lower() or "arxiv" in result.output.lower()

    def test_analyze_with_mock(self, mock_all_apis):
        """Run analyze command with mocked APIs."""
        from typer.testing import CliRunner
        from ai_in_loop.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["analyze", "https://arxiv.org/abs/1706.03762"])

        # Should complete without error
        assert result.exit_code == 0
