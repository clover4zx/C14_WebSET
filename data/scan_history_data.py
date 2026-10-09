"""
data/scan_history_data.py
Where the Scan History page gets its list of past scans.

Right now this returns DUMMY data. When the scanner saves scans to
SQLite, replace the body of get_scan_history() with a real query —
the Scan History page (and the Dashboard's Recent Scans table, which
reads from here too) won't need to change, as long as each scan has
the same keys.

The dummy data is consistent with the Dashboard: 12 scans in total,
34 findings, of which 5 are Critical / 9 High / 12 Medium / 8 Low.
"""

# Each scan:
#   id          short unique id shown in the table
#   target      URL that was scanned
#   date        when it started (display text for now)
#   scan_type   "Static" or "Dynamic"
#   profile     "Quick", "Standard" or "Thorough"
#   status      "Completed", "Running" or "Failed"
#   duration    how long it took (display text), "" if still running
#   severity    findings per severity level
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


def get_scan_history() -> list:
    """Every scan, newest first. Each scan also gets a "findings" key
    with its total number of findings (worked out from "severity")."""
    # TODO (backend): SELECT ... FROM scans ORDER BY started_at DESC
    scans = []
    for scan in _DUMMY_SCANS:
        scan = dict(scan)  # copy, so the dummy list itself never changes
        scan["findings"] = sum(scan["severity"].values())
        scans.append(scan)
    return scans