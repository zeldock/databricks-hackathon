"""Grade calculator: current average, expected final grade, and the D/F check.

The WolfHacks dataset only labels "D or F" (final score below 70) without final scores, so the model alone can
estimate *risk* but not a letter grade. The expected grade here comes from the student's actual graded work
(weighted scores), and is cross-checked against the model's prediction.

Grade items are dicts: {"item": str, "type": str, "weight": float (% of course grade), "score": float | None}
A score of None means "not graded yet" — its weight counts as remaining work.
"""

from __future__ import annotations

import math
from typing import Any

ITEM_TYPES = ["Assignment", "Quiz", "Midterm", "Final exam", "Exam", "Project", "Lab", "Participation", "Other"]
# Standard US scale; plus/minus grades are not distinguished.
LETTER_CUTOFFS = [(90, "A"), (80, "B"), (70, "C"), (60, "D"), (0, "F")]
PASSING = 70  # matches the dataset: at_risk = final score below 70 (a D or F)


def letter(score: float | None) -> str | None:
    if score is None:
        return None
    for cutoff, grade in LETTER_CUTOFFS:
        if score >= cutoff:
            return grade
    return "F"


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else number


def clean_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop blank rows and coerce numbers (data editors return NaN/None for empty cells)."""
    cleaned = []
    for row in items:
        raw_name = row.get("item")
        name = "" if raw_name is None or (isinstance(raw_name, float) and math.isnan(raw_name)) else str(raw_name).strip()
        weight, score = _number(row.get("weight")), _number(row.get("score"))
        if not name and weight is None and score is None:
            continue
        kind = row.get("type")
        kind = kind if isinstance(kind, str) and kind in ITEM_TYPES else "Other"
        cleaned.append({"item": name or "Untitled", "type": kind,
                        "weight": weight, "score": score})
    return cleaned


def validate(items: list[dict[str, Any]]) -> list[str]:
    errors = []
    for row in items:
        if row["weight"] is None or row["weight"] <= 0:
            errors.append(f"“{row['item']}” needs a weight greater than 0%.")
        if row["score"] is not None and not 0 <= row["score"] <= 120:
            errors.append(f"“{row['item']}” has a score of {row['score']:g}% — scores must be 0–120%.")
    total = sum(r["weight"] or 0 for r in items)
    if total > 100.0001:
        errors.append(f"Weights add up to {total:g}% — they can't be more than 100%.")
    return errors


def summarize(items: list[dict[str, Any]], remaining_score: float | None = None) -> dict[str, Any]:
    """Weighted current average, projected final grade, and the score needed on remaining work per letter.

    ``remaining_score`` is the % the student expects on ungraded work; defaults to their current average.
    """
    graded = [r for r in items if r["score"] is not None and r["weight"]]
    graded_weight = sum(r["weight"] for r in graded)
    total_weight = sum(r["weight"] or 0 for r in items)
    remaining_weight = max(0.0, 100 - graded_weight)
    earned_points = sum(r["weight"] * r["score"] for r in graded) / 100  # points out of the whole course

    current = earned_points * 100 / graded_weight if graded_weight else None
    expected_remaining = current if remaining_score is None else remaining_score
    projected = (earned_points + remaining_weight * expected_remaining / 100
                 if expected_remaining is not None else None)

    needed = {}
    for cutoff, grade in LETTER_CUTOFFS[:-1]:
        if remaining_weight <= 0:
            needed[grade] = None
        else:
            needed[grade] = (cutoff - earned_points) * 100 / remaining_weight

    return {
        "graded_weight": graded_weight,
        "total_weight": total_weight,
        "unlisted_weight": max(0.0, 100 - total_weight),
        "remaining_weight": remaining_weight,
        "earned_points": earned_points,
        "current": current,
        "current_letter": letter(current),
        "projected": projected,
        "projected_letter": letter(projected),
        "best_case": earned_points + remaining_weight,
        "worst_case": earned_points,
        "needed": needed,
    }


def midterm_score(items: list[dict[str, Any]]) -> float | None:
    """Average score of graded Midterm items — fed to the risk model's midterm_score feature."""
    scores = [r["score"] for r in items if r["type"] == "Midterm" and r["score"] is not None]
    return sum(scores) / len(scores) if scores else None


def df_band(score: float | None) -> str | None:
    """'D' for 60–69, 'F' for under 60, None when passing (C or better) or unknown."""
    grade = letter(score)
    return grade if grade in ("D", "F") else None


def _a(grade: str | None) -> str:
    """'an F' / 'an A' but 'a B' — with the grade in bold."""
    return f"{'an' if grade in ('A', 'F') else 'a'} **{grade}**"


def cross_check(projected: float | None, model_at_risk: bool) -> tuple[str, str]:
    """Compare the grade-based projection with the model. Returns (level, message) for an alert box."""
    band = df_band(projected)
    if projected is None:
        return "info", "Add graded work to verify the model's prediction against your real grades."
    if band and model_at_risk:
        return "error", (f"Both agree: your grades project {_a(band)} ({projected:.1f}%) and the model flags "
                         "you as at risk. Act now — see the steps below.")
    if band:
        return "error", (f"Your grades project {_a(band)} ({projected:.1f}%), even though your study habits "
                         "look on track to the model. Your scores need attention first.")
    if model_at_risk:
        return "warning", (f"Your grades project {_a(letter(projected))} ({projected:.1f}%), but your habits "
                           "match students who ended with a D or F. Keep your scores up by fixing the habits below.")
    return "success", (f"Both agree: your grades project {_a(letter(projected))} ({projected:.1f}%) and your "
                       "habits look on track.")
