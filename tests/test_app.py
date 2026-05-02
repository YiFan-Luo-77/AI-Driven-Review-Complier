"""Full tests for the Streamlit Paper Analyzer app.

These tests verify the complete app functionality (Steps 1-7):
- Workflow runs and produces a summary from the mock LLM
- Metadata from the fixture is displayed (title, authors)
- st.metric elements show correct values from fixture data
- st.expander contains paper metadata
- Workflow warnings from API failures are surfaced

All tests mock the external API calls to avoid network access.
These tests should pass once all 7 steps are completed.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


# ── Fixture loading ──────────────────────────────────────────────────
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "papers"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text())


def _mock_apis():
    """Return a context manager that mocks all external API calls."""
    fixture = _load_fixture("attention")
    ss_data = fixture.get("semantic_scholar")
    arxiv_data = fixture.get("arxiv")
    crossref_data = fixture.get("crossref")
    unpaywall_data = fixture.get("unpaywall")

    unpaywall_normalized = None
    if unpaywall_data and unpaywall_data.get("best_oa_location"):
        loc = unpaywall_data["best_oa_location"]
        unpaywall_normalized = {
            "is_oa": unpaywall_data.get("is_oa", False),
            "oa_url": loc.get("url_for_pdf") or loc.get("url"),
            "oa_version": loc.get("version"),
            "license": loc.get("license"),
        }

    sample_text = (
        "Abstract\n\n"
        "This paper presents a novel approach to the problem at hand.\n"
        "We demonstrate significant improvements over prior work.\n\n"
        "1. Introduction\n\n"
        "The field has seen rapid progress in recent years.\n"
    )

    class _MockContext:
        def __init__(self):
            self._patches = [
                patch.dict(os.environ, {"USE_GEMINI": "0"}),
                patch("ai_in_loop.nodes.fetch_semantic_scholar", return_value=ss_data),
                patch("ai_in_loop.nodes.fetch_arxiv", return_value=arxiv_data),
                patch("ai_in_loop.nodes.fetch_crossref", return_value=crossref_data),
                patch("ai_in_loop.nodes.fetch_unpaywall", return_value=unpaywall_normalized),
                patch("ai_in_loop.tools.extract_pdf_text", return_value=sample_text),
            ]

        def __enter__(self):
            for p in self._patches:
                p.__enter__()
            return self

        def __exit__(self, *args):
            for p in reversed(self._patches):
                p.__exit__(*args)

    return _MockContext()


def _mock_apis_no_data():
    """Mock all APIs to return None (simulating failures)."""

    class _MockContext:
        def __init__(self):
            self._patches = [
                patch.dict(os.environ, {"USE_GEMINI": "0"}),
                patch("ai_in_loop.nodes.fetch_semantic_scholar", return_value=None),
                patch("ai_in_loop.nodes.fetch_arxiv", return_value=None),
                patch("ai_in_loop.nodes.fetch_crossref", return_value=None),
                patch("ai_in_loop.nodes.fetch_unpaywall", return_value=None),
                patch("ai_in_loop.tools.extract_pdf_text", return_value=None),
            ]

        def __enter__(self):
            for p in self._patches:
                p.__enter__()
            return self

        def __exit__(self, *args):
            for p in reversed(self._patches):
                p.__exit__(*args)

    return _MockContext()


# ── Helper ───────────────────────────────────────────────────────────


def _run_analysis(mock_ctx):
    """Run the app, enter URL, click Analyze, return the AppTest instance."""
    with mock_ctx:
        at = AppTest.from_file("app.py")
        at.run(timeout=30)
        assert not at.exception, f"App raised an exception on load: {at.exception}"

        assert len(at.text_input) > 0, (
            "No st.text_input found. Complete Step 1 before running these tests."
        )
        assert len(at.button) > 0, (
            "No st.button found. Complete Step 2 before running these tests."
        )

        at.text_input[0].set_value("https://arxiv.org/abs/1706.03762").run(timeout=30)
        at.button[0].click().run(timeout=30)
        assert not at.exception, f"App raised an exception during analysis: {at.exception}"
        return at


# ── Tests ────────────────────────────────────────────────────────────


def test_analysis_produces_summary():
    """Workflow runs through mock LLM and the summary is displayed.

    The MockChatModel returns text containing '[MOCK SUMMARY]'.
    This proves the workflow actually ran (not hardcoded text).
    """
    at = _run_analysis(_mock_apis())

    md_values = [m.value for m in at.markdown]
    combined = " ".join(md_values)
    assert "MOCK SUMMARY" in combined, (
        "Expected '[MOCK SUMMARY]' in markdown output (from MockChatModel). "
        "Make sure Step 4 streams the workflow and Step 5 displays the summary. "
        f"Found markdown: {md_values[:5]}"
    )


def test_analysis_shows_metadata():
    """Paper title from fixture data appears in the output.

    The fixture's CrossRef title is 'Attention Is All You Need'.
    This proves the app displays real metadata from the workflow,
    not placeholder text.
    """
    at = _run_analysis(_mock_apis())

    all_text = " ".join(m.value for m in at.markdown)
    assert "Attention" in all_text, (
        "Expected paper title 'Attention Is All You Need' in markdown output. "
        "Make sure Step 6 displays the metadata title. "
        f"Found markdown: {[m.value for m in at.markdown][:5]}"
    )


def test_analysis_metrics_have_correct_values():
    """st.metric elements display correct values from the fixture.

    The attention fixture has year=2017, 8 authors, venue from CrossRef.
    """
    at = _run_analysis(_mock_apis())

    assert len(at.metric) >= 3, (
        f"Expected at least 3 st.metric elements (Year, Authors, Venue), "
        f"found {len(at.metric)}. Make sure Step 6 creates metrics in columns."
    )

    # Collect metric labels and values
    metrics = {m.label: m.value for m in at.metric}

    # Check year metric
    assert "Year" in metrics, (
        f"Expected a metric labeled 'Year'. Found labels: {list(metrics.keys())}"
    )
    assert str(metrics["Year"]) == "2017", (
        f"Expected Year metric value '2017', got '{metrics['Year']}'. "
        "Make sure you're reading year from the workflow metadata."
    )

    # Check authors metric
    assert "Authors" in metrics, (
        f"Expected a metric labeled 'Authors'. Found labels: {list(metrics.keys())}"
    )
    assert str(metrics["Authors"]) == "8", (
        f"Expected Authors metric value '8', got '{metrics['Authors']}'. "
        "Make sure you're counting len(metadata['authors'])."
    )


def test_analysis_has_expander_with_content():
    """st.expander is used and contains paper metadata."""
    at = _run_analysis(_mock_apis())

    assert len(at.expander) > 0, (
        "No st.expander found. Use st.expander() to wrap the paper metadata section."
    )

    # Check that the expander contains the metrics (not placed outside)
    expander = at.expander[0]
    expander_metrics = expander.metric
    assert len(expander_metrics) > 0, (
        "st.expander exists but has no st.metric elements inside it. "
        "Make sure the metrics are placed inside the expander context manager."
    )


def test_workflow_warnings_displayed():
    """Warnings from API failures are shown with st.warning.

    When all APIs return None, the workflow generates warnings like
    'Could not fetch metadata from any API'. These must be surfaced
    to the user via st.warning().
    """
    at = _run_analysis(_mock_apis_no_data())

    assert len(at.warning) > 0, (
        "No st.warning elements found. When the workflow produces warnings, "
        "Step 7 should loop over them and call st.warning() for each one."
    )

    # Verify warnings contain actual workflow messages, not hardcoded text
    warning_texts = [w.value for w in at.warning]
    combined = " ".join(warning_texts)
    assert "metadata" in combined.lower() or "could not" in combined.lower(), (
        f"Warnings don't contain expected workflow messages. "
        f"Expected messages about failed metadata fetching. "
        f"Found: {warning_texts}"
    )
