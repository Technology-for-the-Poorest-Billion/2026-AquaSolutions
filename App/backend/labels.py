"""Retrospective labelling of sensor readings from inbound illness reports.

When an SMS report arrives naming a station, we look back over a trailing
window of sensor readings at that station and label them as ``unsafe``.
This module owns that rule.

----------------------------------------------------------------------------
Why this is the most important decision in the pipeline
----------------------------------------------------------------------------

The window length encodes two unknowns at once:

  1. **Incubation lag.** Cholera incubation is hours to ~5 days. The
     reporter is symptomatic *now*, but the contaminated reading is in
     the past.
  2. **Reporting delay.** Reporters typically text 0–2 days after symptoms
     appear, not at the instant of exposure.

So the *true* exposure window is roughly (report_time - 7 days,
report_time - 6 hours). The default below uses 7 days as a single
flat window — defensible, simple, but not the only valid choice.

----------------------------------------------------------------------------
Trade-offs to consider when changing the rule
----------------------------------------------------------------------------

* **Window length.** Shorter (e.g. 3 days) gives sharper labels but misses
  long-incubation exposures. Longer (e.g. 14 days) catches more true
  positives but contaminates the negative class with stale readings.
* **Window anchor.** report_receipt vs an estimated exposure time
  (report_receipt - 2d for an assumed symptom onset, then further
  back for incubation). Estimated anchor is more biologically honest
  but introduces a hyperparameter the model could overfit to.
* **All-or-none vs graded confidence.** All-or-none ('unsafe') is what
  the default does. A graded label (confidence falling off with time)
  carries more information into the eventual model but complicates
  downstream code.
* **Multiple reports.** If two reporters name the same station in the
  same window, are the labels reinforced (raise confidence), or treated
  as one event (idempotent)? The default is idempotent via a
  UNIQUE(reading_id, report_id) constraint in the schema.

These trade-offs are the *meaningful student contribution* in this file.
The default below is a working baseline so the demo runs; the function
is structured so the rule can be swapped without touching ``app.py``.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection

DEFAULT_WINDOW_DAYS = 7
DEFAULT_LABEL = "unsafe"
RULE_VERSION = "trailing_7d_v1"


def label_readings_for_report(
    conn: Connection,
    report_id: int,
    station_id: int,
    report_time: datetime,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> int:
    """Label the trailing window of readings at ``station_id`` as unsafe.

    Returns the number of readings newly labelled. Idempotent via the
    UNIQUE(reading_id, report_id) constraint on reading_labels.
    """
    window_start = report_time - timedelta(days=window_days)

    target_readings = conn.execute(
        text(
            "SELECT reading_id FROM sensor_readings "
            "WHERE station_id = :sid "
            "  AND recorded_at >= :ws "
            "  AND recorded_at <= :rt"
        ),
        {
            "sid": station_id,
            "ws": window_start.isoformat(),
            "rt": report_time.isoformat(),
        },
    ).all()

    if not target_readings:
        return 0

    rule_description = (
        f"{RULE_VERSION}: trailing {window_days}d window at station "
        f"{station_id} anchored at report receipt"
    )

    inserted = 0
    for row in target_readings:
        result = conn.execute(
            text(
                "INSERT INTO reading_labels "
                "(reading_id, report_id, label, rule_description) "
                "VALUES (:rid, :rep, :label, :rule) "
                "ON CONFLICT (reading_id, report_id) DO NOTHING"
            ),
            {
                "rid": row.reading_id,
                "rep": report_id,
                "label": DEFAULT_LABEL,
                "rule": rule_description,
            },
        )
        inserted += result.rowcount

    return inserted


# ---------------------------------------------------------------------------
# STUDENT EXTENSION POINT
# ---------------------------------------------------------------------------
#
# The default rule above is intentionally simple. Three alternative rules
# worth implementing as you reason about label quality vs collected data:
#
#   1. **Estimated-exposure anchor.** Shift the window back by an assumed
#      symptom-onset delay (e.g. 2 days), so the window is
#      ``[report_time - 2d - 7d, report_time - 2d]``. Hyperparameter
#      becomes the (assumed_onset_delay, incubation_max) pair.
#
#   2. **Graded confidence.** Replace the flat 'unsafe' with a per-row
#      confidence that decays from the centre of the assumed exposure
#      window. Add a ``confidence REAL`` column to ``reading_labels``
#      (migrate the schema) and emit values in [0, 1].
#
#   3. **Multi-report reinforcement.** Track the number of distinct reports
#      pointing at the same reading; treat a station as 'confirmed unsafe'
#      only above a threshold (e.g. >=2 reports in 48h). Useful as a
#      dashboard signal that resists single-reporter abuse.
#
# Whichever rule you implement, bump ``RULE_VERSION`` so the audit trail
# distinguishes labels generated by different rules.
