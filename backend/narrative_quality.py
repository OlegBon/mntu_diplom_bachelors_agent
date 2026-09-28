"""Explainable, non-blocking metadata checks for private report narratives."""

from __future__ import annotations

from collections import Counter
import re
from typing import Iterable


# These are deliberately conservative review signals, not a quality rubric or
# validation rules.  They are kept here, with their messages, so API and UI
# cannot disagree about what was detected.
SHORT_TEXT_WORDS = 2
LONG_TEXT_CHARACTERS = 4_000
PLACEHOLDERS = frozenset({"-", "—", "…", "...", "n/a", "na", "test", "тест", "не вказано"})
WORD_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", flags=re.UNICODE)


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").split())


def word_count(value: str | None) -> int:
    """Count Ukrainian and English words under one Unicode-aware rule."""
    return len(WORD_PATTERN.findall(normalize_text(value)))


def non_whitespace_char_count(value: str | None) -> int:
    return len(re.sub(r"\s+", "", value or ""))


def _is_repetitive(words: Iterable[str]) -> bool:
    tokens = [word.casefold() for word in words]
    if len(tokens) < 3:
        return False
    return len(set(tokens)) == 1 or Counter(tokens).most_common(1)[0][1] >= 4


def check_text(*, field_key: str, label: str, value: str | None, optional: bool = True) -> list[dict[str, str]]:
    """Return explainable review signals without changing or rejecting text."""
    normalized = normalize_text(value)
    if not normalized:
        message = "Поле необов’язкове й поки не заповнене." if optional else "Поле не заповнене."
        return [{"field_key": field_key, "label": label, "code": "empty", "message": message}]

    words = WORD_PATTERN.findall(normalized)
    warnings: list[dict[str, str]] = []
    if normalized.casefold() in PLACEHOLDERS:
        warnings.append({"field_key": field_key, "label": label, "code": "placeholder", "message": "Значення схоже на службовий placeholder; перевірте його перед завершенням роботи."})
    if len(words) <= SHORT_TEXT_WORDS:
        warnings.append({"field_key": field_key, "label": label, "code": "too_short", "message": "Текст дуже короткий; це сигнал для ручної перевірки, а не оцінка якості."})
    if _is_repetitive(words):
        warnings.append({"field_key": field_key, "label": label, "code": "repetition", "message": "Текст містить надмірне повторення; перевірте, чи це не помилка введення."})
    if non_whitespace_char_count(normalized) > LONG_TEXT_CHARACTERS:
        warnings.append({"field_key": field_key, "label": label, "code": "very_long", "message": "Текст незвично великий; перевірте структуру та повноту передавання змісту."})
    return warnings


def check_report_narratives(*, identification_status: str, identification_method: str | None, identification_conclusion: str | None, expert_comment: str | None) -> list[dict[str, str]]:
    warnings = [
        *check_text(field_key="identification_method", label="Метод ідентифікації", value=identification_method),
        *check_text(field_key="identification_conclusion", label="Висновок щодо ідентифікації", value=identification_conclusion),
        *check_text(field_key="expert_comment", label="Коментар експерта", value=expert_comment),
    ]
    if identification_status == "confirmed" and not normalize_text(identification_conclusion):
        warnings.append({
            "field_key": "identification_conclusion",
            "label": "Висновок щодо ідентифікації",
            "code": "status_context",
            "message": "Для рівня «Підтверджено» варто додати текстовий висновок; це не блокує збереження.",
        })
    return warnings
