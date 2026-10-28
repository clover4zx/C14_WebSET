"""
static_zip_analyzer.py

WebSET - Week 8 milestone: "Implement static ZIP file analysis"

Takes a ZIP upload of a website's/app's source code and performs STATIC
analysis on it (i.e. it never executes any of the extracted code). It looks
for:

    1. Hardcoded secrets (API keys, private keys, passwords, tokens)
    2. Risky / dangerous code patterns (eval, exec, insecure deserialisation...)
    3. Exposed sensitive files that should never ship (.env, .git, backups...)
    4. Declared dependencies (from requirements.txt / package.json / composer.json)
    5. A best-effort tech-stack guess, based on marker files present

It is deliberately defensive about the ZIP itself: it guards against
zip-slip (path traversal) and zip-bomb (decompression bomb) attacks, since
this tool will often be fed untrusted uploads.

Usage:
    from scanner.static_zip_analyzer import StaticZipAnalyzer

    analyzer = StaticZipAnalyzer("uploaded_site.zip")
    report = analyzer.analyze()

    print(report["tech_stack"])
    for finding in report["findings"]:
        print(finding["severity"], finding["category"], finding["location"])

The returned `report` dict is plain JSON-serialisable, so it can be handed
straight to the SQLite logging layer or rendered in the PyQt GUI.
"""

from __future__ import annotations

import os
import re
import json
import shutil
import zipfile
import tempfile
import dataclasses
from pathlib import Path
from typing import List, Dict, Optional, Iterable


MAX_TOTAL_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
MAX_SINGLE_FILE_BYTES = 25 * 1024 * 1024
MAX_FILE_COUNT = 5000
MAX_COMPRESSION_RATIO = 100

SCANNABLE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".php", ".rb", ".java", ".go",
    ".html", ".htm", ".css", ".json", ".yml", ".yaml", ".env", ".ini",
    ".cfg", ".conf", ".xml", ".sh", ".sql", ".txt", ".md", ".toml",
}

SEVERITY_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}


@dataclasses.dataclass
class Finding:
    severity: str
    category: str
    location: str
    line: Optional[int]
    snippet: str
    description: str
    recommendation: str

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)


SECRET_PATTERNS = [
    (
        "AWS Access Key ID",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "HIGH",
        "A hardcoded AWS Access Key ID was found in source.",
        "Revoke this key immediately and load credentials from environment "
        "variables or a secrets manager instead of committing them to code.",
    ),
    (
        "Generic Private Key",
        re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PGP)?\s?PRIVATE KEY-----"),
        "HIGH",
        "A private key block was found committed in source.",
        "Remove the key from source control, rotate/regenerate it, and store "
        "keys outside the repository (e.g. a secrets vault or CI secret store).",
    ),
    (
        "Slack Token",
        re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,48}\b"),
        "HIGH",
        "A Slack API token was found hardcoded in source.",
        "Revoke the token in Slack's admin console and load it from an "
        "environment variable instead.",
    ),
    (
        "Generic API Key / Secret Assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|client[_-]?secret)"
            r"\s*[:=]\s*['\"][A-Za-z0-9_\-/+=]{12,}['\"]"
        ),
        "MEDIUM",
        "A variable that looks like an API key or secret is hardcoded.",
        "Move this value to an environment variable or a secrets manager, "
        "and add the config file to .gitignore.",
    ),
    (
        "Hardcoded Password Assignment",
        re.compile(
            r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{4,}['\"]"
        ),
        "MEDIUM",
        "A password appears to be hardcoded directly in source.",
        "Never store credentials in source. Use environment variables, a "
        ".env file excluded from version control, or a secrets manager.",
    ),
    (
        "JWT-like Token",
        re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
        "MEDIUM",
        "A JSON Web Token (JWT) was found hardcoded in source.",
        "Do not commit real tokens to source. If this is a test/sample "
        "token confirm it has no real access before ignoring.",
    ),
    (
        "Database Connection String with Credentials",
        re.compile(
            r"(?i)\b(mysql|postgres(?:ql)?|mongodb|redis)://[^\s'\"]+:[^\s'\"@]+@"
        ),
        "HIGH",
        "A database connection string with an embedded username/password "
        "was found.",
        "Externalise the connection string via environment variables and "
        "rotate the exposed database credentials.",
    ),
]

