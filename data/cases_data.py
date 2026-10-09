"""
data/cases_data.py
Where the Cases page gets its cases from.

A "case" groups related findings about one target or issue, so the
team can track it from discovery through to fixing it. Each finding
includes its OWASP Top 10 (2021) category and a remediation step.

Right now this uses DUMMY data kept in memory. Changing a case's status
works while the app is open but resets when it restarts. When the
SQLite database is ready, replace the bodies of these functions with
real queries; the Cases page won't need to change.
"""

import copy
from datetime import date

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]
CASE_STATUSES = ["Open", "In Progress", "Resolved"]

# Each case:
#   id, title, target, status, assignee, created, updated
#   scans        ids of the scans that found these issues (see scan_history_data.py)
#   description  short summary of the case
#   findings     list of {title, severity, owasp, remediation}
_DUMMY_CASES = [
    {
        "id": "CS-007", "title": "SQL injection in DVWA",
        "target": "http://dvwa.local", "status": "Open", "assignee": "Oliver",
        "created": "08/10/2026", "updated": "09/10/2026", "scans": ["WS-008", "WS-010"],
        "description": "User input reaches database queries without sanitisation, "
                       "allowing attackers to read or modify stored data.",
        "findings": [
            {"title": "SQL injection in 'id' parameter (/vulnerabilities/sqli)", "severity": "Critical",
             "owasp": "A03:2021 Injection",
             "remediation": "Use parameterised queries (prepared statements) instead of building SQL from user input."},
            {"title": "Missing CSRF token on login form", "severity": "Medium",
             "owasp": "A01:2021 Broken Access Control",
             "remediation": "Add a per-session anti-CSRF token to every state-changing form and verify it server-side."},
            {"title": "Session cookie missing HttpOnly flag", "severity": "Low",
             "owasp": "A05:2021 Security Misconfiguration",
             "remediation": "Set the HttpOnly and Secure flags on the session cookie."},
        ],
    },
    {
        "id": "CS-006", "title": "Juice Shop authentication weaknesses",
        "target": "http://juiceshop.local:3000", "status": "Open", "assignee": "Andy",
        "created": "09/10/2026", "updated": "09/10/2026", "scans": ["WS-011"],
        "description": "Several weaknesses in the login process allow an attacker to "
                       "access accounts, including the administrator account.",
        "findings": [
            {"title": "Admin login bypass via SQL injection in email field", "severity": "Critical",
             "owasp": "A03:2021 Injection",
             "remediation": "Use parameterised queries in the login handler and validate the email format."},
            {"title": "JWT signed with a weak, guessable secret", "severity": "High",
             "owasp": "A02:2021 Cryptographic Failures",
             "remediation": "Use a long random signing secret (or asymmetric keys) and rotate it."},
            {"title": "Weak password policy allows short passwords", "severity": "Medium",
             "owasp": "A07:2021 Identification and Authentication Failures",
             "remediation": "Require a minimum length of 12 characters and check against breached-password lists."},
        ],
    },
    {
        "id": "CS-005", "title": "Reflected XSS in DVWA",
        "target": "http://dvwa.local/vulnerabilities/xss_r", "status": "In Progress", "assignee": "Oliver",
        "created": "29/09/2026", "updated": "06/10/2026", "scans": ["WS-006"],
        "description": "User input is reflected into the page without encoding, so "
                       "attackers can run scripts in a victim's browser.",
        "findings": [
            {"title": "Reflected XSS in 'name' parameter", "severity": "High",
             "owasp": "A03:2021 Injection",
             "remediation": "HTML-encode all user input before writing it into the page."},
            {"title": "Missing Content-Security-Policy header", "severity": "Medium",
             "owasp": "A05:2021 Security Misconfiguration",
             "remediation": "Add a Content-Security-Policy header that blocks inline scripts."},
        ],
    },
    {
        "id": "CS-004", "title": "Exposed files on Juice Shop FTP folder",
        "target": "http://juiceshop.local:3000/ftp", "status": "Open", "assignee": "Andy",
        "created": "18/09/2026", "updated": "02/10/2026", "scans": ["WS-003", "WS-005"],
        "description": "The /ftp folder is publicly browsable and contains internal "
                       "business documents.",
        "findings": [
            {"title": "Confidential document publicly accessible (acquisitions.md)", "severity": "High",
             "owasp": "A01:2021 Broken Access Control",
             "remediation": "Remove sensitive files from the web root and require authentication for internal documents."},
            {"title": "Directory listing enabled on /ftp", "severity": "Medium",
             "owasp": "A05:2021 Security Misconfiguration",
             "remediation": "Disable directory listing in the web server configuration."},
        ],
    },
    {
        "id": "CS-003", "title": "Unrestricted file upload in DVWA",
        "target": "http://dvwa.local/vulnerabilities/upload", "status": "In Progress", "assignee": "Oliver",
        "created": "22/09/2026", "updated": "30/09/2026", "scans": ["WS-004"],
        "description": "The upload form accepts any file type, so an attacker could "
                       "upload and run server-side code.",
        "findings": [
            {"title": "Upload accepts executable .php files", "severity": "High",
             "owasp": "A04:2021 Insecure Design",
             "remediation": "Allow-list safe file types, rename uploads, and store them outside the web root."},
        ],
    },
    {
        "id": "CS-002", "title": "Missing security headers on DVWA",
        "target": "http://dvwa.local", "status": "Resolved", "assignee": "Andy",
        "created": "15/09/2026", "updated": "22/09/2026", "scans": ["WS-002"],
        "description": "Responses were missing headers that protect against "
                       "clickjacking.",
        "findings": [
            {"title": "Missing X-Frame-Options header", "severity": "Low",
             "owasp": "A05:2021 Security Misconfiguration",
             "remediation": "Add 'X-Frame-Options: DENY' (or a CSP frame-ancestors rule) to all responses."},
        ],
    },
    {
        "id": "CS-001", "title": "Outdated JavaScript library on Juice Shop",
        "target": "http://juiceshop.local:3000", "status": "Resolved", "assignee": "Oliver",
        "created": "25/09/2026", "updated": "01/10/2026", "scans": ["WS-005"],
        "description": "The site loads an old library version with publicly known "
                       "vulnerabilities.",
        "findings": [
            {"title": "Outdated jQuery version (2.2.4)", "severity": "Medium",
             "owasp": "A06:2021 Vulnerable and Outdated Components",
             "remediation": "Upgrade to the latest supported jQuery release and track dependencies."},
        ],
    },
]


