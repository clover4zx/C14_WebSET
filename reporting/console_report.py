"""
console_report.py

Renders a PassiveScanner report dict as a colourised console report using
`rich`, so results are readable at a glance during development/demos
rather than staring at raw JSON. The GUI (PyQt) will eventually render
this data itself, but this is useful for the CLI and for quick debugging.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

SEVERITY_STYLE = {
    "HIGH": "bold white on red",
    "MEDIUM": "bold black on yellow",
    "LOW": "bold black on cyan",
    "INFO": "dim white",
}


def print_report(report: dict, console: Console = None) -> None:
    console = console or Console()

    header = Text(f"WebSET Passive Scan Report", style="bold magenta")
    subheader = Text(f"{report['url']}  (HTTP {report['status_code']})", style="dim")
    console.print(Panel.fit(Text.assemble(header, "\n", subheader)))

    summary = report["summary"]
    summary_line = "  ".join(
        f"[{SEVERITY_STYLE[sev]}] {sev}: {summary.get(sev, 0)} [/{SEVERITY_STYLE[sev]}]"
        for sev in ("HIGH", "MEDIUM", "LOW", "INFO")
    )
    console.print(summary_line)
    console.print(f"Total findings: [bold]{report['total_findings']}[/bold]\n")

    if not report["findings"]:
        console.print("[green]No findings.[/green]")
        return

    table = Table(show_lines=True)
    table.add_column("Severity", no_wrap=True)
    table.add_column("Category")
    table.add_column("Location", overflow="fold")
    table.add_column("Description", overflow="fold")

    for finding in report["findings"]:
        sev = finding["severity"]
        table.add_row(
            f"[{SEVERITY_STYLE.get(sev, '')}] {sev} [/{SEVERITY_STYLE.get(sev, '')}]",
            finding["category"],
            finding["location"],
            finding["description"],
        )

    console.print(table)
