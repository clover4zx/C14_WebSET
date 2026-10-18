# dynamic/ — Passive scanning of live pages

Makes one read-only GET request to a page and analyses the HTML. It **never** submits forms or sends payloads.
Active testing (payload injection) is a later milestone and will also live in this folder. Only ever point this at sites you are authorised to test (DVWA, OWASP Juice Shop).

## What it checks
- Secrets and risky JavaScript in inline scripts (`re`)
- Outdated frontend libraries, from script filenames compared with `packaging` (`vulnerable_versions.py`)
- Links to untrusted third-party domains (`tldextract`, bundled offline snapshot)
- Passive form checks: HTTP submission, password `autocomplete`, no visible CSRF field
- Your own regex rules, loaded from a YAML scan profile (`pyyaml`)

HTML is parsed with BeautifulSoup + `lxml`; console output uses `rich`; the CLI uses `click`.

## Files
| File | Purpose |
|---|---|
| `passive_scanner.py` | The scanner |
| `scan_profile.py` | Loads YAML/JSON scan profiles |
| `scan_profile_example.yaml` | Example profile |
| `vulnerable_versions.py` | Small known-vulnerable library list |
| `console_report.py` | Coloured terminal report |
| `cli.py` | Command-line interface |
| `demo_passive.py` | Self-contained demo (local test server) |

## Use it
```python
from dynamic import PassiveScanner, ScanProfile

report = PassiveScanner(ScanProfile()).scan("http://127.0.0.1:3000/")
```
CLI, from the repo root: `python -m dynamic.cli http://127.0.0.1:3000/ --config dynamic/scan_profile_example.yaml`

## Try it
From the repo root: `python -m dynamic.demo_passive` (or right-click `demo_passive.py` in PyCharm and Run). Expected: 8 findings.

## Known limits
- Library versions are read from filenames only; bundled or renamed scripts are missed.
- The vulnerable-library list is small and hand-written, not a live feed.
- The CSRF check is a heuristic.
- Needs Python 3.10 or newer.
