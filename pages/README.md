# static/ — Static ZIP analysis

Reads an uploaded `.zip` of a site's source code and scans it **without running any of it**.

## What it checks
- Hardcoded secrets (AWS keys, private keys, tokens, passwords, DB connection strings)
- Risky code patterns (`eval`, `exec`, `pickle.loads`, `shell=True`, SQL string concatenation, `innerHTML`, debug mode left on)
- Exposed sensitive files (`.env`, `.git`, keys, backups, `.sql` dumps)
- Declared dependencies (`requirements.txt`, `package.json`, `composer.json`)
- Tech stack, guessed from marker files

It is also defensive about the ZIP itself: zip-slip (path traversal) and zip-bomb limits.

## Use it
```python
from static import StaticZipAnalyzer

report = StaticZipAnalyzer("uploaded_site.zip").analyze()
```
Report format: see `INTEGRATION.md` in the repo root.

## Try it
From the repo root: `python -m static.demo_static`
(or right-click `demo_static.py` in PyCharm and Run). Expected: 9 findings.

## Known limits
Detection is regex-based, so expect some false positives and negatives. Dependencies are listed but not yet checked against a CVE database.
