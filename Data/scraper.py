#!/usr/bin/env python3
"""
DWS NMMP E. coli + Physical/Chemical Dataset Scraper
====================================================

Scrapes the South African DWS National Microbiological Monitoring Programme
(NMMP) bi-monthly reports from https://www.dws.gov.za/iwqs/microbio/report/WMA2012/
and combines them into a CSV suitable for training a (TinyML) classifier.

Each NMMP report row contains:
  - Site ID, name, sample date
  - E. coli (MPN or cfu / 100mL)
  - Faecal coliforms (MPN or cfu / 100mL)
  - Turbidity (NTU)  -- physical
  - pH               -- chemical
  - Temperature (oC) -- physical (very sparse: ~3% of rows)
  - Four risk class labels (HIGH/Med/low) for drinking, recreation, irrigation

Usage:
    python scrape_dws_nmmp.py --years 1990-2024 --out dataset.csv

By default scrapes 2020-2024 across all Water Management Areas (WMAs), then
filters to rows with BOTH turbidity and pH present. The full unfiltered raw
data is also written to <out_stem>_raw.csv for reference.

Requires: Python 3.8+, requests, beautifulsoup4
    pip install requests beautifulsoup4

Notes:
  - Be courteous: the script sleeps 1 second between requests by default.
  - The DWS server occasionally returns 5xx errors. The script retries up to 3 times.
  - Index pages list WMA links per period. Greyed-out (plain text) entries mean
    no report exists for that WMA-period combination; these are skipped.
"""

from __future__ import annotations
import argparse
import csv
import re
import sys
import time
from dataclasses import dataclass, asdict
from typing import Iterable
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Missing dependency. Run: pip install requests beautifulsoup4")


BASE = "https://www.dws.gov.za/iwqs/microbio/report/WMA2012"
INDEX_URL = f"{BASE}/index.aspx"
YEAR_URL = f"{BASE}/NMMPkey_{{year}}.htm"

REPORT_RE = re.compile(
    r"coli_(?P<wma>[A-Za-z_]+)_NMMP_(?P<ps>\d{4}-\d{2}-\d{2})_(?P<pe>\d{4}-\d{2}-\d{2})\.htm"
)

USER_AGENT = "DWS-NMMP-scraper/1.0 (data science / research)"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

FIELDS = [
    "wma", "period_start", "period_end",
    "site_id", "site_name", "date",
    "ecoli_per_100ml", "faecal_coliforms_per_100ml",
    "turbidity_ntu", "ph", "temperature_c",
    "risk_drinking_no_treatment", "risk_drinking_limited_treatment",
    "risk_contact", "risk_irrigation_raw",
]


