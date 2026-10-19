"""Readable results window shared by static and passive scans."""
from PyQt6.QtWidgets import QDialog, QPlainTextEdit, QVBoxLayout, QPushButton, QHBoxLayout, QLabel

class ScanResultsDialog(QDialog):
    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WebSET Scan Results")
        self.resize(850, 600)
        root = QVBoxLayout(self)
        ok = bool(result.get("ok"))
        headline = QLabel(("Scan completed" if ok else "Scan could not complete") +
                          f" — {result.get('scan_type', 'unknown').title()} scan")
        headline.setStyleSheet("font-size: 16px; font-weight: 600; padding: 6px;")
        root.addWidget(headline)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        lines = [f"Target: {result.get('target') or 'Not provided'}"]
        if result.get("error"):
            lines += ["", "ERROR", result["error"]]
        summary = result.get("summary") or {}
        lines += ["", "SUMMARY"]
        for severity in ("HIGH", "MEDIUM", "LOW", "INFO"):
            lines.append(f"  {severity}: {summary.get(severity, 0)}")
        lines += [f"  Total findings: {result.get('total_findings', 0)}", "", "FINDINGS"]
        findings = result.get("findings") or []
        if not findings:
            lines.append("No findings were returned. This does not prove the target is secure.")
        for index, finding in enumerate(findings, 1):
            lines += [f"[{index}] {finding.get('severity', 'UNKNOWN')} — {finding.get('category', 'Finding')}",
                      f"    Location: {finding.get('location') or 'Not specified'}"]
            if finding.get("line") is not None:
                lines.append(f"    Line: {finding['line']}")
            if finding.get("description"):
                lines.append(f"    Description: {finding['description']}")
            if finding.get("snippet"):
                lines.append(f"    Evidence: {finding['snippet']}")
            if finding.get("recommendation"):
                lines.append(f"    Recommendation: {finding['recommendation']}")
            lines.append("")
        meta = result.get("meta") or {}
        if meta.get("tech_stack"):
            lines += ["TECH STACK", str(meta["tech_stack"]), ""]
        if meta.get("dependencies"):
            lines += ["DEPENDENCIES", str(meta["dependencies"]), ""]
        text.setPlainText("\n".join(lines))
        root.addWidget(text, 1)
        buttons = QHBoxLayout()
        buttons.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addLayout(buttons)
