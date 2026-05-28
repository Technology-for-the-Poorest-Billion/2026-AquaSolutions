"""Tests for the cholera-pattern risk-tier estimator.

Spec: docs/superpowers/specs/2026-05-28-medical-gov-portal-design.md §5.
Rules in priority order: SEVERE, HIGH, MEDIUM, LOW (first match wins).
"""

from datetime import date, timedelta

import pytest

from estimator import estimate_risk_tier


TODAY = date.today()


# --- SEVERE rule -----------------------------------------------------------

def test_severe_textbook_cholera_pattern():
    tier, rationale = estimate_risk_tier(
        symptoms=["diarrhoea", "dehydration"],
        onset_date=TODAY - timedelta(days=2),
        case_count=4,
    )
    assert tier == "severe"
    assert "textbook" in rationale.lower() or "severe-cholera" in rationale.lower()


def test_severe_requires_recent_onset():
    """Same symptoms but onset >3 days ago → not SEVERE (falls to HIGH)."""
    tier, _ = estimate_risk_tier(
        symptoms=["diarrhoea", "dehydration"],
        onset_date=TODAY - timedelta(days=10),
        case_count=4,
    )
    assert tier != "severe"


def test_severe_requires_multiple_cases():
    """Even classic symptom pattern with case_count=1 is not SEVERE."""
    tier, _ = estimate_risk_tier(
        symptoms=["diarrhoea", "dehydration"],
        onset_date=TODAY,
        case_count=1,
    )
    assert tier != "severe"


# --- HIGH rule -------------------------------------------------------------

def test_high_three_symptoms():
    tier, _ = estimate_risk_tier(
        symptoms=["diarrhoea", "vomiting", "fever"],
        onset_date=None,
        case_count=1,
    )
    assert tier == "high"


def test_high_outbreak_scale_multi_symptom():
    tier, _ = estimate_risk_tier(
        symptoms=["vomiting", "fever"],
        onset_date=None,
        case_count=8,
    )
    assert tier == "high"


def test_high_recent_diarrhoea():
    tier, _ = estimate_risk_tier(
        symptoms=["diarrhoea"],
        onset_date=TODAY - timedelta(days=1),
        case_count=1,
    )
    assert tier == "high"


# --- MEDIUM rule -----------------------------------------------------------

def test_medium_one_symptom():
    tier, rationale = estimate_risk_tier(
        symptoms=["fever"],
        onset_date=None,
        case_count=1,
    )
    assert tier == "medium"
    assert "1" in rationale or "non-specific" in rationale.lower()


def test_medium_two_symptoms_no_recent_onset():
    tier, _ = estimate_risk_tier(
        symptoms=["vomiting", "fever"],
        onset_date=None,
        case_count=1,
    )
    assert tier == "medium"


# --- LOW rule --------------------------------------------------------------

def test_low_no_symptoms():
    tier, rationale = estimate_risk_tier(
        symptoms=[],
        onset_date=None,
        case_count=1,
    )
    assert tier == "low"
    assert "no symptoms" in rationale.lower() or "clinical assessment" in rationale.lower()


# --- Defensive handling ---------------------------------------------------

def test_future_onset_date_treated_as_none():
    """Future onset_date should not satisfy the 'recent onset' rule."""
    tier, _ = estimate_risk_tier(
        symptoms=["diarrhoea", "dehydration"],
        onset_date=TODAY + timedelta(days=5),
        case_count=4,
    )
    # Without recent onset, SEVERE rule fails; falls through.
    assert tier != "severe"


def test_zero_case_count_treated_as_one():
    """case_count=0 should not trigger the multi-case rules."""
    tier, _ = estimate_risk_tier(
        symptoms=["vomiting"],
        onset_date=None,
        case_count=0,
    )
    assert tier == "medium"  # 1 symptom → MEDIUM, not HIGH


def test_negative_case_count_treated_as_one():
    tier, _ = estimate_risk_tier(
        symptoms=[],
        onset_date=None,
        case_count=-5,
    )
    assert tier == "low"


def test_unknown_symptoms_ignored():
    """Unknown symptom names should not be counted."""
    tier, _ = estimate_risk_tier(
        symptoms=["unknown_thing", "another_one"],
        onset_date=None,
        case_count=1,
    )
    assert tier == "low"


# --- Output contract -------------------------------------------------------

@pytest.mark.parametrize("symptoms,onset,cases", [
    ([], None, 1),
    (["fever"], None, 1),
    (["diarrhoea", "vomiting", "fever"], None, 1),
    (["diarrhoea", "dehydration"], TODAY, 5),
])
def test_returns_tuple_of_str(symptoms, onset, cases):
    tier, rationale = estimate_risk_tier(symptoms=symptoms, onset_date=onset, case_count=cases)
    assert tier in ("low", "medium", "high", "severe")
    assert isinstance(rationale, str)
    assert len(rationale) > 0
