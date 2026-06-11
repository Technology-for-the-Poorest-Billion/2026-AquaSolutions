"""Thin loader around the project partner's labelling logic. We import and call
their `label_readings()` UNCHANGED — the labelling scheme is partner-owned
(spec D15 / E4). The source file's name contains a space, so we load it by path.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

# App/dhis2/etl/labeller.py -> parents[3] is the repo root
_PARTNER_FILE = Path(__file__).resolve().parents[3] / "Data" / "Labelling" / "Labelling Logic.py"


def _load_partner_module():
    spec = importlib.util.spec_from_file_location("partner_labelling", str(_PARTNER_FILE))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load partner labelling logic at {_PARTNER_FILE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def label_readings(readings, reports):
    """Delegate to the partner's batch labeller. Returns their result verbatim:
    [{reading_id, station_id, timestamp, label, confidence, score}, ...]."""
    return _load_partner_module().label_readings(readings, reports)