def get_cases() -> list:
    """Every case, newest first. Each case also gets:
        findings_count  how many findings it groups
        severity        its highest finding severity (e.g. "Critical")
    """
    # TODO (backend): SELECT ... FROM cases ORDER BY created DESC (+ their findings)
    cases = copy.deepcopy(_DUMMY_CASES)   # copy, so pages can't change the dummy data by accident
    for case in cases:
        case["findings_count"] = len(case["findings"])
        severities = [finding["severity"] for finding in case["findings"]]
        case["severity"] = next((level for level in SEVERITY_ORDER if level in severities), "Low")
    return cases


def get_case_status_counts() -> dict:
    """How many cases are in each status, e.g. {"Open": 3, "In Progress": 2, "Resolved": 2}."""
    counts = {status: 0 for status in CASE_STATUSES}
    for case in get_cases():
        counts[case["status"]] = counts.get(case["status"], 0) + 1
    return counts


def update_case_status(case_id: str, new_status: str):
    """Change a case's status (e.g. "Open" -> "In Progress")."""
    # TODO (backend): UPDATE cases SET status = ?, updated = now WHERE id = ?
    for case in _DUMMY_CASES:
        if case["id"] == case_id:
            case["status"] = new_status
            case["updated"] = date.today().strftime("%d/%m/%Y")
            return