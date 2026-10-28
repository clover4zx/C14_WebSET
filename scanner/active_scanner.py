"""
active_scanner.py

WebSET - Active Scanner (Selenium).

Where the passive scanner only READS a page, this scanner drives a real
headless Chrome browser, submits harmless test payloads into a target's
forms and URL parameters, and then VERIFIES the outcome by inspecting the
live DOM. Verifying in a browser (instead of just pattern-matching the
response text) is what keeps false positives low:

  * XSS            - a unique marker payload sets a JavaScript variable if
                     (and only if) it really executes. Three outcomes:
                       executed   -> HIGH   "Cross-Site Scripting (confirmed)"
                       injected   -> MEDIUM "HTML injection (execution not observed)"
                       reflected but safely encoded -> NOT reported
  * SQL injection (error-based) - a lone quote character is submitted; a
                     finding is only raised if a database error signature
                     appears that was NOT already on the page before the
                     probe (baseline diff).
  * SQL injection (boolean-based / auth bypass) - on login-style forms (a
                     password field present), an always-true condition
                     (e.g. ' OR '1'='1) and an always-false condition with
                     the same syntax (e.g. ' AND '1'='2) are submitted into
                     the username/email field. If the two conditions lead
                     to a different outcome (different resulting URL, or a
                     markedly different page), that's the classic signature
                     of a boolean-based SQLi / authentication bypass - this
                     catches cases (like the classic Juice Shop login
                     bypass) where no database error is ever shown, so the
                     error-based check above would miss it.

Findings use the same shape as the passive and static scanners:
    severity, category, location, line, snippet, description, recommendation

SAFETY
  * Only loopback / private-network targets are allowed (DVWA, Juice Shop,
    your own VM). Pass allow_external=True to override deliberately.
  * Payloads are benign markers; nothing is destroyed, stolen or persisted.
  * Submissions are rate-limited and capped (max_submissions).

Usage:
    from scanner.active_scanner import ActiveScanner

    scanner = ActiveScanner(timeout=10)
    report = scanner.scan("http://127.0.0.1:8000/")

Requires: selenium (4.6+) and Chrome/Chromium. On Kali:
    sudo apt install chromium chromium-driver
"""

from __future__ import annotations

import ipaddress
import os
import re
import shutil
import socket
import time
import uuid
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlparse, urlunparse

try:
    from .passive_scanner import Finding, SEVERITY_ORDER
except ImportError:  # run directly as a script
    from scanner.passive_scanner import Finding, SEVERITY_ORDER

try:
    from selenium import webdriver
    from selenium.common.exceptions import (
        NoAlertPresentException,
        StaleElementReferenceException,
        TimeoutException,
        UnexpectedAlertPresentException,
        WebDriverException,
    )
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    SELENIUM_AVAILABLE = True
except ImportError:  # the rest of WebSET must still start without Selenium
    SELENIUM_AVAILABLE = False

DEFAULT_TIMEOUT = 10
USER_AGENT = "WebSET-ActiveScanner/1.0 (+authorised-testing-only)"


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #

class ActiveScanError(Exception):
    """Base class for active-scan problems the GUI should show nicely."""


class SeleniumNotInstalledError(ActiveScanError):
    pass


class BrowserStartError(ActiveScanError):
    pass


class TargetNotAllowedError(ActiveScanError):
    pass


# --------------------------------------------------------------------------- #
# Payloads and detection signatures
# --------------------------------------------------------------------------- #

# {t} is replaced with a unique token per attempt, so a hit can only come
# from OUR payload executing - never from something already on the page.
XSS_PAYLOADS: List[Tuple[str, str]] = [
    ("HTML context", "<img src=x onerror=\"window['__webset_{t}']=1\">"),
    ("double-quote attribute breakout", "\"><img src=x onerror=\"window['__webset_{t}']=1\">"),
    ("single-quote attribute breakout", "'><svg onload=\"window['__webset_{t}']=1\">"),
]

SQLI_PROBES: List[str] = ["'", '"']

# Boolean-based pairs: (always-true, always-false) using matching syntax, so
# a differing outcome between the two is attributable to the TRUE/FALSE
# condition rather than to the payload shape. Used for the auth-bypass check
# below, not the per-field error-based loop.
BOOLEAN_SQLI_PAYLOADS: List[Tuple[str, str]] = [
    ("' OR '1'='1", "' AND '1'='2"),
    ("' OR 1=1-- -", "' AND 1=2-- -"),
]