CODE_PATTERNS = [
    (
        "Use of eval()",
        {".py", ".js", ".jsx", ".ts", ".tsx", ".php"},
        re.compile(r"\beval\s*\("),
        "HIGH",
        "eval() executes arbitrary code from a string and is a common "
        "injection vector if any part of the input is user-controlled.",
        "Avoid eval(). Use safer alternatives (e.g. json.loads for data, "
        "explicit dispatch tables for logic).",
    ),
    (
        "Use of exec()",
        {".py", ".php"},
        re.compile(r"\bexec\s*\("),
        "HIGH",
        "exec() runs arbitrary code and is dangerous if fed external input.",
        "Avoid exec(). Refactor to avoid dynamic code execution entirely.",
    ),
    (
        "Insecure Deserialisation (pickle)",
        {".py"},
        re.compile(r"\bpickle\.loads?\s*\("),
        "HIGH",
        "pickle can execute arbitrary code during deserialisation of "
        "untrusted data.",
        "Use a safe serialisation format like JSON for untrusted data. If "
        "pickle is required, never load data from an untrusted source.",
    ),
    (
        "Unsafe YAML Load",
        {".py"},
        re.compile(r"\byaml\.load\s*\((?!.*Loader\s*=\s*yaml\.SafeLoader)"),
        "MEDIUM",
        "yaml.load() without a SafeLoader can execute arbitrary Python "
        "objects from untrusted YAML.",
        "Use yaml.safe_load() or explicitly pass Loader=yaml.SafeLoader.",
    ),
    (
        "Shell Command with shell=True",
        {".py"},
        re.compile(r"subprocess\.\w+\([^)]*shell\s*=\s*True"),
        "MEDIUM",
        "Running shell commands with shell=True is a common injection risk "
        "if any argument includes untrusted input.",
        "Avoid shell=True; pass command arguments as a list instead, and "
        "validate/sanitise any user-supplied values.",
    ),
    (
        "PHP eval/system family",
        {".php"},
        re.compile(r"\b(system|passthru|shell_exec|proc_open)\s*\("),
        "HIGH",
        "Direct shell execution functions are present and are common "
        "remote-code-execution vectors if fed user input.",
        "Avoid shelling out with user-controlled input. Use safe, "
        "parameterised library functions instead.",
    ),
    (
        "PHP Superglobal Extraction",
        {".php"},
        re.compile(r"\bextract\s*\(\s*\$_(GET|POST|REQUEST)\b"),
        "HIGH",
        "extract() on user input dumps request data straight into local "
        "variables, which can override application logic (variable "
        "injection).",
        "Never call extract() on request superglobals. Explicitly "
        "whitelist and validate each expected input.",
    ),
    (
        "Potential SQL string concatenation",
        {".py", ".php", ".js", ".rb"},
        re.compile(
            r"(select|insert|update|delete)\b[^;\"']*['\"]\s*\+\s*\w+|"
            r"(select|insert|update|delete)\b.*\.\s*format\s*\(",
            re.IGNORECASE,
        ),
        "MEDIUM",
        "A SQL statement appears to be built via string concatenation or "
        ".format(), which is a classic SQL-injection vector.",
        "Use parameterised queries / prepared statements instead of "
        "building SQL via string concatenation.",
    ),
    (
        "innerHTML assignment from variable",
        {".js", ".jsx", ".ts", ".tsx", ".html", ".htm"},
        re.compile(r"\.innerHTML\s*=\s*[^'\"][^;]*;"),
        "LOW",
        "Assigning to innerHTML from a variable can lead to XSS if the "
        "value includes unsanitised user input.",
        "Use textContent for plain text, or a sanitisation library "
        "(e.g. DOMPurify) before inserting HTML.",
    ),
    (
        "Debug Mode Enabled",
        {".py", ".ini", ".cfg", ".env"},
        re.compile(r"(?i)\bDEBUG\s*[:=]\s*(True|1|\"true\"|'true')\b"),
        "LOW",
        "Debug mode appears to be enabled, which can leak stack traces, "
        "source paths, and configuration to attackers in production.",
        "Ensure DEBUG is disabled in any production configuration.",
    ),
]

SENSITIVE_FILE_PATTERNS = [
    (re.compile(r"^\.env(\..+)?$"), "HIGH",
     "Environment file containing configuration/secrets."),
    (re.compile(r"^\.git$", re.IGNORECASE), "HIGH",
     "Exposed .git directory can leak entire source & commit history."),
    (re.compile(r"^id_rsa$|^id_dsa$|.*\.pem$|.*\.key$"), "HIGH",
     "Private key material should never be bundled with a deployment."),
    (re.compile(r"wp-config\.php$"), "HIGH",
     "WordPress config file containing DB credentials."),
    (re.compile(r"^config(\.local)?\.(php|json|yml|yaml)$"), "MEDIUM",
     "Configuration file that may contain sensitive settings."),
    (re.compile(r".*\.(bak|backup|old|orig)$"), "MEDIUM",
     "Backup file left in the deployment; may contain stale secrets or "
     "leak source code."),
    (re.compile(r".*\.sql$"), "MEDIUM",
     "Raw SQL dump file - may expose schema and/or real data."),
    (re.compile(r"^\.htpasswd$"), "HIGH",
     "Exposed HTTP basic-auth credential file."),
    (re.compile(r"^Dockerfile$|docker-compose\.ya?ml$"), "INFO",
     "Infrastructure file present - review for hardcoded secrets/ports."),
]

