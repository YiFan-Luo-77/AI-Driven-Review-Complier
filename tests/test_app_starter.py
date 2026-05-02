"""Starter tests for the Streamlit Paper Analyzer app.

These tests verify the basic UI scaffolding (Steps 1-3):
- App loads without errors
- Title element exists
- Text input widget exists
- Button widget exists
- Empty URL shows a warning

These tests should pass once Steps 1-3 are completed.
"""

from streamlit.testing.v1 import AppTest


def test_app_loads_without_error():
    """App loads and runs without raising an exception."""
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    assert not at.exception, f"App raised an exception: {at.exception}"


def test_app_has_title():
    """App displays a title element."""
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    assert len(at.title) > 0, "No st.title found in the app"
    assert at.title[0].value == "Paper Analyzer"


def test_app_has_text_input():
    """App has a text input widget for entering paper URLs."""
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    assert len(at.text_input) > 0, "No st.text_input found in the app"


def test_app_has_button():
    """App has an Analyze button."""
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    assert len(at.button) > 0, "No st.button found in the app"


def test_empty_url_shows_warning():
    """Clicking Analyze with an empty URL shows a warning."""
    at = AppTest.from_file("app.py")
    at.run(timeout=30)

    # Click the Analyze button without entering a URL
    at.button[0].click().run(timeout=30)

    assert len(at.warning) > 0, "No st.warning shown for empty URL"