SQL_ERROR_SIGNATURES: List[Tuple[str, "re.Pattern"]] = [
    ("SQLite", re.compile(r"SQLITE_ERROR|sqlite3?\.OperationalError|SQLite3::|unrecognized token", re.I)),
    ("MySQL/MariaDB", re.compile(
        r"You have an error in your SQL syntax|check the manual that corresponds to your (MySQL|MariaDB)"
        r"|mysqli?_(query|fetch|num_rows)|MySqlException", re.I)),
    ("PostgreSQL", re.compile(r"PG::SyntaxError|unterminated quoted string at or near|PSQLException|pg_query\(", re.I)),
    ("Microsoft SQL Server", re.compile(
        r"Unclosed quotation mark after the character string|Microsoft OLE DB Provider for SQL Server|SqlException", re.I)),
    ("Oracle", re.compile(r"\bORA-\d{5}\b", re.I)),
]

TEXT_INPUT_TYPES = {"", "text", "search", "email", "url", "tel"}
SKIP_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".css", ".js", ".map",
    ".pdf", ".zip", ".woff", ".woff2", ".ttf", ".mp4", ".mp3",
)
OVERLAY_SELECTORS = [  # best-effort: banners that block clicks (e.g. Juice Shop)
    "button[aria-label='Close Welcome Banner']",
    "a[aria-label='dismiss cookie message']",
    ".cc-dismiss",
]

# Boolean-diff thresholds. A large difference in resulting page size between
# the TRUE and FALSE submissions (on an otherwise identical request) is a
# secondary signal, in case the URL does not change but the page content does.
BOOLEAN_LENGTH_DIFF_THRESHOLD = 200


# --------------------------------------------------------------------------- #
# Pure helpers (no browser needed - easy to unit test)
# --------------------------------------------------------------------------- #

