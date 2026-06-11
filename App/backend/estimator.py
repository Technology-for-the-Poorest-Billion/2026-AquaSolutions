"""Risk-tier estimator (cholera-pattern heuristic).

Spec: docs/superpowers/specs/2026-05-28-medical-gov-portal-design.md §5.

Pure function. No DB access. Idempotent. Re-evaluated at render time
on the government detail page when the reporter did not supply a tier.

NOT a medical-advice system. The tier reflects 'does this symptom pattern
match the disease we are watching for' — not a diagnosis. The detail page
always renders an explicit 'estimated heuristic — not medical advice'
banner when this function's output is shown.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from flask_babel import gettext as _, ngettext

KNOWN_SYMPTOMS = {"diarrhoea", "vomiting", "fever", "dehydration"}
RECENT_ONSET_DAYS = 3


def _normalise(
    symptoms: Iterable[str],
    onset_date: date | None,
    case_count: int,
) -> tuple[set[str], date | None, int]:
    """Defensive input handling — see spec §5 'Defensive handling'."""
    canonical = {s for s in symptoms if isinstance(s, str)} & KNOWN_SYMPTOMS
    today = date.today()
    safe_onset = onset_date if (isinstance(onset_date, date) and onset_date <= today) else None
    safe_cases = case_count if (isinstance(case_count, int) and case_count >= 1) else 1
    return canonical, safe_onset, safe_cases


def _is_recent(onset_date: date | None) -> bool:
    if onset_date is None:
        return False
    return (date.today() - onset_date) <= timedelta(days=RECENT_ONSET_DAYS)


def estimate_risk_tier(
    symptoms: Iterable[str],
    onset_date: date | None,
    case_count: int,
) -> tuple[str, str]:
    """Return (tier, rationale). tier ∈ {'low','medium','high','severe'}."""
    syms, onset, cases = _normalise(symptoms, onset_date, case_count)
    recent = _is_recent(onset)

    # 1. SEVERE — textbook severe-cholera pattern
    if (
        "diarrhoea" in syms
        and "dehydration" in syms
        and recent
        and cases >= 3
    ):
        return ("severe",
                _("textbook severe-cholera pattern (diarrhoea + dehydration + "
                  "recent onset + multiple cases)"))

    # 2. HIGH — three sub-rules, ORed
    if len(syms) >= 3:
        return ("high", _("3+ symptoms reported"))
    if cases >= 5 and len(syms) >= 2:
        return ("high", _("outbreak-scale case count (≥5) with multiple symptoms"))
    if "diarrhoea" in syms and recent:
        return ("high", _("recent-onset diarrhoea"))

    # 3. MEDIUM — uses ngettext for the count
    if 1 <= len(syms) <= 2:
        n = len(syms)
        return ("medium", ngettext("%(num)d non-specific symptom reported",
                                   "%(num)d non-specific symptoms reported", n))

    # 4. LOW — fallthrough
    return ("low", _("no symptoms reported — request clinical assessment regardless"))
