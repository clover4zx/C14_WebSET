"""
cli.py

Command-line interface for WebSET's passive scanner, built with `click`
rather than bare argparse for cleaner flag handling, help text, and easy
future subcommands (e.g. `webset scan`, `webset active-scan`, ...).

Usage:
    python -m dynamic.cli https://example.com
    python -m dynamic.cli https://example.com --config scan_profile_example.yaml
    python -m dynamic.cli https://example.com --format json --output report.json
    python -m dynamic.cli https://example.com --no-links --no-forms
"""

import json
import sys

import click
from rich.console import Console

try:
    from .passive_scanner import PassiveScanner
    from .scan_profile import ScanProfile
    from .console_report import print_report
except ImportError:
    from passive_scanner import PassiveScanner
    from scan_profile import ScanProfile
    from console_report import print_report


@click.command()
@click.argument("url")
@click.option("--config", "-c", "config_path", type=click.Path(exists=True),
              help="Path to a YAML/JSON scan profile (trusted domains, "
                   "custom signatures, etc.).")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json"]),
              default="table", show_default=True, help="Output format.")
@click.option("--output", "-o", "output_path", type=click.Path(),
              help="Write the JSON report to this file (in addition to "
                   "console output).")
@click.option("--no-links", is_flag=True, help="Skip external link analysis.")
@click.option("--no-forms", is_flag=True, help="Skip form security checks.")
@click.option("--no-scripts", is_flag=True, help="Skip script/secret/version analysis.")
@click.option("--verbose", "-v", is_flag=True, help="Show extra progress output.")
def scan(url, config_path, output_format, output_path, no_links, no_forms, no_scripts, verbose):
    """Run WebSET's passive scanner against URL.

    This performs a read-only GET request and analyses the returned HTML.
    It never submits forms or sends attack payloads - use only against
    sites you are authorised to test.
    """
    console = Console()

    profile = ScanProfile.load(config_path) if config_path else ScanProfile()

    if verbose:
        console.print(f"[dim]Fetching {url} ...[/dim]")

    scanner = PassiveScanner(profile)

    # Toggle checks off by temporarily monkeypatching (kept simple/explicit
    # for a small CLI tool rather than building a full plugin system).
    if no_links:
        scanner._scan_links = lambda *a, **k: None
    if no_forms:
        scanner._scan_forms = lambda *a, **k: None
    if no_scripts:
        scanner._scan_scripts = lambda *a, **k: None

    try:
        report = scanner.scan(url)
    except Exception as exc:
        console.print(f"[bold red]Scan failed:[/bold red] {exc}")
        sys.exit(1)

    if output_format == "json":
        click.echo(json.dumps(report, indent=2))
    else:
        print_report(report, console)

    if output_path:
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        if verbose:
            console.print(f"[dim]Report written to {output_path}[/dim]")


if __name__ == "__main__":
    scan()
