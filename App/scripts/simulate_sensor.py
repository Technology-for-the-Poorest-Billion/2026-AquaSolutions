"""Simulate field sensor nodes by POSTing readings to /ingest.

Usage
-----
    python App/scripts/simulate_sensor.py
    python App/scripts/simulate_sensor.py --url https://gm2aquasolutions-production-aff9.up.railway.app \
        --secret my-device-secret --stations 1,2,3,4 --interval 5

The script POSTs one randomised-but-plausible reading per station per
``--interval`` seconds. Pre-seeded stations are 1..4 (see ``database.py``).

Reading distributions are loose physical defaults — pH around 7,
turbidity 0–50 NTU, temp 18–28 °C, rainfall 0 most of the time with
occasional spikes. Not calibrated to any specific borehole.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import datetime, timezone

import urllib.error
import urllib.request
import json


def _reading_for(station_id: int) -> dict:
    """Generate a plausible reading for one station."""
    rain = 0.0 if random.random() > 0.15 else round(random.uniform(0.5, 12.0), 1)
    return {
        "station_id": station_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "ph": round(random.gauss(7.2, 0.4), 2),
        "turbidity_ntu": round(max(0.0, random.gauss(8.0, 6.0)), 1),
        "temperature_c": round(random.gauss(23.0, 2.0), 1),
        "rainfall_mm": rain,
        "provenance": "simulator_v1",
    }


def _post(url: str, secret: str, payload: dict) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Device-Secret": secret,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except urllib.error.URLError as e:
        return 0, str(e)
    except (TimeoutError, OSError) as e:
        # Don't crash the simulator on a single slow Railway response;
        # report and move on to the next station / round.
        return 0, f"timeout/network: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://gm2aquasolutions-production-aff9.up.railway.app",
                        help="Base URL of the Flask app (default Railway production)")
    parser.add_argument("--secret", default=os.environ.get("DEVICE_SECRET", ""),
                        help="Shared secret matching DEVICE_SECRET in .env")
    parser.add_argument("--stations", default="1,2,3,4,5,6,7,8,9,10",
                        help="Comma-separated station IDs to simulate")
    parser.add_argument("--interval", type=float, default=5.0,
                        help="Seconds between rounds of POSTs")
    parser.add_argument("--once", action="store_true",
                        help="Send one round and exit (useful for tests)")
    args = parser.parse_args()

    if not args.secret:
        print("error: --secret is required (or set DEVICE_SECRET in env)",
              file=sys.stderr)
        return 2

    ingest_url = args.url.rstrip("/") + "/ingest"
    station_ids = [int(s.strip()) for s in args.stations.split(",") if s.strip()]

    print(f"Simulating stations {station_ids} -> {ingest_url} "
          f"every {args.interval}s. Ctrl-C to stop.")

    try:
        while True:
            for station_id in station_ids:
                payload = _reading_for(station_id)
                status, body = _post(ingest_url, args.secret, payload)
                ts = payload["recorded_at"]
                marker = "OK " if status in (200, 201) else "ERR"
                summary = (
                    f"pH={payload['ph']} turb={payload['turbidity_ntu']} "
                    f"temp={payload['temperature_c']} rain={payload['rainfall_mm']}"
                )
                print(f"[{ts}] {marker} station={station_id} status={status} {summary}")
                if status not in (200, 201):
                    print(f"    body: {body[:200]}")
            if args.once:
                return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