TECH_STACK_MARKERS = {
    "package.json": "Node.js / JavaScript",
    "requirements.txt": "Python",
    "Pipfile": "Python",
    "pyproject.toml": "Python",
    "composer.json": "PHP",
    "Gemfile": "Ruby",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java/Kotlin (Gradle)",
    "go.mod": "Go",
    "wp-config.php": "WordPress",
    "artisan": "Laravel (PHP)",
    "manage.py": "Django (Python)",
    "next.config.js": "Next.js (React)",
    "angular.json": "Angular",
}

DEPENDENCY_FILES = {
    "requirements.txt": "pip",
    "package.json": "npm",
    "composer.json": "composer",
}


class ZipSafetyError(Exception):
    """Raised when a ZIP fails basic safety checks (zip-slip / zip-bomb)."""


class StaticZipAnalyzer:
    def __init__(
        self,
        zip_path: str,
        work_dir: Optional[str] = None,
        cleanup: bool = True,
    ):
        """
        zip_path: path to the uploaded .zip file to analyze
        work_dir: optional directory to extract into. If not given, a
                  temporary directory is created and removed after analysis
                  (unless cleanup=False).
        cleanup:  whether to delete the extracted files after analyze()
                  finishes. Set False if you want to inspect the extracted
                  tree afterwards.
        """
        self.zip_path = Path(zip_path)
        self._owns_temp_dir = work_dir is None
        self.work_dir = Path(work_dir) if work_dir else Path(
            tempfile.mkdtemp(prefix="webset_zipscan_")
        )
        self.cleanup = cleanup
        self.findings: List[Finding] = []

        if not self.zip_path.is_file():
            raise FileNotFoundError(f"ZIP not found: {self.zip_path}")


    def analyze(self) -> Dict:
        """Run the full static analysis pipeline and return a report dict."""
        try:
            self._safe_extract()
            tech_stack = self._detect_tech_stack()
            dependencies = self._collect_dependencies()

            for file_path in self._iter_scannable_files():
                self._scan_file_for_secrets(file_path)
                self._scan_file_for_code_patterns(file_path)

            self._scan_sensitive_filenames()

            return self._build_report(tech_stack, dependencies)
        finally:
            if self.cleanup and self._owns_temp_dir:
                shutil.rmtree(self.work_dir, ignore_errors=True)


    def _safe_extract(self) -> None:
        """
        Extract the ZIP defensively:
          - reject path traversal ("zip-slip") entries
          - reject absolute paths
          - enforce total/individual size limits (zip-bomb protection)
          - enforce a maximum file count
        """
        self.work_dir.mkdir(parents=True, exist_ok=True)
        total_uncompressed = 0
        file_count = 0

        with zipfile.ZipFile(self.zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue

                file_count += 1
                if file_count > MAX_FILE_COUNT:
                    raise ZipSafetyError(
                        f"ZIP contains more than {MAX_FILE_COUNT} files - refusing "
                        "to extract (possible zip bomb)."
                    )

                target_path = (self.work_dir / info.filename).resolve()
                if not str(target_path).startswith(str(self.work_dir.resolve())):
                    raise ZipSafetyError(
                        f"Unsafe path traversal detected in ZIP entry: "
                        f"{info.filename!r}"
                    )

                if info.file_size > MAX_SINGLE_FILE_BYTES:
                    continue

                total_uncompressed += info.file_size
                if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
                    raise ZipSafetyError(
                        "Total uncompressed size exceeds safety limit - "
                        "refusing to extract (possible zip bomb)."
                    )

                if info.compress_size > 0:
                    ratio = info.file_size / max(info.compress_size, 1)
                    if ratio > MAX_COMPRESSION_RATIO:
                        raise ZipSafetyError(
                            f"Suspicious compression ratio ({ratio:.0f}x) on "
                            f"{info.filename!r} - refusing to extract "
                            "(possible zip bomb)."
                        )

                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)


    def _detect_tech_stack(self) -> List[str]:
        found = set()
        for path in self.work_dir.rglob("*"):
            if path.is_file() and path.name in TECH_STACK_MARKERS:
                found.add(TECH_STACK_MARKERS[path.name])
        return sorted(found) if found else ["Unknown / static HTML"]

    def _collect_dependencies(self) -> List[Dict]:
        deps: List[Dict] = []
        for path in self.work_dir.rglob("*"):
            if not path.is_file() or path.name not in DEPENDENCY_FILES:
                continue
            manager = DEPENDENCY_FILES[path.name]
            try:
                if path.name == "requirements.txt":
                    for line in path.read_text(errors="ignore").splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            deps.append({"manager": manager, "package": line})
                elif path.name == "package.json":
                    data = json.loads(path.read_text(errors="ignore"))
                    for section in ("dependencies", "devDependencies"):
                        for name, version in data.get(section, {}).items():
                            deps.append({
                                "manager": manager,
                                "package": f"{name}@{version}",
                            })
                elif path.name == "composer.json":
                    data = json.loads(path.read_text(errors="ignore"))
                    for name, version in data.get("require", {}).items():
                        deps.append({
                            "manager": manager,
                            "package": f"{name}:{version}",
                        })
            except (json.JSONDecodeError, OSError):
                self.findings.append(Finding(
                    severity="LOW",
                    category="Malformed Dependency Manifest",
                    location=str(path.relative_to(self.work_dir)),
                    line=None,
                    snippet="",
                    description=f"Could not parse {path.name} - it may be "
                                "malformed or corrupted.",
                    recommendation="Verify the manifest file is valid.",
                ))
        return deps


    def _iter_scannable_files(self) -> Iterable[Path]:
        for path in self.work_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SCANNABLE_EXTENSIONS:
                continue
            try:
                if path.stat().st_size > MAX_SINGLE_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield path

    def _scan_file_for_secrets(self, path: Path) -> None:
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            return

        rel_path = str(path.relative_to(self.work_dir))
        for line_no, line in enumerate(text.splitlines(), start=1):
            for name, pattern, severity, description, recommendation in SECRET_PATTERNS:
                match = pattern.search(line)
                if match:
                    self.findings.append(Finding(
                        severity=severity,
                        category=f"Hardcoded Secret: {name}",
                        location=rel_path,
                        line=line_no,
                        snippet=self._redact(line, match.span()),
                        description=description,
                        recommendation=recommendation,
                    ))

    def _scan_file_for_code_patterns(self, path: Path) -> None:
        ext = path.suffix.lower()
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            return

        rel_path = str(path.relative_to(self.work_dir))
        for name, extensions, pattern, severity, description, recommendation in CODE_PATTERNS:
            if ext not in extensions:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    self.findings.append(Finding(
                        severity=severity,
                        category=f"Risky Pattern: {name}",
                        location=rel_path,
                        line=line_no,
                        snippet=line.strip()[:160],
                        description=description,
                        recommendation=recommendation,
                    ))

    def _scan_sensitive_filenames(self) -> None:
        for path in self.work_dir.rglob("*"):
            name = path.name
            rel_path = str(path.relative_to(self.work_dir))
            for pattern, severity, description in SENSITIVE_FILE_PATTERNS:
                if pattern.match(name):
                    self.findings.append(Finding(
                        severity=severity,
                        category="Exposed Sensitive File",
                        location=rel_path,
                        line=None,
                        snippet="",
                        description=description,
                        recommendation=f"Remove '{name}' from the deployed "
                                       "package and ensure it is excluded "
                                       "via .gitignore / build config.",
                    ))

    @staticmethod
    def _redact(line: str, span: tuple) -> str:
        """Return a line with the matched secret masked out, for safe display."""
        start, end = span
        return (line[:start] + "[REDACTED]" + line[end:]).strip()[:160]


    def _build_report(self, tech_stack: List[str], dependencies: List[Dict]) -> Dict:
        findings_sorted = sorted(
            self.findings,
            key=lambda f: SEVERITY_ORDER.get(f.severity, 0),
            reverse=True,
        )
        summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in findings_sorted:
            summary[f.severity] = summary.get(f.severity, 0) + 1

        return {
            "scan_type": "static",
            "target": self.zip_path.name,
            "zip_file": self.zip_path.name,
            "tech_stack": tech_stack,
            "dependencies": dependencies,
            "summary": summary,
            "total_findings": len(findings_sorted),
            "findings": [f.to_dict() for f in findings_sorted],
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python static_zip_analyzer.py <path-to-zip>")
        sys.exit(1)

    analyzer = StaticZipAnalyzer(sys.argv[1])
    report = analyzer.analyze()
    print(json.dumps(report, indent=2))
