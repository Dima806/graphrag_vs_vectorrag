"""Unit tests for src/evaluation/rag_triad.py — LLM calls mocked."""

import math
from unittest.mock import MagicMock, patch

import pytest

from src.evaluation.rag_triad import RAGTriad, parse_score

# ── parse_score ──────────────────────────────────────────────────────────────


def test_parse_score_decimal() -> None:
    assert parse_score("0.85") == pytest.approx(0.85)


def test_parse_score_integer_one() -> None:
    assert parse_score("1") == pytest.approx(1.0)


def test_parse_score_integer_zero() -> None:
    assert parse_score("0") == pytest.approx(0.0)


def test_parse_score_clamps_above_one() -> None:
    assert parse_score("1.5") == pytest.approx(1.0)


def test_parse_score_clamps_below_zero() -> None:
    assert parse_score("-0.3") == pytest.approx(0.0)


def test_parse_score_extracts_from_surrounding_text() -> None:
    assert parse_score("The score is 0.72 out of 1.") == pytest.approx(0.72)


def test_parse_score_returns_zero_on_no_match() -> None:
    assert parse_score("no number here") == pytest.approx(0.0)


# ── RAGTriad.evaluate ─────────────────────────────────────────────────────────


def _make_triad(cr: float, gr: float, ar: float) -> tuple[RAGTriad, MagicMock]:
    with patch("src.evaluation.rag_triad.httpx.post"):
        triad = RAGTriad()

    responses = [str(cr), str(gr), str(ar)]
    call_count = 0

    def side_effect(*args, **kwargs):  # noqa: ANN002, ANN003
        nonlocal call_count
        mock = MagicMock()
        mock.raise_for_status.return_value = None
        mock.json.return_value = {"response": responses[call_count % len(responses)]}
        call_count += 1
        return mock

    return triad, side_effect


@patch("src.evaluation.rag_triad.httpx.post")
def test_evaluate_returns_all_keys(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"response": "0.8"}),
    )
    triad = RAGTriad()
    result = triad.evaluate("q", "context", "answer")
    assert set(result.keys()) == {"context_relevance", "groundedness", "answer_relevance", "triad"}


@patch("src.evaluation.rag_triad.httpx.post")
def test_evaluate_geometric_mean(mock_post: MagicMock) -> None:
    responses = ["0.8", "0.6", "0.9"]
    call_iter = iter(responses)

    def side_effect(*args, **kwargs):  # noqa: ANN002, ANN003
        val = next(call_iter, "0.5")
        m = MagicMock()
        m.raise_for_status.return_value = None
        m.json.return_value = {"response": val}
        return m

    mock_post.side_effect = side_effect
    triad = RAGTriad()
    result = triad.evaluate("q", "ctx", "ans")
    expected = math.pow(0.8 * 0.6 * 0.9, 1 / 3)
    assert result["triad"] == pytest.approx(expected, abs=1e-6)


@patch("src.evaluation.rag_triad.httpx.post")
def test_evaluate_zero_product_gives_zero_triad(mock_post: MagicMock) -> None:
    mock_post.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"response": "0.0"}),
    )
    triad = RAGTriad()
    result = triad.evaluate("q", "ctx", "ans")
    assert result["triad"] == pytest.approx(0.0)
