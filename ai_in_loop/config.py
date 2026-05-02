"""Configuration for the paper analyzer.

This module defines runtime configuration loaded from environment variables.
"""

from dataclasses import dataclass
import os
import sys


@dataclass(frozen=True)
class Config:
    """Runtime configuration loaded from environment variables."""

    use_gemini: bool
    gemini_api_key: str | None
    gemini_model: str
    temperature: float
    thinking_level: str | None  # For Gemini 3+: None, "low", "medium", "high"
    thinking_budget: int | None  # For Gemini 2.5: None or 0 = disabled, positive int = token budget
    api_email: str  # Email for API identification (Unpaywall, CrossRef polite pool)

    @staticmethod
    def from_env() -> "Config":
        """Load configuration from environment variables.

        Environment variables:
            USE_GEMINI: Set to "1" or "true" to use Gemini API (default: "0")
            GEMINI_API_KEY: API key for Gemini (required if USE_GEMINI=1)
            GEMINI_MODEL: Model to use (default: "gemini-2.5-flash")
            GEMINI_TEMPERATURE: Temperature setting (default: 0.7)
            GEMINI_THINKING_LEVEL: For Gemini 3+ models (default: "none")
            GEMINI_THINKING_BUDGET: For Gemini 2.5 models (default: 0)
            API_EMAIL: Email for API identification (Unpaywall, CrossRef)
        """
        use_gemini = os.getenv("USE_GEMINI", "0").strip() in {"1", "true", "TRUE", "yes", "YES"}
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        gemini_api_key = gemini_api_key.strip() if gemini_api_key else None

        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        temp_str = os.getenv("GEMINI_TEMPERATURE", "0.7").strip()
        thinking_level_str = os.getenv("GEMINI_THINKING_LEVEL", "none").strip().lower()

        try:
            temperature = float(temp_str)
        except ValueError:
            print(f"Warning: GEMINI_TEMPERATURE '{temp_str}' is not a valid number, using 0.7", file=sys.stderr)
            temperature = 0.7

        # Parse thinking settings - only warn about the one relevant to the current model
        is_gemini_3 = gemini_model.startswith("gemini-3")

        # Thinking level for Gemini 3+ models
        valid_thinking_levels = {"none", "low", "medium", "high"}
        if thinking_level_str in valid_thinking_levels:
            thinking_level = None if thinking_level_str == "none" else thinking_level_str
        else:
            if is_gemini_3:
                print(f"Warning: GEMINI_THINKING_LEVEL '{thinking_level_str}' is not valid (use none/low/medium/high), using none", file=sys.stderr)
            thinking_level = None

        # Thinking budget for Gemini 2.5 models
        thinking_budget_str = os.getenv("GEMINI_THINKING_BUDGET", "").strip()
        if thinking_budget_str:
            try:
                thinking_budget = int(thinking_budget_str)
            except ValueError:
                if not is_gemini_3:
                    print(f"Warning: GEMINI_THINKING_BUDGET '{thinking_budget_str}' is not a valid integer, using 0", file=sys.stderr)
                thinking_budget = 0
        else:
            thinking_budget = 0  # Default: no thinking

        # Email for API identification (Unpaywall requires it, CrossRef uses it for polite pool)
        api_email = os.getenv("API_EMAIL", "").strip()
        if not api_email:
            api_email = "student@example.edu"  # Default placeholder

        return Config(
            use_gemini=use_gemini,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            temperature=temperature,
            thinking_level=thinking_level,
            thinking_budget=thinking_budget,
            api_email=api_email,
        )
