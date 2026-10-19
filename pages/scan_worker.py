"""Run scanner jobs off the GUI thread so the interface remains responsive."""
from PyQt6.QtCore import QThread, pyqtSignal

class ScanWorker(QThread):
    finished_with_result = pyqtSignal(object)

    def __init__(self, scan_type: str, target: str, parent=None):
        super().__init__(parent)
        self.scan_type = scan_type
        self.target = target

    def run(self):
        try:
            # Lazy import: a missing scanner dependency should be reported in
            # the UI, not stop the whole application from opening.
            from pages.webset_core import run_passive_scan, run_static_scan
            if self.scan_type == "passive":
                result = run_passive_scan(self.target)
            elif self.scan_type == "static":
                result = run_static_scan(self.target)
            else:
                result = {"ok": False, "error": f"Unknown scan type: {self.scan_type}",
                          "scan_type": self.scan_type, "target": self.target,
                          "summary": {}, "total_findings": 0, "findings": [], "meta": {}}
        except Exception as exc:
            result = {"ok": False, "error": f"Scanner could not start: {exc}",
                      "scan_type": self.scan_type, "target": self.target,
                      "summary": {}, "total_findings": 0, "findings": [], "meta": {}}
        self.finished_with_result.emit(result)
