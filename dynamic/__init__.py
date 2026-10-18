"""WebSET dynamic scanning: passive scanning of live pages (active testing will live here too)."""

from .passive_scanner import PassiveScanner
from .scan_profile import ScanProfile

__all__ = ["PassiveScanner", "ScanProfile"]
