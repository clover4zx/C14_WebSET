"""
data/scan_history_data.py
Where the Scan History page (and the Dashboard's Recent Scans table) gets
its list of past scans.

This returns a few DUMMY sample scans PLUS every real scan the app has run.
Real scans are recorded by the Static/Dynamic tabs via add_scan_result()
and saved to scan_history_store.json next to this file, so they survive
closing and re-opening the app.

Each scan has the same keys so the Scan History page never changes:
    id, target, date, scan_type, profile, status, duration, severity, error?
"""

import datetime
import json
from pathlib import Path

# Real scans are saved here so history persists between runs.
_STORE_PATH = Path(__file__).parent / "scan_history_store.json"

# Each scan:
#   id          short unique id shown in the table
#   target      URL (or file) that was scanned
#   date        when it started (display text)
#   scan_type   "Static" or "Dynamic"
#   profile     "Quick", "Standard" or "Thorough" (or a short label)
#   status      "Completed", "Running" or "Failed"
#   duration    how long it took (display text), "" if still running
#   severity    findings per severity level (Critical/High/Medium/Low)
#   error       why it failed (only for Failed scans)
_DUMMY_SCANS = [
    {"id": "WS-012", "target": "http://dvwa.local/vulnerabilities/sqli", "date": "09/10/2026 7:42 pm",
     "scan_type": "Dynamic", "profile": "Thorough", "status": "Running", "duration": "",
     "severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}},
    {"id": "WS-011", "target": "http://juiceshop.local:3000", "date": "09/10/2026 4:15 pm",
     "scan_type": "Static", "profile": "Standard", "status": "Completed", "duration": "2m 14s",
     "severity": {"Critical": 1, "High": 2, "Medium": 3, "Low": 1}},
    {"id": "WS-010", "target": "http://dvwa.local/login.php", "date": "08/10/2026 11:03 am",
     "scan_type": "Static", "profile": "Quick", "status": "Completed", "duration": "48s",
     "severity": {"Critical": 0, "High": 1, "Medium": 2, "Low": 1}},
    {"id": "WS-009", "target": "http://juiceshop.local:3000/#/login", "date": "07/10/2026 3:27 pm",
     "scan_type": "Dynamic", "profile": "Standard", "status": "Failed", "duration": "12s",
     "severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
     "error": "Target unreachable (connection timed out after 10s)."},
    {"id": "WS-008", "target": "http://dvwa.local", "date": "06/10/2026 9:50 am",
     "scan_type": "Static", "profile": "Standard", "status": "Completed", "duration": "1m 37s",
     "severity": {"Critical": 1, "High": 1, "Medium": 2, "Low": 1}},
    {"id": "WS-007", "target": "http://juiceshop.local:3000/rest/products/search", "date": "02/10/2026 2:10 pm",
     "scan_type": "Dynamic", "profile": "Thorough", "status": "Completed", "duration": "6m 05s",
     "severity": {"Critical": 2, "High": 2, "Medium": 1, "Low": 0}},
    {"id": "WS-006", "target": "http://dvwa.local/vulnerabilities/xss_r", "date": "29/09/2026 10:30 am",
     "scan_type": "Dynamic", "profile": "Standard", "status": "Completed", "duration": "3m 41s",
     "severity": {"Critical": 1, "High": 1, "Medium": 1, "Low": 1}},
    {"id": "WS-005", "target": "http://juiceshop.local:3000", "date": "25/09/2026 4:45 pm",
     "scan_type": "Static", "profile": "Thorough", "status": "Completed", "duration": "4m 02s",
     "severity": {"Critical": 0, "High": 1, "Medium": 1, "Low": 2}},
    {"id": "WS-004", "target": "http://dvwa.local/vulnerabilities/upload", "date": "22/09/2026 1:15 pm",
     "scan_type": "Static", "profile": "Quick", "status": "Completed", "duration": "52s",
     "severity": {"Critical": 0, "High": 1, "Medium": 1, "Low": 0}},
    {"id": "WS-003", "target": "http://juiceshop.local:3000/ftp", "date": "18/09/2026 11:20 am",
     "scan_type": "Static", "profile": "Quick", "status": "Completed", "duration": "39s",
     "severity": {"Critical": 0, "High": 0, "Medium": 1, "Low": 1}},
    {"id": "WS-002", "target": "http://dvwa.local", "date": "15/09/2026 3:05 pm",
     "scan_type": "Static", "profile": "Standard", "status": "Completed", "duration": "1m 20s",
     "severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 1}},
    {"id": "WS-001", "target": "http://dvwa.local", "date": "11/09/2026 9:00 am",
     "scan_type": "Static", "profile": "Quick", "status": "Completed", "duration": "30s",
     "severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}},
]


# --------------------------------------------------------------------------- #
# Saving / loading real scans
# --------------------------------------------------------------------------- #

def _load_real_scans() -> list:
    try:
        if _STORE_PATH.exists():
            return json.loads(_STORE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        pass
    return []


def _save_real_scans(scans: list) -> None:
    try:
        _STORE_PATH.write_text(json.dumps(scans, indent=2))
    except OSError:
        pass


def _next_id(existing: list) -> str:
    """Next WS-### id, above both the samples and the real scans so far."""
    numbers = []
    for scan in existing:
        sid = scan.get("id", "")
        if sid.startswith("WS-") and sid[3:].isdigit():
            numbers.append(int(sid[3:]))
    nxt = (max(numbers) + 1) if numbers else 13
    return f"WS-{nxt:03d}"


def _now_text() -> str:
    now = datetime.datetime.now()
    # e.g. "19/10/2026 7:42 pm"  (matches the sample format)
    return now.strftime("%d/%m/%Y ") + now.strftime("%I:%M %p").lstrip("0").lower()


def add_scan_result(result: dict, scan_type: str, target: str, profile: str = "") -> dict:
    """
    Record one finished scan in the history.

    result:    the envelope dict returned by webset_core (has ok, summary,
               total_findings, error).
    scan_type: "Static" or "Dynamic".
    target:    the URL or file name that was scanned.
    profile:   a short label (e.g. "Source ZIP", "Passive").
    """
    summary = result.get("summary", {}) or {}
    # Map the scanner's severities onto the history's buckets.
    # (The scanner has no "Critical"; its "INFO" findings are folded into Low.)
    severity = {
        "Critical": 0,
        "High": summary.get("HIGH", 0),
        "Medium": summary.get("MEDIUM", 0),
        "Low": summary.get("LOW", 0) + summary.get("INFO", 0),
    }

    real = _load_real_scans()
    record = {
        "id": _next_id(real + _DUMMY_SCANS),
        "target": target,
        "date": _now_text(),
        "scan_type": scan_type,
        "profile": profile or "—",
        "status": "Completed" if result.get("ok") else "Failed",
        "duration": "",
        "severity": severity,
    }
    if not result.get("ok"):
        record["error"] = result.get("error", "Scan failed.")

    real.append(record)
    _save_real_scans(real)
    return record


# --------------------------------------------------------------------------- #
# Reading the history
# --------------------------------------------------------------------------- #

def get_scan_history() -> list:
    """Every scan, newest first. Real scans (most recent at the top) come
    before the sample data. Each scan gets a "findings" total from its
    severity counts."""
    scans = []
    real_newest_first = list(reversed(_load_real_scans()))
    for scan in real_newest_first + _DUMMY_SCANS:
        scan = dict(scan)  # copy so the source lists never change
        scan["findings"] = sum(scan["severity"].values())
        scans.append(scan)
    return scans
