"""
scanner package - every scan engine WebSET uses, plus the integration layer.

    webset_core.py          single entry point the GUI calls (run_static_scan,
                            run_passive_scan, run_active_scan, ...)
    static_zip_analyzer.py  static analysis of an uploaded source-code ZIP
    passive_scanner.py      passive (read-only) analysis of a live page
    active_scanner.py       Selenium-driven active payload testing + verification
    scan_profile.py         YAML/JSON scan configuration
    vulnerable_versions.py  known-vulnerable frontend library versions

Selenium is imported lazily inside active_scanner.py, so the rest of the
application still starts if Selenium / Chrome are not installed.
"""

from .scan_profile import ScanProfile
from .passive_scanner import PassiveScanner
from .static_zip_analyzer import StaticZipAnalyzer

__all__ = ["ScanProfile", "PassiveScanner", "StaticZipAnalyzer"]