def assert_target_allowed(url: str, allow_external: bool = False) -> None:
    """Refuse anything that is not http(s) to a local / private address."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise TargetNotAllowedError("Target must be an http:// or https:// URL.")
    if allow_external:
        return
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        raise TargetNotAllowedError(f"Cannot resolve host '{parsed.hostname}'.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not (ip.is_loopback or ip.is_private or ip.is_link_local):
            raise TargetNotAllowedError(
                f"Active testing is restricted to local/private targets; "
                f"{parsed.hostname} resolves to {ip}. "
                "Only test systems you own or are authorised to test."
            )


def find_sql_errors(text: str) -> List[Tuple[str, str]]:
    """Return [(database, matched_text)] for every SQL error signature in text."""
    hits = []
    for name, pattern in SQL_ERROR_SIGNATURES:
        match = pattern.search(text or "")
        if match:
            hits.append((name, match.group(0)))
    return hits


def param_locations(url: str) -> List[Tuple[str, str]]:
    """List the injectable parameters in a URL as ('query'|'fragment', name).

    Single-page apps often keep their route (and parameters) in the fragment,
    e.g. http://host/#/search?q=apple, so both places are checked.
    """
    parsed = urlparse(url)
    found = [("query", k) for k, _ in parse_qsl(parsed.query, keep_blank_values=True)]
    if "?" in parsed.fragment:
        frag_query = parsed.fragment.split("?", 1)[1]
        found += [("fragment", k) for k, _ in parse_qsl(frag_query, keep_blank_values=True)]
    return found


def with_param(url: str, where: str, name: str, value: str) -> str:
    """Return url with parameter `name` (in query or fragment) set to value."""
    parsed = urlparse(url)
    if where == "query":
        pairs = [(k, value if k == name else v)
                 for k, v in parse_qsl(parsed.query, keep_blank_values=True)]
        return urlunparse(parsed._replace(query=urlencode(pairs, quote_via=quote)))
    route, frag_query = parsed.fragment.split("?", 1)
    pairs = [(k, value if k == name else v)
             for k, v in parse_qsl(frag_query, keep_blank_values=True)]
    return urlunparse(parsed._replace(fragment=route + "?" + urlencode(pairs, quote_via=quote)))


def normalise_link(base_url: str, href: str) -> Optional[str]:
    """Absolute same-origin URL for a link, or None if it is not worth testing.

    Hash routes (#/login) are kept because single-page apps use them as pages;
    plain in-page anchors (#top) are dropped.
    """
    if not href or href.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None
    absolute = urljoin(base_url, href)
    parsed, base = urlparse(absolute), urlparse(base_url)
    if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc):
        return None
    if parsed.path.lower().endswith(SKIP_EXTENSIONS):
        return None
    fragment = parsed.fragment if parsed.fragment.startswith(("/", "!/")) else ""
    return urlunparse(parsed._replace(fragment=fragment))


# --------------------------------------------------------------------------- #
# The scanner
# --------------------------------------------------------------------------- #

class ActiveScanner:
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        headless: bool = True,
        allow_external: bool = False,
        max_pages: int = 5,
        max_submissions: int = 80,
        delay: float = 0.3,
        settle_delay: float = 0.4,
        exec_wait: float = 1.2,
        progress: Optional[Callable[[str], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
    ):
        """
        timeout          page-load / script timeout (seconds)
        headless         run Chrome without a visible window
        allow_external   disable the local/private-network restriction
        max_pages        start page + up to (max_pages-1) same-origin pages
        max_submissions  hard cap on payload submissions (rate / scope limit)
        delay            pause between submissions (stops lag looking like DoS)
        settle_delay     wait after load/submit so single-page apps can render
        exec_wait        how long to wait for a payload to execute
        progress         optional callback(str) for status messages (GUI)
        should_stop      optional callback() -> bool; True cancels the scan
        """
        if not SELENIUM_AVAILABLE:
            raise SeleniumNotInstalledError(
                "Selenium is not installed. Run: pip install selenium "
                "(and on Kali: sudo apt install chromium chromium-driver)"
            )
        self.timeout = timeout
        self.headless = headless
        self.allow_external = allow_external
        self.max_pages = max_pages
        self.max_submissions = max_submissions
        self.delay = delay
        self.settle_delay = settle_delay
        self.exec_wait = exec_wait
        self._progress = progress or (lambda msg: None)
        self._should_stop = should_stop or (lambda: False)
        self.driver = None
        self._reset()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def scan(self, url: str) -> Dict:
        assert_target_allowed(url, self.allow_external)
        self._reset()
        started = time.time()
        self.driver = self._make_driver()
        try:
            self._progress("Discovering pages ...")
            pages = self._discover_pages(url)
            for page in pages:
                if self._stopped():
                    break
                self.stats["pages"] += 1
                self._progress(f"Testing {page}")
                self._test_page(page)
        finally:
            self._quit_driver()
        return self._build_report(url, time.time() - started)

    # ------------------------------------------------------------------ #
    # Browser management
    # ------------------------------------------------------------------ #

    def _make_driver(self):
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        for arg in ("--disable-gpu", "--disable-dev-shm-usage", "--window-size=1280,900",
                    f"--user-agent={USER_AGENT}"):
            opts.add_argument(arg)
        if hasattr(os, "geteuid") and os.geteuid() == 0:  # Kali's default root user
            opts.add_argument("--no-sandbox")
        for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
            binary = shutil.which(name)
            if binary:
                opts.binary_location = binary
                break
        driver_path = shutil.which("chromedriver")
        service = Service(executable_path=driver_path) if driver_path else Service()
        try:
            driver = webdriver.Chrome(service=service, options=opts)
        except WebDriverException as exc:
            raise BrowserStartError(
                "Could not start Chrome. Install Chromium + chromedriver "
                "(sudo apt install chromium chromium-driver) and make sure their "
                f"versions match. Details: {str(exc).splitlines()[0]}"
            ) from exc
        driver.set_page_load_timeout(self.timeout)
        driver.set_script_timeout(self.timeout)
        return driver

    def _quit_driver(self) -> None:
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def _stopped(self) -> bool:
        return self._should_stop() or self.stats["payloads_sent"] >= self.max_submissions

    # ------------------------------------------------------------------ #
    # Page loading / discovery
    # ------------------------------------------------------------------ #

    def _load(self, url: str) -> bool:
        """Load a URL and give single-page apps a moment to render."""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete")
        except UnexpectedAlertPresentException:
            self._dismiss_alert()
        except (TimeoutException, WebDriverException):
            return False
        time.sleep(self.settle_delay)
        self._dismiss_overlays()
        return True

    def _dismiss_alert(self) -> None:
        try:
            self.driver.switch_to.alert.dismiss()
        except (NoAlertPresentException, WebDriverException):
            pass

    def _dismiss_overlays(self) -> None:
        for selector in OVERLAY_SELECTORS:
            try:
                for el in self.driver.find_elements(By.CSS_SELECTOR, selector):
                    if el.is_displayed():
                        el.click()
                        time.sleep(0.2)
            except WebDriverException:
                pass

    def _discover_pages(self, start_url: str) -> List[str]:
        pages = [start_url]
        if not self._load(start_url):
            return pages
        try:
            hrefs = [a.get_attribute("href") for a in self.driver.find_elements(By.TAG_NAME, "a")]
        except WebDriverException:
            hrefs = []
        for href in hrefs:
            link = normalise_link(start_url, href or "")
            if link and link not in pages:
                pages.append(link)
            if len(pages) >= self.max_pages:
                break
        return pages

    # ------------------------------------------------------------------ #
    # Testing one page
    # ------------------------------------------------------------------ #

    def _test_page(self, page_url: str) -> None:
        if not self._load(page_url):
            return
        baseline = self._safe_source()
        forms = self.driver.find_elements(By.TAG_NAME, "form")
        for form_index in range(len(forms)):
            if self._stopped():
                return
            self._test_form(page_url, form_index, baseline)
        for where, name in param_locations(page_url):
            if self._stopped():
                return
            self._test_param(page_url, where, name, baseline)

    def _safe_source(self) -> str:
        try:
            return self.driver.page_source or ""
        except WebDriverException:
            return ""

    # ---- forms ---------------------------------------------------------

    def _testable_fields(self, form) -> list:
        fields = []
        for el in form.find_elements(By.CSS_SELECTOR, "input, textarea"):
            kind = (el.get_attribute("type") or "text").lower()
            if (el.tag_name == "textarea" or kind in TEXT_INPUT_TYPES) \
                    and el.is_displayed() and el.is_enabled():
                fields.append(el)
        return fields

    @staticmethod
    def _field_label(el, position: int) -> str:
        for attr in ("name", "id", "placeholder", "aria-label"):
            value = el.get_attribute(attr)
            if value:
                return value
        return f"field {position + 1}"

    @staticmethod
    def _benign_value(el) -> str:
        kind = (el.get_attribute("type") or "text").lower()
        return "webset@example.com" if kind == "email" else "WebSET-test"

    def _fill_form(self, form, target_index: int, payload: str) -> None:
        """Payload goes in ONE field; every other field gets a harmless value,
        so a finding can be pinned to the exact parameter."""
        self.driver.execute_script("arguments[0].setAttribute('novalidate','novalidate')", form)
        text_fields = self._testable_fields(form)
        for i, el in enumerate(text_fields):
            el.clear()
            el.send_keys(payload if i == target_index else self._benign_value(el))
        for el in form.find_elements(By.CSS_SELECTOR, "input[type=password]"):
            if el.is_displayed() and el.is_enabled():
                el.clear()
                el.send_keys("WebSET-Test1!")

    def _submit_form(self, form) -> None:
        buttons = form.find_elements(
            By.CSS_SELECTOR, "button[type=submit], input[type=submit], button:not([type])")
        for button in buttons:
            if button.is_displayed() and button.is_enabled():
                button.click()
                break
        else:
            self.driver.execute_script(
                "var f=arguments[0]; f.requestSubmit ? f.requestSubmit() : f.submit();", form)
        self._settle()

    def _settle(self) -> None:
        try:
            WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete")
        except (TimeoutException, UnexpectedAlertPresentException, WebDriverException):
            self._dismiss_alert()
        time.sleep(self.settle_delay)

    def _test_form(self, page_url: str, form_index: int, baseline: str) -> None:
        forms = self.driver.find_elements(By.TAG_NAME, "form")
        if form_index >= len(forms):
            return
        fields = self._testable_fields(forms[form_index])
        labels = [self._field_label(el, i) for i, el in enumerate(fields)]
        if not fields:
            return
        self.stats["forms"] += 1

        for field_index, label in enumerate(labels):
            location = f"{page_url} -> form #{form_index + 1}, field '{label}'"
            for kind, payload, token in self._attempts():
                if self._stopped():
                    return
                try:
                    if not self._load(page_url):
                        continue
                    form = self.driver.find_elements(By.TAG_NAME, "form")[form_index]
                    self._fill_form(form, field_index, payload)
                    self._submit_form(form)
                except (StaleElementReferenceException, IndexError, WebDriverException):
                    continue  # page changed under us; skip this attempt
                self.stats["payloads_sent"] += 1
                self._evaluate(kind, payload, token, location, baseline)
                time.sleep(self.delay)

        # Boolean-based / authentication-bypass check: only meaningful on
        # login-style forms (a password field present), and only tested on
        # the non-password fields (typically username/email), since that is
        # the field an auth-bypass payload targets.
        has_password = bool(forms[form_index].find_elements(By.CSS_SELECTOR, "input[type=password]"))
        if has_password:
            for field_index, label in enumerate(labels):
                if self._stopped():
                    return
                self._test_boolean_sqli_field(page_url, form_index, field_index, label)

    # ---- boolean-based SQLi (authentication bypass) --------------------

    def _submit_and_snapshot(self, page_url: str, form_index: int, field_index: int,
                              payload: str) -> Optional[Dict]:
        """Load the page fresh, submit `payload` into one field, and record
        where/what we ended up with. Returns None if anything goes wrong
        (page changed, element gone, etc.) so the caller can just skip it."""
        try:
            if not self._load(page_url):
                return None
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            if form_index >= len(forms):
                return None
            form = forms[form_index]
            self._fill_form(form, field_index, payload)
            self._submit_form(form)
            return {"url": self.driver.current_url, "source": self._safe_source()}
        except (StaleElementReferenceException, IndexError, WebDriverException):
            return None

    def _test_boolean_sqli_field(self, page_url: str, form_index: int, field_index: int,
                                  label: str) -> None:
        location = f"{page_url} -> form #{form_index + 1}, field '{label}' (boolean-based SQLi)"
        for true_payload, false_payload in BOOLEAN_SQLI_PAYLOADS:
            if self._stopped():
                return
            true_state = self._submit_and_snapshot(page_url, form_index, field_index, true_payload)
            if true_state is None:
                continue
            false_state = self._submit_and_snapshot(page_url, form_index, field_index, false_payload)
            if false_state is None:
                continue
            # count both submissions against the budget, since _submit_and_snapshot
            # doesn't go through the shared _evaluate() path that normally does this.
            self.stats["payloads_sent"] += 2
            self._evaluate_boolean_sqli(true_payload, false_payload, true_state, false_state, location)
            time.sleep(self.delay)

    def _evaluate_boolean_sqli(self, true_payload: str, false_payload: str,
                                true_state: Dict, false_state: Dict, location: str) -> None:
        # Strongest signal: the TRUE and FALSE conditions land on different
        # pages/URLs (e.g. TRUE logs in and redirects away from /login,
        # FALSE stays on the login page). That's the classic auth-bypass shape.
        if true_state["url"] != false_state["url"]:
            self._add(
                "HIGH", "SQL injection (boolean-based, authentication bypass suspected)", location,
                f"true: {true_payload!r} -> {true_state['url']}  |  "
                f"false: {false_payload!r} -> {false_state['url']}",
                "Submitting an always-true condition produced a different outcome "
                "(a different resulting page/URL) than an always-false condition using "
                "the same syntax. This is the classic signature of a boolean-based SQL "
                "injection, and on a login form it typically means the query can be "
                "manipulated to bypass authentication without needing valid credentials.",
                "Use parameterised queries / prepared statements for all authentication "
                "and data-access logic; never build SQL by concatenating user input. "
                "Confirm manually, since this check infers the bypass from navigation "
                "behaviour rather than reading the database layer directly.",
            )
            return

        # Weaker secondary signal: same URL, but a large difference in the
        # returned content, which can also indicate boolean-based injection
        # (e.g. a results page that changes size depending on the condition).
        len_diff = abs(len(true_state["source"]) - len(false_state["source"]))
        if len_diff > BOOLEAN_LENGTH_DIFF_THRESHOLD:
            self._add(
                "MEDIUM", "Possible SQL injection (boolean-based, response size differs)", location,
                f"true: {true_payload!r} ({len(true_state['source'])} chars)  |  "
                f"false: {false_payload!r} ({len(false_state['source'])} chars)",
                "An always-true and an always-false condition, submitted with the same "
                "syntax, produced responses of noticeably different size on the same "
                "page. This can indicate boolean-based SQL injection, though it may also "
                "be caused by unrelated application state - verify manually.",
                "Use parameterised queries / prepared statements, and confirm this "
                "finding manually (e.g. with Burp or ZAP) before treating it as certain.",
            )

    # ---- URL parameters ------------------------------------------------

    def _test_param(self, page_url: str, where: str, name: str, baseline: str) -> None:
        location = f"{page_url} -> parameter '{name}'"
        for kind, payload, token in self._attempts():
            if self._stopped():
                return
            if not self._load(with_param(page_url, where, name, payload)):
                continue
            self.stats["payloads_sent"] += 1
            self._evaluate(kind, payload, token, location, baseline)
            time.sleep(self.delay)

    # ------------------------------------------------------------------ #
    # Payload attempts and verification
    # ------------------------------------------------------------------ #

    @staticmethod
    def _attempts() -> List[Tuple[str, str, str]]:
        """(kind, payload, token) for every probe. A fresh token per attempt."""
        attempts = []
        for label, template in XSS_PAYLOADS:
            token = uuid.uuid4().hex[:10]
            attempts.append((f"xss:{label}", template.replace("{t}", token), token))
        for probe in SQLI_PROBES:
            attempts.append(("sqli", probe, ""))
        return attempts

    def _evaluate(self, kind: str, payload: str, token: str, location: str, baseline: str) -> None:
        if kind.startswith("xss:"):
            self._evaluate_xss(kind.split(":", 1)[1], payload, token, location)
        else:
            self._evaluate_sqli(payload, location, baseline)

    def _evaluate_xss(self, label: str, payload: str, token: str, location: str) -> None:
        source = self._safe_source()
        if token not in source:
            return  # payload was not reflected at all
        try:
            injected = self.driver.execute_script(
                "return !!document.querySelector(arguments[0]);",
                f'[onerror*="__webset_{token}"],[onload*="__webset_{token}"]')
            executed = self._wait_for_execution(token)
        except WebDriverException:
            return
        if executed:
            self._add("HIGH", "Cross-Site Scripting (confirmed)", location, payload,
                      f"Test payload ({label}) was executed by the browser, confirmed by "
                      "evaluating the live DOM. User input is rendered as active markup.",
                      "Encode all user-controlled output for its context (HTML, attribute, "
                      "JavaScript), validate input server-side, and set a strict "
                      "Content-Security-Policy.")
        elif injected:
            self._add("MEDIUM", "HTML injection (execution not observed)", location, payload,
                      f"Test payload ({label}) was parsed into the page as markup, but script "
                      "execution was not observed (it may be blocked by a CSP or browser "
                      "protection). The underlying injection flaw is still present.",
                      "Encode output for its context; do not rely on CSP alone.")
        else:
            self.stats["reflected_encoded"] += 1  # reflected but safely encoded: not a finding

    def _wait_for_execution(self, token: str) -> bool:
        try:
            WebDriverWait(self.driver, self.exec_wait, poll_frequency=0.1).until(
                lambda d: d.execute_script(f"return window['__webset_{token}'] === 1;"))
            return True
        except TimeoutException:
            return False

    def _evaluate_sqli(self, probe: str, location: str, baseline: str) -> None:
        baseline_hits = {name for name, _ in find_sql_errors(baseline)}
        for database, evidence in find_sql_errors(self._safe_source()):
            if database in baseline_hits:
                continue  # error was already on the page before we probed
            self._add("HIGH", "SQL injection (database error exposed)", location, probe,
                      f"Submitting a lone quote character caused a {database} error message "
                      f"to appear that was not present on the page beforehand "
                      f"(\"{evidence[:80]}\"). Input appears to reach a SQL query unsafely.",
                      "Use parameterised queries / prepared statements, never build SQL by "
                      "string concatenation, and disable verbose database error output.")

    # ------------------------------------------------------------------ #
    # Results
    # ------------------------------------------------------------------ #

    def _add(self, severity, category, location, snippet, description, recommendation) -> None:
        key = (category, location)
        if key in self._seen:
            return
        self._seen.add(key)
        self.findings.append(Finding(
            severity=severity, category=category, location=location, line=None,
            snippet=snippet, description=description, recommendation=recommendation))

    def _reset(self) -> None:
        self.findings: List[Finding] = []
        self._seen: set = set()
        self.stats = {"pages": 0, "forms": 0, "payloads_sent": 0, "reflected_encoded": 0}

    def _build_report(self, url: str, seconds: float) -> Dict:
        ordered = sorted(self.findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 0), reverse=True)
        summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in ordered:
            summary[f.severity] = summary.get(f.severity, 0) + 1
        return {
            "scan_type": "active",
            "target": url,
            "url": url,
            "summary": summary,
            "total_findings": len(ordered),
            "findings": [f.to_dict() for f in ordered],
            "pages_tested": self.stats["pages"],
            "forms_tested": self.stats["forms"],
            "payloads_sent": self.stats["payloads_sent"],
            "reflected_encoded": self.stats["reflected_encoded"],
            "truncated": self.stats["payloads_sent"] >= self.max_submissions,
            "duration_seconds": round(seconds, 1),
        }