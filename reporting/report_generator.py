"""
pages/report_generator.py

Turns a Reports-page config dict (from reports_page.get_config()) into an
actual report file on disk. Supports PDF, HTML, Markdown, JSON and CSV.

The config dict has:
    title, client, prepared_by, format, scope, min_severity,
    include_resolved, sections (list), findings (list of dicts).
Each finding has: title, severity, owasp, remediation, case_id,
case_title, case_status, target.

PDF uses the `fpdf2` library (see requirements.txt); the other formats use
only Python's standard library.
"""

import csv
import datetime
import html
import json
from pathlib import Path

SEVERITY_LEVELS = ["Critical", "High", "Medium", "Low"]


def generate_report(config: dict, out_path: str) -> str:
    """Write the report to out_path, choosing the writer from the file
    extension (falling back to the config's format). Returns out_path."""
    ext = Path(out_path).suffix.lower()
    fmt = (config.get("format") or "").lower()

    if ext == ".pdf" or (not ext and fmt == "pdf"):
        _write_pdf(config, out_path)
    elif ext in (".html", ".htm") or fmt == "html":
        _write_html(config, out_path)
    elif ext == ".md" or fmt == "markdown":
        _write_markdown(config, out_path)
    elif ext == ".json" or fmt == "json":
        _write_json(config, out_path)
    elif ext == ".csv" or fmt == "csv":
        _write_csv(config, out_path)
    else:
        _write_pdf(config, out_path)
    return out_path


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _counts(findings: list) -> dict:
    counts = {level: 0 for level in SEVERITY_LEVELS}
    for finding in findings:
        sev = finding.get("severity", "")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _today() -> str:
    return datetime.datetime.now().strftime("%d/%m/%Y")


def _ascii(text) -> str:
    """Core PDF fonts are latin-1 only; replace anything they can't show."""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def _trunc(text, limit: int) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "."


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #

def _write_pdf(config: dict, out_path: str) -> None:
    from fpdf import FPDF

    findings = config.get("findings", [])
    sections = config.get("sections", [])
    counts = _counts(findings)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- title + meta ---
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 18)
    pdf.multi_cell(0, 10, _ascii(config.get("title") or "Security Report"))

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    for line in [
        f"Client: {config.get('client') or '-'}",
        f"Prepared by: {config.get('prepared_by') or '-'}",
        f"Date: {_today()}",
        f"Scope: {config.get('scope', 'All scans')}",
        f"Minimum severity: {config.get('min_severity', 'Low')}",
    ]:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, _ascii(line))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # --- executive summary ---
    if "summary" in sections:
        _pdf_heading(pdf, "Executive Summary")
        pdf.set_font("Helvetica", "", 11)
        pdf.set_x(pdf.l_margin)
        case_count = len({f.get("case_id") for f in findings})
        pdf.multi_cell(0, 6, _ascii(
            f"This report covers {len(findings)} finding(s) across {case_count} case(s). "
            f"Severity breakdown: Critical {counts['Critical']}, High {counts['High']}, "
            f"Medium {counts['Medium']}, Low {counts['Low']}."
        ))
        pdf.ln(3)

    # --- severity bar chart (bars drawn as rectangles, so no cell can run
    #     out of horizontal space) ---
    if "chart" in sections:
        _pdf_heading(pdf, "Findings by Severity")
        colours = {
            "Critical": (192, 57, 43), "High": (230, 126, 34),
            "Medium": (241, 196, 15), "Low": (41, 128, 185),
        }
        total = max(sum(counts.values()), 1)
        pdf.set_font("Helvetica", "", 10)
        label_w = 25
        bar_max = 110
        for level in SEVERITY_LEVELS:
            pdf.set_x(pdf.l_margin)
            y = pdf.get_y()
            pdf.set_text_color(0, 0, 0)
            pdf.cell(label_w, 7, level, 0, 0)
            bar_w = bar_max * counts[level] / total
            if bar_w > 0:
                r, g, b = colours[level]
                pdf.set_fill_color(r, g, b)
                pdf.rect(pdf.l_margin + label_w, y + 1.5, bar_w, 4, style="F")
            pdf.set_xy(pdf.l_margin + label_w + bar_max + 4, y)
            pdf.cell(15, 7, str(counts[level]), 0, 1)
        pdf.ln(3)

    # --- detailed findings table ---
    if "details" in sections and findings:
        _pdf_heading(pdf, "Detailed Findings")
        widths = [20, 92, 50, 18]
        limits = [12, 62, 40, 10]
        headers = ["Severity", "Finding", "OWASP Category", "Case"]

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        pdf.set_x(pdf.l_margin)
        for width, head in zip(widths, headers):
            pdf.cell(width, 7, head, 1, 0, "L", True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for finding in findings:
            pdf.set_x(pdf.l_margin)
            values = [finding.get("severity", ""), finding.get("title", ""),
                      finding.get("owasp", ""), finding.get("case_id", "")]
            for value, width, limit in zip(values, widths, limits):
                pdf.cell(width, 7, _ascii(_trunc(value, limit)), 1, 0, "L")
            pdf.ln()
        pdf.ln(3)

    # --- remediation ---
    if "remediation" in sections and findings:
        _pdf_heading(pdf, "Remediation Recommendations")
        for finding in findings:
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, _ascii(f"[{finding.get('severity', '')}] {finding.get('title', '')}"))
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, _ascii(finding.get("remediation") or "Review and remediate this finding."))
            pdf.ln(1)
        pdf.ln(2)

    # --- OWASP mapping ---
    if "owasp" in sections and findings:
        _pdf_heading(pdf, "OWASP Top 10 Mapping")
        groups = {}
        for finding in findings:
            groups.setdefault(finding.get("owasp", "Unmapped"), []).append(finding)
        for category in sorted(groups):
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, _ascii(category))
            pdf.set_font("Helvetica", "", 10)
            for finding in groups[category]:
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(0, 6, _ascii(f"   - {finding.get('title', '')} ({finding.get('severity', '')})"))
            pdf.ln(1)
        pdf.ln(2)

    # --- scan details appendix ---
    if "scan_info" in sections and findings:
        _pdf_heading(pdf, "Scan Details")
        targets = sorted({f.get("target", "") for f in findings if f.get("target")})
        pdf.set_font("Helvetica", "", 10)
        for target in targets:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 6, _ascii("- " + target))

    pdf.output(out_path)


