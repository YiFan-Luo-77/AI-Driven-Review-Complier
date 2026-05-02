"""Verify A8 submission requirements.

This script checks that all required files exist and contain expected content.
Students can run this before submitting to ensure their work is complete.
"""

from __future__ import annotations

from pathlib import Path


REQUIRED_FILES = [
    Path("app.py"),
    Path("docs/ai_dev_log.md"),
    Path("docs/activity1_streamlit.md"),
    Path("docs/activity2_testing.md"),
    Path("ai_in_loop/state.py"),
    Path("ai_in_loop/nodes.py"),
    Path("ai_in_loop/graph.py"),
]

PLACEHOLDER_TOKENS = [
    "REPLACE_ME",
]

# Required fields for ai_dev_log.md
DEV_LOG_REQUIRED_FIELDS = [
    "**Date:**",
    "**Goal:**",
    "**Tool used:**",
    "**Changes Made:**",
    "**Result:**",
]

# Required sections for activity1_streamlit.md
ACTIVITY1_SECTIONS = [
    "## Background",
    "## Your Implementation Notes",
]

# Required sections for activity2_testing.md
ACTIVITY2_SECTIONS = [
    "## Test Results",
    "## Reflection",
]

# Minimum content lengths per file
MIN_LENGTHS = {
    "docs/ai_dev_log.md": 100,
    "docs/activity1_streamlit.md": 400,
    "docs/activity2_testing.md": 400,
}

# Required Streamlit widgets in app.py
REQUIRED_WIDGETS = [
    "st.text_input",
    "st.button",
    "st.markdown",
    "st.expander",
    ".metric(",
    "st.warning",
    "pipeline.stream",
]


def check_file(
    path: Path,
    min_length: int = 50,
    required_fields: list[str] | None = None,
) -> list[str]:
    """Check a file for basic requirements and optional required fields.

    Args:
        path: Path to file to check
        min_length: Minimum content length required
        required_fields: Optional list of field markers that must be present

    Returns:
        List of problems found (empty if all checks pass)
    """
    problems: list[str] = []

    if not path.exists():
        problems.append(f"Missing required file: {path}")
        return problems

    text = path.read_text(encoding="utf-8").strip()

    if len(text) < min_length:
        problems.append(f"{path} looks too short ({len(text)} chars, need {min_length}) - did you fill it in?")

    # Check for required fields if specified
    if required_fields:
        for field in required_fields:
            if field not in text:
                problems.append(f"{path} missing required section: {field}")

    # Check for placeholders
    for token in PLACEHOLDER_TOKENS:
        if token in text:
            problems.append(f"{path} still contains placeholder token '{token}'")
            break

    return problems


def check_app_py() -> list[str]:
    """Check that app.py contains required Streamlit widgets in code (not comments)."""
    problems: list[str] = []

    app_path = Path("app.py")
    if not app_path.exists():
        problems.append("Missing app.py")
        return problems

    # Extract only non-comment code lines
    lines = app_path.read_text(encoding="utf-8").splitlines()
    code_lines = [line for line in lines if not line.strip().startswith("#")]
    code = "\n".join(code_lines)

    for widget in REQUIRED_WIDGETS:
        if widget not in code:
            problems.append(f"app.py missing required widget: {widget}")

    # Check that st.status or st.spinner is used for progress
    if "st.status" not in code and "st.spinner" not in code:
        problems.append("app.py missing progress indicator (st.status or st.spinner)")

    return problems


def main() -> int:
    problems: list[str] = []

    for f in REQUIRED_FILES:
        file_key = str(f)
        min_len = MIN_LENGTHS.get(file_key, 50)

        if f.name == "ai_dev_log.md":
            problems.extend(check_file(f, min_length=min_len, required_fields=DEV_LOG_REQUIRED_FIELDS))
        elif f.name == "activity1_streamlit.md":
            problems.extend(check_file(f, min_length=min_len, required_fields=ACTIVITY1_SECTIONS))
        elif f.name == "activity2_testing.md":
            problems.extend(check_file(f, min_length=min_len, required_fields=ACTIVITY2_SECTIONS))
        elif f.suffix == ".py":
            # Just check existence for Python files
            if not f.exists():
                problems.append(f"Missing required file: {f}")
        else:
            problems.extend(check_file(f, min_length=min_len))

    # Check app.py for required Streamlit widgets
    problems.extend(check_app_py())

    if problems:
        print("Submission Verification: PROBLEMS FOUND")
        print()
        for p in problems:
            print(f"  - {p}")
        print()
        print(f"Found {len(problems)} issue(s). Please fix and try again.")
        return 1

    print("Submission Verification: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
