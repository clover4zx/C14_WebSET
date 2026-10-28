"""
vulnerable_versions.py

A small, illustrative database of known-vulnerable frontend library version
ranges. This is NOT exhaustive or a substitute for a real CVE feed - it
exists to demonstrate the version-comparison detection technique using
`packaging.version`, and to give WebSET's passive scanner something
concrete to check against out of the box.

Each entry: library name (lowercase, as it typically appears in filenames)
-> list of (max_vulnerable_version, cve_or_advisory, severity, description)
meaning: any detected version <= max_vulnerable_version is flagged.

Extending this file (or replacing it with a live OSV/NVD API lookup) is a
natural next step - see the README for notes on that.
"""

from packaging.version import Version, InvalidVersion

VULNERABLE_LIBRARIES = {
    "jquery": [
        ("1.12.4", "CVE-2020-11022 / CVE-2020-11023", "MEDIUM",
         "Older jQuery versions are vulnerable to XSS via HTML manipulation "
         "methods (e.g. .html(), .append()) when passed untrusted input."),
        ("3.4.1", "CVE-2020-11023", "MEDIUM",
         "jQuery versions before 3.5.0 pass HTML from untrusted sources to "
         "$.html/append/etc. even when disallowed, enabling XSS."),
    ],
    "bootstrap": [
        ("3.4.0", "CVE-2019-8331", "MEDIUM",
         "Bootstrap tooltip/popover data-template attribute is vulnerable "
         "to XSS in versions before 3.4.1 / 4.3.1."),
    ],
    "lodash": [
        ("4.17.20", "CVE-2020-8203 / CVE-2021-23337", "HIGH",
         "Lodash versions before 4.17.21 are vulnerable to prototype "
         "pollution and command injection via template()."),
    ],
    "angular": [
        ("1.7.9", "CVE-2020-7676", "MEDIUM",
         "AngularJS versions before 1.8.0 are vulnerable to DOM-based XSS "
         "via the `templateNamespace` / interpolation of `<textarea>` "
         "and `<title>` elements."),
    ],
    "moment": [
        ("2.29.3", "CVE-2022-31129", "MEDIUM",
         "Moment.js versions before 2.29.4 are vulnerable to ReDoS "
         "(regular expression denial of service) in date parsing."),
    ],
}


def check_version(library: str, version_str: str):
    """
    Returns (advisory_id, severity, description) if the given
    library/version is known-vulnerable, else None.
    """
    library = library.lower()
    if library not in VULNERABLE_LIBRARIES:
        return None

    try:
        detected = Version(version_str)
    except InvalidVersion:
        return None

    for max_vuln_version, advisory, severity, description in VULNERABLE_LIBRARIES[library]:
        try:
            if detected <= Version(max_vuln_version):
                return (advisory, severity, description)
        except InvalidVersion:
            continue
    return None
