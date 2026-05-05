"""Unit tests for src/evaluation/question_bank.py — no external services."""

from src.evaluation.question_bank import (
    MULTI_HOP,
    QUESTION_BANK,
    SINGLE_HOP,
    EvalQuestion,
    multi_hop_questions,
    single_hop_questions,
)


def test_total_question_count() -> None:
    assert len(QUESTION_BANK) == 30


def test_single_hop_count() -> None:
    assert len(single_hop_questions()) == 15


def test_multi_hop_count() -> None:
    assert len(multi_hop_questions()) == 15


def test_all_questions_have_required_fields() -> None:
    for q in QUESTION_BANK:
        assert isinstance(q, EvalQuestion)
        assert q.question.strip() != "", "question must not be blank"
        assert q.query_type in (SINGLE_HOP, MULTI_HOP)
        assert q.gold_answer.strip() != "", "gold_answer must not be blank"
        assert isinstance(q.required_entities, list)
        assert isinstance(q.required_relationships, list)
