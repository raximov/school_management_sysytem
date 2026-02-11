from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ChoiceQuestion:
    points: Decimal
    correct_option_ids: set[int]


@dataclass(frozen=True)
class ShortAnswerQuestion:
    points: Decimal
    accepted_answers: set[str]
    case_sensitive: bool = False


@dataclass(frozen=True)
class ComputationalQuestion:
    points: Decimal
    expected_answer: Decimal
    tolerance: Decimal


@dataclass(frozen=True)
class ScoreResult:
    is_correct: bool
    awarded_points: Decimal
    feedback: str = ""


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def grade_single_choice(question: ChoiceQuestion, selected_option_ids: Sequence[int]) -> ScoreResult:
    selected = set(selected_option_ids)
    is_correct = len(selected) == 1 and selected == question.correct_option_ids
    return ScoreResult(is_correct=is_correct, awarded_points=question.points if is_correct else Decimal("0"))


def grade_multiple_choice_exact(question: ChoiceQuestion, selected_option_ids: Sequence[int]) -> ScoreResult:
    selected = set(selected_option_ids)
    is_correct = selected == question.correct_option_ids
    return ScoreResult(is_correct=is_correct, awarded_points=question.points if is_correct else Decimal("0"))


def grade_multiple_choice_partial(question: ChoiceQuestion, selected_option_ids: Sequence[int]) -> ScoreResult:
    if not question.correct_option_ids:
        return ScoreResult(is_correct=False, awarded_points=Decimal("0"), feedback="No correct options configured")

    selected = set(selected_option_ids)
    correct = question.correct_option_ids

    hits = len(selected & correct)
    misses = len(selected - correct)

    per_option = question.points / _to_decimal(len(correct))
    raw = (per_option * _to_decimal(hits)) - (per_option * _to_decimal(misses))
    awarded = max(Decimal("0"), raw.quantize(Decimal("0.01")))
    is_correct = selected == correct
    return ScoreResult(
        is_correct=is_correct,
        awarded_points=awarded,
        feedback="partial" if not is_correct and awarded > 0 else "",
    )


def grade_short_answer(question: ShortAnswerQuestion, submitted_text: str | None) -> ScoreResult:
    submitted = (submitted_text or "").strip()
    if not submitted:
        return ScoreResult(is_correct=False, awarded_points=Decimal("0"), feedback="empty answer")

    accepted = question.accepted_answers
    if not question.case_sensitive:
        submitted = submitted.lower()
        accepted = {a.lower().strip() for a in accepted}

    is_correct = submitted in accepted
    return ScoreResult(is_correct=is_correct, awarded_points=question.points if is_correct else Decimal("0"))


def grade_computational(question: ComputationalQuestion, submitted_value: Decimal | int | float | str | None) -> ScoreResult:
    if submitted_value is None:
        return ScoreResult(is_correct=False, awarded_points=Decimal("0"), feedback="missing numeric answer")

    actual = _to_decimal(submitted_value)
    expected = _to_decimal(question.expected_answer)
    tolerance = abs(_to_decimal(question.tolerance))

    distance = abs(actual - expected)
    is_correct = distance <= tolerance
    return ScoreResult(is_correct=is_correct, awarded_points=question.points if is_correct else Decimal("0"))


def total_score(results: Iterable[ScoreResult]) -> Decimal:
    total = sum((r.awarded_points for r in results), start=Decimal("0"))
    return total.quantize(Decimal("0.01"))
