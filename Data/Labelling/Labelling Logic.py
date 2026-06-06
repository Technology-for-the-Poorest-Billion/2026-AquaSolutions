import math
from datetime import datetime, timedelta
from typing import List, Optional
 
 
# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
 
WINDOW_DAYS = 7          # Reports older than this contribute 0
LOG_BASE = WINDOW_DAYS + 1  # = 8; gives decay of exactly 0 at t = WINDOW_DAYS
 
# Confidence tier bin boundaries
TIER_UNLABELLED_MAX = 0.5
TIER_LOW_MAX = 1.5
TIER_MED_MAX = 2.5
 
# Confidence values
CONFIDENCE_UNLABELLED = None   # No label assigned
CONFIDENCE_LOW = 0.3
CONFIDENCE_MED = 0.6
CONFIDENCE_HIGH = 0.9
 
 
# ---------------------------------------------------------------------------
# Core decay function
# ---------------------------------------------------------------------------
 
def report_decay_score(report_timestamp: datetime, reading_timestamp: datetime) -> float:
  
    delta = reading_timestamp - report_timestamp
    t = delta.total_seconds() / 86400.0  # fractional days
 
    if t < 0 or t >= WINDOW_DAYS:
        # Report is in the future relative to this reading, or outside the window
        return 0.0
 
    score = 1.0 * (1.0 - math.log(t + 1) / math.log(LOG_BASE))
    return max(0.0, score)  # numerical safety clamp
 
 
# ---------------------------------------------------------------------------
# Score aggregation
# ---------------------------------------------------------------------------
 
def aggregate_report_score(
    report_timestamps: List[datetime],
    reading_timestamp: datetime):
    
    return sum(
        report_decay_score(rt, reading_timestamp)
        for rt in report_timestamps)
 
 
# ---------------------------------------------------------------------------
# Confidence binning
# ---------------------------------------------------------------------------
 
def score_to_confidence(score: float) -> Optional[float]:
   
    if score < TIER_UNLABELLED_MAX:
        return CONFIDENCE_UNLABELLED
    elif score < TIER_LOW_MAX:
        return CONFIDENCE_LOW
    elif score < TIER_MED_MAX:
        return CONFIDENCE_MED
    else:
        return CONFIDENCE_HIGH
 
 
# ---------------------------------------------------------------------------
# Top-level labelling function
# ---------------------------------------------------------------------------
 
def compute_label(
    report_timestamps: List[datetime],
    reading_timestamp: datetime) -> dict:

    score = aggregate_report_score(report_timestamps, reading_timestamp)
    confidence = score_to_confidence(score)
 
    return {
        "label": "at_risk" if confidence is not None else "unlabelled",
        "confidence": confidence,
        "score": round(score, 4),
}
 
 
# ---------------------------------------------------------------------------
# Batch labelling (for use against a database export or CSV)
# ---------------------------------------------------------------------------
 
def label_readings(readings: List[dict], reports: List[dict]) -> List[dict]:

    # Index reports by station for efficient lookup
    from collections import defaultdict
    reports_by_station = defaultdict(list)
    for r in reports:
        reports_by_station[r["station_id"]].append(r["timestamp"])
 
    results = []
    for reading in readings:
        station_reports = reports_by_station.get(reading["station_id"], [])
        result = compute_label(station_reports, reading["timestamp"])
        results.append({
            "reading_id":  reading["id"],
            "station_id":  reading["station_id"],
            "timestamp":   reading["timestamp"],
            **result,
        })
 
    return results
 
 
# ---------------------------------------------------------------------------
# Quick sanity check (run this file directly to verify)
# ---------------------------------------------------------------------------
 
if __name__ == "__main__":
    now = datetime(2024, 6, 1, 12, 0, 0)
 
    scenarios = [
        ("No reports",             []),
        ("1 report, just now",     [now - timedelta(hours=1)]),
        ("1 report, 3 days ago",   [now - timedelta(days=3)]),
        ("1 report, 6.9 days ago", [now - timedelta(days=6, hours=23)]),
        ("1 report, 7+ days ago",  [now - timedelta(days=8)]),
        ("2 reports, both fresh",  [now - timedelta(hours=2), now - timedelta(hours=6)]),
        ("3 reports, all fresh",   [now - timedelta(hours=1),
                                    now - timedelta(hours=3),
                                    now - timedelta(hours=5)]),
        ("3 reports, spread out",  [now - timedelta(days=1),
                                    now - timedelta(days=3),
                                    now - timedelta(days=5)]),
    ]
 
    print(f"{'Scenario':<35} {'Score':>6}  {'Confidence':>10}  {'Label'}")
    print("-" * 70)
    for name, report_times in scenarios:
        result = compute_label(report_times, now)
        conf = str(result["confidence"]) if result["confidence"] else "None"
        print(f"{name:<35} {result['score']:>6.3f}  {conf:>10}  {result['label']}")