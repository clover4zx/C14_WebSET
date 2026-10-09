"""
data/dashboard_data.py
Where the Dashboard gets its numbers from.

Right now every function returns DUMMY data so the UI can be built and
tested. When the scanner and SQLite database are ready, replace the
body of each function with real queries — the Dashboard page doesn't
need to change at all, as long as the same shape of data is returned.

The dummy numbers are kept consistent with each other (e.g. the
severity counts add up to the "Vulnerabilities Found" card) so the
demo looks believable.
"""

from data.cases_data import get_case_status_counts
from data.scan_history_data import get_scan_history



def get_dashboard_summary() -> dict:
    """Numbers for the four summary cards.

    Keys must match the keys in SUMMARY_CARDS in pages/dashboard_page.py.
    """
    # TODO (backend): replace with real values, e.g.
    #   SELECT COUNT(*) FROM scans
    #   SELECT COUNT(*) FROM findings
    #   SELECT COUNT(*) FROM findings WHERE severity = 'critical'
    #   SELECT COUNT(*) FROM cases WHERE status = 'open'
    return {
        "total_scans": 12,
        "vulnerabilities": 34,
        "critical": 5,
        "open_cases": get_case_status_counts()["Open"],   # live from the Cases page
    }


def get_findings_by_severity() -> dict:
    """How many findings there are at each severity level.

    Must return these four keys, in this order: Critical, High, Medium, Low.
    """
    # TODO (backend): SELECT severity, COUNT(*) FROM findings GROUP BY severity
    return {
        "Critical": 5,
        "High": 9,
        "Medium": 12,
        "Low": 8,
    }


def get_activity_over_time() -> dict:
    """Scans run and findings discovered per week, oldest week first.

    Returns:
        {
            "labels": ["W1", "W2", ...],         # x-axis labels
            "series": {
                "Scans": [ ... one number per label ... ],
                "Findings": [ ... one number per label ... ],
            },
        }
    """
    # TODO (backend): group scans/findings by week using their timestamps
    return {
        "labels": ["W5", "W6", "W7", "W8", "W9", "W10", "W11", "W12"],
        "series": {
            "Scans": [0, 1, 1, 2, 1, 2, 2, 3],
            "Findings": [0, 2, 3, 6, 4, 7, 5, 7],
        },
    }


def get_recent_scans(limit: int = 5) -> list:
    """The most recent scans, newest first.

    Uses the same list as the Scan History page, so the two always agree.
    Each scan is a dict with (at least): target, date, scan_type, status, findings.
    """
    return get_scan_history()[:limit]