"""
webset_core.py

WebSET - Integration layer (backend "glue").

This is the single entry point the frontend (your page files) should call.
Instead of the GUI needing to know how the static analyzer and the passive
scanner work internally, it just calls one of these functions and gets back
a predictable result it can display.

Both underlying scanners already return the SAME finding shape:
    severity, category, location, line, snippet, description, recommendation
...so this file mostly:
    1. Calls the right scanner.
    2. Catches errors so a bad URL or bad ZIP never crashes the GUI.
    3. Returns one consistent "envelope" the frontend can always trust.

This version expects your backend files to sit at the top level of the
project (loose, next to main.py), i.e.:

    C14_WebSET/
    |-- static_zip_analyzer.py     <- static scanner
    |-- passive_scanner.py         <- passive scanner
    |-- scan_profile.py
    |-- vulnerable_versions.py
    |-- webset_core.py             <- THIS FILE
    |-- main.py

Usage from the frontend:

    import webset_core

    result = webset_core.run_passive_scan("http://127.0.0.1:8000/")
    if result["ok"]:
        for f in result["findings"]:
            print(f["severity"], f["category"], f["location"])
    else:
        print("Scan failed:", result["error"])
"""

from __future__ import annotations

from typing import Dict, List, Optional

# Import the two scanners. This try/except is the same trick your other
# files use: it works both when this file is run directly
# (python pages/webset_core.py) AND when the PyQt app imports it as part of
# the `pages` package.
try:
    from .static_zip_analyzer import StaticZipAnalyzer, ZipSafetyError
    from .passive_scanner import PassiveScanner
    from .scan_profile import ScanProfile
except ImportError:
    from static_zip_analyzer import StaticZipAnalyzer, ZipSafetyError
    from passive_scanner import PassiveScanner
    from scan_profile import ScanProfile


# --------------------------------------------------------------------------- #
# A consistent "envelope" so the frontend always gets the same keys back,
# whether the scan succeeded or failed.
# --------------------------------------------------------------------------- #

def _empty_summary() -> Dict[str, int]:
    return {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}


def _ok_envelope(report: Dict, scan_type: str) -> Dict:
    """Wrap a successful scanner report in the shared envelope."""
    return {
        "ok": True,
        "error": None,
        "scan_type": scan_type,
        "target": report.get("target", ""),
        "summary": report.get("summary", _empty_summary()),
        "total_findings": report.get("total_findings", 0),
        "findings": report.get("findings", []),
        # Anything scanner-specific (tech_stack, dependencies, status_code...)
        # is passed through here so the GUI can show it if it wants to.
        "meta": {
            k: v for k, v in report.items()
            if k not in {"summary", "total_findings", "findings", "target", "scan_type"}
        },
    }


def _error_envelope(message: str, scan_type: str, target: str = "") -> Dict:
    """Wrap a failure in the same envelope shape, so the GUI never crashes."""
    return {
        "ok": False,
        "error": message,
        "scan_type": scan_type,
        "target": target,
        "summary": _empty_summary(),
        "total_findings": 0,
        "findings": [],
        "meta": {},
    }


# --------------------------------------------------------------------------- #
# Static scan: analyse an uploaded source-code ZIP (no code is executed).
# --------------------------------------------------------------------------- #

def run_static_scan(zip_path: str) -> Dict:
    """
    Run the static analyzer against a .zip of website source code.

    zip_path: path to the uploaded .zip file on disk.
    Returns the shared envelope dict (see module docstring).
    """
    try:
        report = StaticZipAnalyzer(zip_path).analyze()
        return _ok_envelope(report, scan_type="static")
    except FileNotFoundError:
        return _error_envelope(f"ZIP file not found: {zip_path}", "static", zip_path)
    except ZipSafetyError as exc:
        # The ZIP failed a safety check (zip-slip / zip-bomb protection).
        return _error_envelope(f"Unsafe ZIP rejected: {exc}", "static", zip_path)
    except Exception as exc:
        return _error_envelope(f"Static scan failed: {exc}", "static", zip_path)


# --------------------------------------------------------------------------- #
# Passive scan: fetch a live page and analyse the HTML (read-only, no attacks).
# --------------------------------------------------------------------------- #

def run_passive_scan(url: str, profile_path: Optional[str] = None) -> Dict:
    """
    Run the passive scanner against a live URL.

    url:          the page to scan, e.g. "http://127.0.0.1:8000/"
                  (only scan DVWA / Juice Shop / your own test sites).
    profile_path: optional path to a YAML/JSON scan profile. If omitted,
                  sensible defaults are used.
    Returns the shared envelope dict.
    """
    try:
        profile = ScanProfile.load(profile_path) if profile_path else ScanProfile()
        report = PassiveScanner(profile).scan(url)
        return _ok_envelope(report, scan_type="passive")
    except Exception as exc:
        # Covers network errors, bad URLs, timeouts, non-200 responses, etc.
        return _error_envelope(f"Passive scan failed: {exc}", "passive", url)


# --------------------------------------------------------------------------- #
# Combined scan: run both, if you have both a ZIP and a live URL for a target.
# --------------------------------------------------------------------------- #

def run_full_scan(
    url: Optional[str] = None,
    zip_path: Optional[str] = None,
    profile_path: Optional[str] = None,
) -> Dict:
    """
    Run whichever scans you have inputs for and merge the results into one
    envelope. Give a url, a zip_path, or both.

    Returns one combined envelope whose `findings` is every finding from both
    scans, and whose `summary` is the two severity counts added together.
    """
    sub_results: List[Dict] = []

    if zip_path:
        sub_results.append(run_static_scan(zip_path))
    if url:
        sub_results.append(run_passive_scan(url, profile_path=profile_path))

    if not sub_results:
        return _error_envelope(
            "Nothing to scan: provide a url, a zip_path, or both.",
            scan_type="combined",
        )

    combined_findings: List[Dict] = []
    combined_summary = _empty_summary()
    errors: List[str] = []

    for res in sub_results:
        combined_findings.extend(res["findings"])
        for sev in combined_summary:
            combined_summary[sev] += res["summary"].get(sev, 0)
        if not res["ok"] and res["error"]:
            errors.append(res["error"])

    # Highest-severity findings first, so the GUI shows the scary stuff on top.
    severity_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
    combined_findings.sort(
        key=lambda f: severity_order.get(f.get("severity"), 0), reverse=True
    )

    return {
        # "ok" is True if at least one sub-scan produced results without error.
        "ok": any(res["ok"] for res in sub_results),
        "error": "; ".join(errors) if errors else None,
        "scan_type": "combined",
        "target": url or zip_path or "",
        "summary": combined_summary,
        "total_findings": len(combined_findings),
        "findings": combined_findings,
        "meta": {"sub_scans": [res["scan_type"] for res in sub_results]},
    }


# --------------------------------------------------------------------------- #
# Quick self-test: run this file directly to confirm the wiring works.
#   python webset_core.py
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import json

    print("Running a passive scan against the built-in demo page...")
    print("(start it first in another terminal with:  python -m dynamic.demo_passive --serve )\n")

    result = run_passive_scan("http://127.0.0.1:8000/")
    if result["ok"]:
        print(f"OK - {result['total_findings']} findings, summary: {result['summary']}")
    else:
        print(f"Could not scan (this is normal if the demo server isn't running):")
        print(f"   {result['error']}")

    print("\nEnvelope shape the frontend will always receive:")
    print(json.dumps({k: (v if k != "findings" else "[...]") for k, v in result.items()}, indent=2))
