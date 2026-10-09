"""
data/dashboard_data.py
Where the Dashboard gets its numbers from.

Right now this returns DUMMY data so the UI can be built and tested.
When the scanner and SQLite database are ready, replace the body of
get_dashboard_summary() with real queries — the Dashboard page doesn't
need to change at all, as long as the same keys are returned.
"""


def get_dashboard_summary() -> dict:
    """Return the numbers shown on the dashboard's summary cards.

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
        "open_cases": 3,
    }