def _pdf_heading(pdf, text: str) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 8, _ascii(text))
    pdf.set_text_color(0, 0, 0)


# --------------------------------------------------------------------------- #
# HTML / Markdown / JSON / CSV
# --------------------------------------------------------------------------- #

def _write_html(config: dict, out_path: str) -> None:
    findings = config.get("findings", [])
    counts = _counts(findings)
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(f.get('severity', '')))}</td>"
        f"<td>{html.escape(str(f.get('title', '')))}</td>"
        f"<td>{html.escape(str(f.get('owasp', '')))}</td>"
        f"<td>{html.escape(str(f.get('case_id', '')))}</td>"
        "</tr>"
        for f in findings
    )
    doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(config.get('title', 'Security Report'))}</title>
<style>
 body{{font-family:Arial,Helvetica,sans-serif;margin:40px;color:#222;}}
 h1{{margin-bottom:4px;}} .meta{{color:#666;}}
 table{{border-collapse:collapse;width:100%;margin-top:12px;}}
 th,td{{border:1px solid #ccc;padding:6px 8px;text-align:left;}} th{{background:#eee;}}
</style></head><body>
<h1>{html.escape(config.get('title', 'Security Report'))}</h1>
<p class="meta">Client: {html.escape(config.get('client') or '-')}<br>
Prepared by: {html.escape(config.get('prepared_by') or '-')}<br>
Date: {_today()}<br>Scope: {html.escape(str(config.get('scope', '')))}</p>
<h2>Summary</h2>
<p>{len(findings)} finding(s) &mdash; Critical {counts['Critical']}, High {counts['High']},
Medium {counts['Medium']}, Low {counts['Low']}.</p>
<h2>Findings</h2>
<table><tr><th>Severity</th><th>Finding</th><th>OWASP Category</th><th>Case</th></tr>{rows}</table>
</body></html>"""
    Path(out_path).write_text(doc, encoding="utf-8")


def _write_markdown(config: dict, out_path: str) -> None:
    findings = config.get("findings", [])
    counts = _counts(findings)
    lines = [
        f"# {config.get('title', 'Security Report')}",
        "",
        f"- **Client:** {config.get('client') or '-'}",
        f"- **Prepared by:** {config.get('prepared_by') or '-'}",
        f"- **Date:** {_today()}",
        f"- **Scope:** {config.get('scope', '')}",
        "",
        f"**Summary:** {len(findings)} finding(s) — Critical {counts['Critical']}, "
        f"High {counts['High']}, Medium {counts['Medium']}, Low {counts['Low']}.",
        "",
        "| Severity | Finding | OWASP Category | Case |",
        "|---|---|---|---|",
    ]
    for f in findings:
        lines.append(
            f"| {f.get('severity', '')} | {f.get('title', '')} | "
            f"{f.get('owasp', '')} | {f.get('case_id', '')} |"
        )
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


def _write_json(config: dict, out_path: str) -> None:
    data = {
        "title": config.get("title"),
        "client": config.get("client"),
        "prepared_by": config.get("prepared_by"),
        "date": _today(),
        "scope": config.get("scope"),
        "min_severity": config.get("min_severity"),
        "sections": config.get("sections"),
        "summary": _counts(config.get("findings", [])),
        "findings": config.get("findings", []),
    }
    Path(out_path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_csv(config: dict, out_path: str) -> None:
    findings = config.get("findings", [])
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Severity", "Finding", "OWASP Category", "Case", "Target", "Remediation"])
        for f in findings:
            writer.writerow([
                f.get("severity", ""), f.get("title", ""), f.get("owasp", ""),
                f.get("case_id", ""), f.get("target", ""), f.get("remediation", ""),
            ])
