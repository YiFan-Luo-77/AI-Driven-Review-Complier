"""Smoke tests to verify basic functionality works."""

from ai_in_loop.config import Config
from ai_in_loop.llm import get_llm, MockChatModel


def test_config_loads():
    """Config can be created with default values."""
    cfg = Config(
        use_gemini=False,
        gemini_api_key=None,
        gemini_model="gemini-2.5-flash",
        temperature=0.7,
        thinking_level=None,
        thinking_budget=0,
        api_email="test@example.edu",
    )
    assert cfg.use_gemini is False
    assert cfg.gemini_model == "gemini-2.5-flash"


def test_mock_llm_works():
    """MockChatModel can be instantiated and used."""
    cfg = Config(
        use_gemini=False,
        gemini_api_key=None,
        gemini_model="gemini-2.5-flash",
        temperature=0.7,
        thinking_level=None,
        thinking_budget=0,
        api_email="test@example.edu",
    )
    llm = get_llm(cfg)
    assert isinstance(llm, MockChatModel)


def test_graph_can_be_built(test_config):
    """Graph can be built without errors."""
    from ai_in_loop.graph import build_graph

    graph = build_graph(test_config)
    assert graph is not None