@dataclass
class Record:
    wma: str
    period_start: str
    period_end: str
    site_id: str | None
    site_name: str | None
    date: str
    ecoli_per_100ml: float | None
    faecal_coliforms_per_100ml: float | None
    turbidity_ntu: float | None
    ph: float | None
    temperature_c: float | None
    risk_drinking_no_treatment: str | None
    risk_drinking_limited_treatment: str | None
    risk_contact: str | None
    risk_irrigation_raw: str | None


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def fetch(url: str, session: requests.Session, retries: int = 3,
          sleep_between: float = 1.0) -> str | None:
    """GET the URL, retry on 5xx errors. Returns body text or None on permanent failure."""
    last_err = None
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=30, headers={"User-Agent": USER_AGENT})
            if r.status_code == 200:
                return r.text
            if 500 <= r.status_code < 600:
                last_err = f"HTTP {r.status_code}"
                time.sleep(2 + attempt * 2)
                continue
            # 4xx: don't retry
            print(f"  HTTP {r.status_code} for {url}", file=sys.stderr)
            return None
        except requests.RequestException as e:
            last_err = str(e)
            time.sleep(2 + attempt * 2)
    print(f"  Giving up on {url}: {last_err}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Index discovery
# ---------------------------------------------------------------------------

def discover_report_urls(years: Iterable[int], session: requests.Session,
                          sleep_between: float) -> list[tuple[str, str, str, str]]:
    """For each year, fetch the index page and pull all report URLs.
    Returns a list of (wma, period_start, period_end, full_url) tuples."""
    urls: list[tuple[str, str, str, str]] = []
    for year in years:
        idx_url = YEAR_URL.format(year=year)
        print(f"Indexing {year}: {idx_url}")
        html = fetch(idx_url, session)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = REPORT_RE.search(href)
            if not m:
                continue
            full = urljoin(idx_url, href)
            urls.append((m["wma"], m["ps"], m["pe"], full))
        time.sleep(sleep_between)
    # De-duplicate while preserving order
    seen = set()
    out = []
    for tup in urls:
        if tup[3] not in seen:
            seen.add(tup[3])
            out.append(tup)
    return out


# ---------------------------------------------------------------------------
# Report parsing
# ---------------------------------------------------------------------------

def parse_value(s: str) -> float | None:
    s = s.strip()
    if s in ("", "-", "—", "–"):
        return None
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def extract_site_id_and_name(cell_html_text: str) -> tuple[str | None, str | None]:
    """Parse the Site column. It contains a numeric ID (4-12 digits) optionally
    wrapped in markup, plus a free-text name."""
    m = re.search(r"\b(\d{4,12})\b", cell_html_text)
    if not m:
        return None, None
    site_id = m.group(1)
    tail = cell_html_text[m.end():]
    # Remove any markdown-ish link leftovers like '](url)'
    tail = re.sub(r"\]\([^)]*\)", " ", tail)
    tail = re.sub(r"\[\[?[^\]]*\]\]?", " ", tail)
    tail = tail.replace("**", "").replace("[", " ").replace("]", " ")
    tail = " ".join(tail.split()).strip()
    tail = tail.lstrip("- :.,")
    return site_id, tail or None


def parse_report(html: str, wma: str, ps: str, pe: str) -> list[Record]:
    """Parse a single NMMP report HTML page into Record objects."""
    soup = BeautifulSoup(html, "html.parser")
    records: list[Record] = []
    current_site_id: str | None = None
    current_site_name: str | None = None

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        # The data table has 13 columns; check the first row.
        # Skip non-data tables.
        first_cells = rows[0].find_all(["th", "td"])
        if len(first_cells) < 8:
            continue
        # Iterate rows looking for valid data lines
        for tr in rows:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 13:
                continue
            cell_texts = [c.get_text(" ", strip=True) for c in cells]
            date = cell_texts[3].strip()
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
                continue
            site_text = cell_texts[1]
            sid, sname = extract_site_id_and_name(site_text)
            if sid:
                current_site_id = sid
                if sname:
                    current_site_name = sname
            if not current_site_id:
                continue
            records.append(Record(
                wma=wma,
                period_start=ps,
                period_end=pe,
                site_id=current_site_id,
                site_name=current_site_name,
                date=date,
                ecoli_per_100ml=parse_value(cell_texts[4]),
                faecal_coliforms_per_100ml=parse_value(cell_texts[5]),
                turbidity_ntu=parse_value(cell_texts[6]),
                ph=parse_value(cell_texts[7]),
                temperature_c=parse_value(cell_texts[8]),
                risk_drinking_no_treatment=cell_texts[9].strip() or None,
                risk_drinking_limited_treatment=cell_texts[10].strip() or None,
                risk_contact=cell_texts[11].strip() or None,
                risk_irrigation_raw=cell_texts[12].strip() or None,
            ))
    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_year_range(s: str) -> list[int]:
    """Accept '2020', '2020-2024', or '2020,2022,2024'."""
    if "-" in s:
        a, b = s.split("-", 1)
        return list(range(int(a), int(b) + 1))
    if "," in s:
        return [int(x) for x in s.split(",")]
    return [int(s)]


def write_csv(path: str, records: list[Record]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in records:
            w.writerow(asdict(r))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--years", default="1990-2024",
                   help="Year range, e.g. '1990-2024' or '2024' or '1990,2000,2024' (default: 1990-2024)")
    p.add_argument("--out", default="dataset.csv",
                   help="Output CSV path for the FILTERED dataset (default: dataset.csv)")
    p.add_argument("--filter", choices=["none", "ph", "ph+turb", "all3"],
                   default="ph+turb",
                   help="Which rows to keep in the filtered output: "
                        "none = everything; ph = rows with pH; "
                        "ph+turb = rows with pH AND turbidity (default); "
                        "all3 = rows with pH AND turbidity AND temperature")
    p.add_argument("--sleep", type=float, default=1.0,
                   help="Seconds to sleep between requests (default: 1.0)")
    p.add_argument("--limit", type=int, default=0,
                   help="Stop after fetching N report pages (0 = no limit, default)")
    args = p.parse_args()

    years = parse_year_range(args.years)
    print(f"Scraping NMMP reports for years: {years}")
    print(f"Filter: {args.filter}")
    print(f"Output: {args.out}")
    print()

    with requests.Session() as s:
        report_urls = discover_report_urls(years, s, args.sleep)
        print(f"Discovered {len(report_urls)} report URLs.")
        if args.limit:
            report_urls = report_urls[:args.limit]
            print(f"Limited to first {args.limit}.")
        print()

        all_records: list[Record] = []
        for i, (wma, ps, pe, url) in enumerate(report_urls, 1):
            print(f"[{i}/{len(report_urls)}] {wma:25s} {ps} -> {pe}")
            html = fetch(url, s)
            if not html:
                continue
            recs = parse_report(html, wma, ps, pe)
            all_records.extend(recs)
            print(f"   parsed {len(recs)} rows (running total: {len(all_records)})")
            time.sleep(args.sleep)

    # Apply filter
    def keep(r: Record) -> bool:
        if args.filter == "none":
            return True
        if args.filter == "ph":
            return r.ph is not None
        if args.filter == "ph+turb":
            return r.ph is not None and r.turbidity_ntu is not None
        if args.filter == "all3":
            return (r.ph is not None and r.turbidity_ntu is not None
                    and r.temperature_c is not None)
        return True

    filtered = [r for r in all_records if keep(r)]

    # Write filtered dataset
    write_csv(args.out, filtered)
    # Also write raw, unfiltered
    raw_path = args.out.replace(".csv", "_raw.csv")
    if raw_path == args.out:
        raw_path = args.out + "_raw.csv"
    write_csv(raw_path, all_records)

    print()
    print(f"Total rows parsed (raw):  {len(all_records)}")
    print(f"Rows kept after filter:   {len(filtered)}")
    print(f"Written: {args.out}  ({len(filtered)} rows)")
    print(f"Written: {raw_path}  ({len(all_records)} rows, unfiltered)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())