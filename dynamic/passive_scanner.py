"""
passive_scanner.py

WebSET - Passive Scanner (Week 6 backend milestone), incorporating the
library improvements suggested for this component:

  1. Advanced filtering & pattern matching
     - re (secret / dangerous-payload detection inside script bodies, URLs, inputs)
     - packaging (comparing detected frontend library versions against a
       known-vulnerable-version list - see vulnerable_versions.py)
     - tldextract (splitting links into subdomain/domain/suffix, to tell
       whether a link on the page points to an untrusted third-party domain)
  2. CLI configuration -> see cli.py (click-based)
  3. Scan profiles/config -> see scan_profile.py (YAML-based)
  4. Advanced HTML parsing -> BeautifulSoup using the "lxml" parser
     (faster, and tolerates broken/malformed HTML far better than the
     stdlib "html.parser")
  5. Rich console output -> see console_report.py

This module only ever performs PASSIVE analysis: it fetches and reads a
page, it never submits forms, brute-forces inputs, or otherwise interacts
with the target beyond a normal GET request. Active/offensive testing
(payload injection etc.) is a separate, later milestone and must remain
scoped to authorised test environments (DVWA / OWASP Juice Shop).

Usage:
    from dynamic import PassiveScanner, ScanProfile

    profile = ScanProfile.load("scan_profile_example.yaml")   # or ScanProfile() for defaults
    scanner = PassiveScanner(profile)
    report = scanner.scan("http://127.0.0.1:8000/")

    for finding in report["findings"]:
        print(finding["severity"], finding["category"], finding["location"])
"""

from __future__ import annotations

import re
import dataclasses
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
import tldextract
from bs4 import BeautifulSoup

try:
    from .scan_profile import ScanProfile
    from .vulnerable_versions import check_version
except ImportError:
    from scan_profile import ScanProfile
    from vulnerable_versions import check_version

# Use tldextract in fully offline mode (bundled public-suffix-list snapshot
# only, no live network fetch). A scanner's core detection logic should not
# silently depend on internet access to a third-party list on every run -
# both for reliability and because it's an unnecessary network dependency
# for a security tool to have.
_tld_extract = tldextract.TLDExtract(suffix_list_urls=())

SEVERITY_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}


@dataclasses.dataclass(kw_only=True)
class Finding:
    severity: str          # HIGH | MEDIUM | LOW | INFO
    category: str
    location: str          # e.g. "inline <script> #2", "form #1", a URL
    line: Optional[int] = None   # always None for live pages; kept so static and passive findings share one shape
    snippet: str
    description: str
    recommendation: str

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)


# --------------------------------------------------------------------------- #
# Secret / dangerous-payload patterns (kept consistent in spirit with the
# static ZIP analyzer, so reports look the same regardless of which scan
# stage produced them).
# --------------------------------------------------------------------------- #

