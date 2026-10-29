# WebSET — Website Security Evaluation Tool

WebSET is an automated, end-to-end penetration testing prototype for local
development teams. It combines static source-code analysis, passive live-page
scanning, active Selenium-driven payload testing, and misconfiguration checks
into a single desktop toolkit with built-in case management and remediation
reporting.

**Team:** WebGoats (Group C14)
- William Wu - Project Manager, QA
- Sophia Pineda - Frontend Developer
- Oliver Neilson - Security Analyst
- Andy Truong - Security Analyst
- Saleh Al Muosa - Backend Developer
- Joshua Tjandra - Backend Developer


## Features

- **Static scan** — upload a source-code `.zip` and scan it for hardcoded
  secrets, dangerous function calls, and outdated dependencies, without
  executing any of the uploaded code.
- **Passive scan** — fetch a live page read-only and check for hardcoded
  secrets, dangerous JavaScript patterns (`eval()`, `document.write`,
  unsanitised `innerHTML`), outdated frontend libraries, and links to
  untrusted third-party domains.
- **Active scan** — drive a headless Chrome browser (Selenium) to submit test
  payloads into forms and URL parameters, then verify the result in the live
  DOM. Confirms reflected/DOM XSS by checking whether a payload actually
  executes, and SQL injection by detecting database error signatures that
  were not present before the probe. Restricted to loopback/private-network
  targets by default.
- **Case management** — track findings as cases through a status workflow.
- **Scan history** — every scan (static, passive, active) is recorded and
  persisted so it survives restarting the app.
- **Reports** — generate findings reports as PDF, HTML, Markdown, JSON, or CSV.

## Tech stack

| Layer | Technology |
|---|---|
| GUI | Python, PyQt6 |
| Static / passive scanning | Requests, BeautifulSoup, lxml, tldextract |
| Active scanning | Selenium, ChromeDriver |
| Reporting | fpdf2 (PDF) |
| Data | JSON file store (`data/scan_history_store.json`); see [Known limitations](#known-limitations) |
| Target environments | VMware-hosted Kali Linux, DVWA, OWASP Juice Shop |

## Requirements

- Python 3.10+
- Chromium or Google Chrome, plus a matching ChromeDriver, for active
  scanning only. On Kali/Debian:
  ```bash
  sudo apt install chromium chromium-driver
  ```
- A target you are authorised to test: DVWA, OWASP Juice Shop, or the
  bundled demo page described below.

## Installation

```bash
git clone <repo-url>
cd C14_WebSET
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the app

```bash
python main.py
```

## Trying it without DVWA or Juice Shop

A self-contained demo target and a sample vulnerable ZIP are included so the
scanners can be tried immediately:

```bash
# Serve a synthetic vulnerable page at http://127.0.0.1:8000/ for the Dynamic tab
python -m tools.demo_passive --serve

# Generate sample_vulnerable_site.zip for the Static tab (already included under tools/)
python tools/make_demo_zip.py
```

## Project structure

```
C14_WebSET/
├── main.py              Parent window: sidebar + dashboard shell
├── requirements.txt
├── app/                 Shared UI: theme, sidebar, reusable widgets, charts
├── pages/                Top-level screens (Dashboard, New Scan, Scan History,
│   │                     Cases, Reports, Settings)
│   └── tabs/             Static / Dynamic tabs inside the New Scan page
├── scanner/              Scan engines + integration layer (webset_core.py is
│                         the single entry point the UI calls)
├── reporting/            Report generation (PDF/HTML/Markdown/JSON/CSV)
├── tools/                Demo server and sample-data generators
└── data/                 Per-feature data access (cases, dashboard, scan history)
```

See Section 2.5 of the project report for the full rationale behind this
structure.

## Safety

WebSET sends real requests, and its active scanner submits real test
payloads. Only use it against systems you own or are explicitly authorised
to test (your own local environment, DVWA, OWASP Juice Shop, or similar).
The active scanner refuses non-loopback/non-private targets by default.

## Known limitations

- Scan history is currently persisted to a local JSON file
  (`data/scan_history_store.json`) rather than the SQLite database originally
  planned; see the project report's reflections section.
- The Scan History and Dashboard pages mix a small set of illustrative dummy
  records with real scan results.
<!-- Add/remove items here to match the current state of the app at submission time. -->

## License

MIT — see [LICENSE](LICENSE).
