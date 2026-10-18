"""WebSET static scanning: reads uploaded source-code ZIPs without running them."""

from .static_zip_analyzer import StaticZipAnalyzer, ZipSafetyError

__all__ = ["StaticZipAnalyzer", "ZipSafetyError"]