SECRET_PATTERNS = [
    ("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "HIGH",
     "A hardcoded AWS Access Key ID was found in page content.",
     "Never ship cloud credentials in client-side code. Revoke this key "
     "and load credentials server-side only."),
    ("Generic API Key / Secret", re.compile(
        r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*['\"][A-Za-z0-9_\-/+=]{12,}['\"]"), "MEDIUM",
     "A value that looks like an API key or secret is embedded in page "
     "content (visible to any visitor).",
     "Remove the key from client-side code; proxy any calls that need it "
     "through a backend that holds the credential server-side."),
    ("Private Key Block", re.compile(
        r"-----BEGIN (RSA|EC|DSA|OPENSSH|PGP)?\s?PRIVATE KEY-----"), "HIGH",
     "A private key block is embedded in page content.",
     "Remove immediately and rotate the key - this is a critical exposure."),
    ("JWT-like Token", re.compile(
        r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"), "LOW",
     "A JSON Web Token is present in page content.",
     "Confirm this is not a live token with real access; avoid embedding "
     "long-lived tokens in client-side code."),
]

DANGEROUS_JS_PATTERNS = [
    ("eval() usage", re.compile(r"\beval\s*\("), "MEDIUM",
     "eval() executes arbitrary strings as code; dangerous if any part of "
     "the string can be influenced by user input.",
     "Avoid eval(). Use JSON.parse for data, or explicit logic instead of "
     "dynamic code execution."),
    ("document.write() usage", re.compile(r"document\.write\s*\("), "LOW",
     "document.write() can be an XSS vector when writing unsanitised "
     "content, and can also cause page-load/performance issues.",
     "Use DOM APIs (createElement/textContent) instead."),
    ("innerHTML assignment from variable", re.compile(
        r"\.innerHTML\s*=\s*[^'\"][^;]*;"), "LOW",
     "Assigning to innerHTML from a variable can lead to XSS if the value "
     "includes unsanitised user input.",
     "Use textContent for plain text, or sanitise HTML (e.g. DOMPurify) "
     "before inserting it."),
]


class PassiveScanner:
    def __init__(self, profile: Optional[ScanProfile] = None, session: Optional[requests.Session] = None):
        """
        profile: a ScanProfile instance (see scan_profile.py). If omitted, sane
                 defaults are used (no excluded tags, no trusted domains,
                 no custom signatures).
        session: optionally supply your own requests.Session (useful for
                 tests, or if authentication/cookies are needed later).
        """
        self.profile = profile or ScanProfile()
        self.session = session or requests.Session()
        self.findings: List[Finding] = []

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def scan(self, url: str) -> Dict:
        self.findings = []
        response = self._fetch(url)
        soup = BeautifulSoup(response.text, "lxml")  # (4) faster + more forgiving parser

        target_domain = _tld_extract(url).registered_domain

        self._scan_scripts(soup, url)
        self._scan_links(soup, url, target_domain)
        self._scan_forms(soup, url)
        self._scan_custom_signatures(response.text)

        return self._build_report(url, response)

    # ------------------------------------------------------------------ #
    # Fetching
    # ------------------------------------------------------------------ #

    def _fetch(self, url: str) -> requests.Response:
        headers = {"User-Agent": self.profile.user_agent}
        response = self.session.get(
            url, headers=headers, timeout=self.profile.timeout
        )
        response.raise_for_status()
        return response

    # ------------------------------------------------------------------ #
    # Script analysis: secrets, dangerous JS patterns, library versions
    # ------------------------------------------------------------------ #

    def _scan_scripts(self, soup: BeautifulSoup, base_url: str) -> None:
        scripts = soup.find_all("script")
        for i, tag in enumerate(scripts, start=1):
            tag_type = (tag.get("type") or "").lower()
            if tag_type in self.profile.excluded_script_types:
                continue

            src = tag.get("src")
            if src:
                self._check_library_version(src, base_url)
                continue  # external script content itself isn't fetched (passive scope)

            # Inline script body
            body = tag.string or ""
            location = f"inline <script> #{i}"
            self._scan_text_for_secrets(body, location)
            self._scan_text_for_dangerous_js(body, location)

    def _check_library_version(self, src: str, base_url: str) -> None:
        """
        Best-effort extraction of a library name + version from a script
        src filename, e.g. '/js/jquery-1.12.4.min.js' -> ('jquery', '1.12.4').
        """
        match = re.search(
            r"([a-zA-Z][\w.-]*?)[-.]v?(\d+\.\d+(?:\.\d+)?)(?:\.min)?\.js",
            src,
        )
        if not match:
            return
        library, version = match.group(1).lower(), match.group(2)

        result = check_version(library, version)
        if result:
            advisory, severity, description = result
            self.findings.append(Finding(
                severity=severity,
                category=f"Outdated Library: {library} {version}",
                location=urljoin(base_url, src),
                snippet=src,
                description=f"{description} ({advisory})",
                recommendation=f"Upgrade {library} beyond the vulnerable "
                                f"version referenced in {advisory}.",
            ))

    def _scan_text_for_secrets(self, text: str, location: str) -> None:
        for name, pattern, severity, description, recommendation in SECRET_PATTERNS:
            match = pattern.search(text)
            if match:
                self.findings.append(Finding(
                    severity=severity,
                    category=f"Hardcoded Secret: {name}",
                    location=location,
                    snippet=self._redact(text, match.span()),
                    description=description,
                    recommendation=recommendation,
                ))

    def _scan_text_for_dangerous_js(self, text: str, location: str) -> None:
        for name, pattern, severity, description, recommendation in DANGEROUS_JS_PATTERNS:
            match = pattern.search(text)
            if match:
                snippet = text[max(0, match.start()-20):match.end()+20].strip()
                self.findings.append(Finding(
                    severity=severity,
                    category=f"Risky Pattern: {name}",
                    location=location,
                    snippet=snippet[:160],
                    description=description,
                    recommendation=recommendation,
                ))

    # ------------------------------------------------------------------ #
    # Link analysis: flag links to untrusted external domains
    # ------------------------------------------------------------------ #

    def _scan_links(self, soup: BeautifulSoup, base_url: str, target_domain: str) -> None:
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme not in ("http", "https"):
                continue
            if absolute in seen:
                continue
            seen.add(absolute)

            ext = _tld_extract(absolute)
            link_domain = ext.registered_domain
            if not link_domain or link_domain == target_domain:
                continue
            if link_domain in self.profile.trusted_domains:
                continue

            self.findings.append(Finding(
                severity="INFO",
                category="External Link to Third-Party Domain",
                location=absolute,
                snippet=f'<a href="{href}">',
                description=f"Page links to an external domain ({link_domain}) "
                             "not in the configured trusted-domains list.",
                recommendation="Review whether this external destination is "
                                "expected and legitimate. If it's a known "
                                "partner domain, add it to trusted_domains "
                                "in the scan profile to silence this.",
            ))

    # ------------------------------------------------------------------ #
    # Form analysis: quick, passive checks only (no submission)
    # ------------------------------------------------------------------ #

    def _scan_forms(self, soup: BeautifulSoup, base_url: str) -> None:
        for i, form in enumerate(soup.find_all("form"), start=1):
            location = f"form #{i}"
            action = form.get("action", "")
            absolute_action = urljoin(base_url, action) if action else base_url

            if absolute_action.startswith("http://"):
                self.findings.append(Finding(
                    severity="MEDIUM",
                    category="Form Submits Over Plain HTTP",
                    location=location,
                    snippet=f'action="{action}"',
                    description="This form submits data over an unencrypted "
                                 "HTTP connection.",
                    recommendation="Serve the form and its action endpoint "
                                    "over HTTPS to protect submitted data "
                                    "in transit.",
                ))

            password_inputs = form.find_all("input", {"type": "password"})
            for pw in password_inputs:
                autocomplete = (pw.get("autocomplete") or "").lower()
                if autocomplete not in ("off", "new-password"):
                    self.findings.append(Finding(
                        severity="LOW",
                        category="Password Field Without autocomplete=off",
                        location=location,
                        snippet=str(pw)[:160],
                        description="A password field does not disable "
                                     "autocomplete, which can allow browsers "
                                     "to store/autofill credentials on "
                                     "shared devices.",
                        recommendation='Add autocomplete="new-password" (or '
                                        '"off") to sensitive password fields '
                                        'where appropriate.',
                    ))

            if not form.find("input", {"name": re.compile("csrf", re.I)}) and \
               not form.find("input", {"type": "hidden"}):
                self.findings.append(Finding(
                    severity="LOW",
                    category="No Obvious CSRF Token",
                    location=location,
                    snippet=str(form)[:160],
                    description="No hidden/CSRF-style input field was found "
                                 "in this form (heuristic check only).",
                    recommendation="Confirm CSRF protection is implemented "
                                    "server-side (token may be set via "
                                    "JS/cookies not visible in static HTML).",
                ))

    # ------------------------------------------------------------------ #
    # Custom signatures loaded from the scan profile
    # ------------------------------------------------------------------ #

    def _scan_custom_signatures(self, full_page_text: str) -> None:
        for sig in self.profile.custom_signatures:
            match = sig["pattern"].search(full_page_text)
            if match:
                self.findings.append(Finding(
                    severity=sig.get("severity", "INFO"),
                    category=f"Custom Signature: {sig['name']}",
                    location="page content",
                    snippet=self._redact(full_page_text, match.span()),
                    description=sig.get("description", "Custom signature matched."),
                    recommendation=sig.get("recommendation", "Review the matched content."),
                ))

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _redact(text: str, span: tuple) -> str:
        start, end = span
        window_start = max(0, start - 15)
        window_end = min(len(text), end + 15)
        return (text[window_start:start] + "[REDACTED]" + text[end:window_end]).strip()[:160]

    def _build_report(self, url: str, response: requests.Response) -> Dict:
        findings_sorted = sorted(
            self.findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 0), reverse=True
        )
        summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in findings_sorted:
            summary[f.severity] = summary.get(f.severity, 0) + 1

        return {
            "scan_type": "passive",
            "target": url,
            "url": url,
            "status_code": response.status_code,
            "summary": summary,
            "total_findings": len(findings_sorted),
            "findings": [f.to_dict() for f in findings_sorted],
        }
