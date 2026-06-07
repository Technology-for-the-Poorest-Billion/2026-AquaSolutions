"""Build the two linked datasets:
  data/reports.csv                 (one row per DHIS2 illness report)
  data/labeled_water_readings.csv  (synthetic readings labelled by the partner)
Linked by station_id (+ the partner's 7-day window).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from etl import reports as R
from etl.labeller import label_readings
from etl.simulate import simulate_readings

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SEED = 7
PER_DAY = 1


def _parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "").split(".")[0])


def main():
    de_by_id, ou_by_id, symptom_names = R.load_maps()
    events = R.fetch_report_events()
    rows = [R.report_event_to_row(e, de_by_id, ou_by_id, symptom_names) for e in events]

    report_fields = ["event_id", "timestamp", "onset_date", "station_id", "borehole",
                     "neighbourhood", "case_count"] + [s.lower().replace(" ", "_") for s in symptom_names]
    R.write_csv(rows, report_fields, DATA_DIR / "reports.csv")
    print(f"wrote {len(rows)} reports -> {DATA_DIR/'reports.csv'}")

    # reports for the partner labeller: station_id + timestamp(datetime)
    reports_for_label = [{"station_id": r["station_id"], "timestamp": _parse_ts(r["timestamp"])}
                         for r in rows if r["station_id"] is not None]

    # simulate readings across the reports' date span, for the stations that reported
    if rows:
        dates = sorted(_parse_ts(r["timestamp"]).date() for r in rows)
        start, end = dates[0], dates[-1]
    else:
        from datetime import date
        start = end = date.today()
    station_ids = sorted({r["station_id"] for r in rows if r["station_id"] is not None})
    readings = simulate_readings(station_ids, start, end, per_day=PER_DAY, seed=SEED)

    labels = label_readings(readings, reports_for_label)
    label_by_id = {l["reading_id"]: l for l in labels}

    out = []
    for rd in readings:
        lab = label_by_id.get(rd["id"], {})
        out.append({
            "reading_id": rd["id"], "station_id": rd["station_id"],
            "timestamp": rd["timestamp"].isoformat(),
            "turbidity_ntu": rd["turbidity_ntu"], "ph": rd["ph"],
            "temperature_c": rd["temperature_c"], "rainfall_mm": rd["rainfall_mm"],
            "chlorine_mg_l": rd["chlorine_mg_l"],
            "score": lab.get("score"), "confidence": lab.get("confidence"),
            "label": lab.get("label", "unlabelled"),
            "unsafe": 1 if lab.get("label") == "at_risk" else 0,
        })
    water_fields = ["reading_id", "station_id", "timestamp", "turbidity_ntu", "ph",
                    "temperature_c", "rainfall_mm", "chlorine_mg_l",
                    "score", "confidence", "label", "unsafe"]
    R.write_csv(out, water_fields, DATA_DIR / "labeled_water_readings.csv")
    n_atrisk = sum(1 for o in out if o["label"] == "at_risk")
    print(f"wrote {len(out)} readings ({n_atrisk} at_risk) -> {DATA_DIR/'labeled_water_readings.csv'}")


if __name__ == "__main__":
    main()
