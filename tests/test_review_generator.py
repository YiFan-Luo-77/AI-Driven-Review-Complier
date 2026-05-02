"""Tests for src/review_generator.py."""

from unittest.mock import MagicMock

from src.review_generator import generate_review

SAMPLE_GAME_INFO = {
    "name": "Test Quest",
    "developer": "Dev Studio",
    "publisher": "Pub Inc.",
    "genres": ["RPG", "Adventure"],
    "release_date": "1 Jan, 2024",
    "price": "$29.99",
    "short_description": "An epic quest through a test world.",
    "platforms": {"windows": True, "mac": False, "linux": True},
    "metacritic_score": 82,
}


def _make_mock_client(reply: str = "Great game! Score: 8/10") -> MagicMock:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = reply
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


def test_generate_review_returns_string():
    client = _make_mock_client("Fantastic game. Score: 9/10")
    result = generate_review(SAMPLE_GAME_INFO, client=client)
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_review_returns_client_response():
    expected = "This is the mocked review content."
    client = _make_mock_client(expected)
    result = generate_review(SAMPLE_GAME_INFO, client=client)
    assert result == expected


def test_generate_review_includes_user_experience_in_prompt():
    client = _make_mock_client()
    generate_review(SAMPLE_GAME_INFO, user_experience="I loved the boss fights!", client=client)

    call_kwargs = client.chat.completions.create.call_args.kwargs
    messages = call_kwargs["messages"]
    user_msg = next(m for m in messages if m["role"] == "user")
    assert "I loved the boss fights!" in user_msg["content"]


def test_generate_review_no_user_experience_omits_section():
    client = _make_mock_client()
    generate_review(SAMPLE_GAME_INFO, user_experience=None, client=client)

    call_kwargs = client.chat.completions.create.call_args.kwargs
    messages = call_kwargs["messages"]
    user_msg = next(m for m in messages if m["role"] == "user")
    assert "Player's Personal Experience" not in user_msg["content"]


def test_generate_review_prompt_includes_game_name():
    client = _make_mock_client()
    generate_review(SAMPLE_GAME_INFO, client=client)

    call_kwargs = client.chat.completions.create.call_args.kwargs
    messages = call_kwargs["messages"]
    user_msg = next(m for m in messages if m["role"] == "user")
    assert "Test Quest" in user_msg["content"]


def test_generate_review_prompt_includes_metacritic():
    client = _make_mock_client()
    generate_review(SAMPLE_GAME_INFO, client=client)

    call_kwargs = client.chat.completions.create.call_args.kwargs
    messages = call_kwargs["messages"]
    user_msg = next(m for m in messages if m["role"] == "user")
    assert "82" in user_msg["content"]


def test_generate_review_no_metacritic_score():
    game_info = {**SAMPLE_GAME_INFO, "metacritic_score": None}
    client = _make_mock_client()
    generate_review(game_info, client=client)

    call_kwargs = client.chat.completions.create.call_args.kwargs
    messages = call_kwargs["messages"]
    user_msg = next(m for m in messages if m["role"] == "user")
    assert "Metacritic Score" not in user_msg["content"]


def test_generate_review_calls_gpt4o():
    client = _make_mock_client()
    generate_review(SAMPLE_GAME_INFO, client=client)

    call_kwargs = client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o"
