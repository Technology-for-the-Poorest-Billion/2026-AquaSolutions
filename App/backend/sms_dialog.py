"""Multi-turn SMS dialog parsers + state-machine helpers.

Spec: docs/superpowers/specs/2026-05-28-medical-gov-portal-design.md §8.

Pure parse functions return parsed values or None (re-prompt signal).
The state-machine step function is consumed by app.py's /sms route.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from typing import Iterable

SYMPTOM_BY_DIGIT = {
    "1": "diarrhoea",
    "2": "vomiting",
    "3": "fever",
    "4": "dehydration",
}
SYMPTOM_NAMES = set(SYMPTOM_BY_DIGIT.values())

INTEGER_RE = re.compile(r"-?\d+")
DDMM_RE = re.compile(r"^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$")


def parse_case_count(message: str) -> int | None:
    if not message:
        return None
    m = INTEGER_RE.search(message)
    if not m:
        return None
    try:
        n = int(m.group(0))
    except ValueError:
        return None
    if n < 1 or n > 200:
        return None
    return n


def parse_symptoms(message: str) -> list[str] | None:
    if not message:
        return None
    tokens = re.split(r"[\s,;]+", message.lower())
    seen: list[str] = []
    for token in tokens:
        token = token.strip()
        if token in SYMPTOM_BY_DIGIT:
            sym = SYMPTOM_BY_DIGIT[token]
        elif token in SYMPTOM_NAMES:
            sym = token
        else:
            continue
        if sym not in seen:
            seen.append(sym)
    return seen if seen else None


def parse_onset(message: str) -> date | None:
    if not message:
        return None
    text = message.strip().lower()
    today = date.today()
    if text == "today":
        return today
    if text == "yesterday":
        return today - timedelta(days=1)
    m = DDMM_RE.match(text)
    if not m:
        return None
    day_s, month_s, year_s = m.groups()
    try:
        day = int(day_s); month = int(month_s)
        if year_s is None:
            year = today.year
        else:
            year = int(year_s)
            if year < 100:
                year += 2000
        parsed = date(year, month, day)
    except ValueError:
        return None
    if parsed > today:
        return None
    return parsed
