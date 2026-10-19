"""
scan_profile.py

WebSET scan profiles: lets a user configure a scan via a human-readable
YAML (or JSON) file instead of long command-line strings - recommended
specifically for security tools since profiles are often shared/reused
across scans and are easier to review than a wall of CLI flags.

Example YAML profile:

    user_agent: "WebSET-PassiveScanner/1.0"
    timeout: 10
    trusted_domains:
      - fonts.googleapis.com
      - cdnjs.cloudflare.com
    excluded_script_types:
      - application/ld+json
    custom_signatures:
      - name: "Internal debug flag"
        pattern: "DEBUG_MODE\\s*=\\s*true"
        severity: HIGH
        description: "Internal debug flag left enabled in shipped page."
        recommendation: "Disable debug mode before deployment."
"""

from __future__ import annotations

import re
import json
import dataclasses
from pathlib import Path
from typing import List, Dict, Set

import yaml

DEFAULT_USER_AGENT = "WebSET-PassiveScanner/1.0 (+authorised-testing-only)"
DEFAULT_TIMEOUT = 10


@dataclasses.dataclass
class ScanProfile:
    user_agent: str = DEFAULT_USER_AGENT
    timeout: int = DEFAULT_TIMEOUT
    trusted_domains: Set[str] = dataclasses.field(default_factory=set)
    excluded_script_types: Set[str] = dataclasses.field(default_factory=set)
    custom_signatures: List[Dict] = dataclasses.field(default_factory=list)

    @classmethod
    def load(cls, path: str) -> "ScanProfile":
        """Load a profile from a .yaml/.yml or .json file."""
        file_path = Path(path)
        raw_text = file_path.read_text()

        if file_path.suffix.lower() in (".yaml", ".yml"):
            data = yaml.safe_load(raw_text) or {}
        elif file_path.suffix.lower() == ".json":
            data = json.loads(raw_text)
        else:
            raise ValueError(
                f"Unsupported profile format: {file_path.suffix} "
                "(use .yaml, .yml or .json)"
            )

        signatures = []
        for sig in data.get("custom_signatures", []):
            compiled = dict(sig)
            compiled["pattern"] = re.compile(sig["pattern"], re.IGNORECASE)
            signatures.append(compiled)

        return cls(
            user_agent=data.get("user_agent", DEFAULT_USER_AGENT),
            timeout=data.get("timeout", DEFAULT_TIMEOUT),
            trusted_domains=set(data.get("trusted_domains", [])),
            excluded_script_types=set(data.get("excluded_script_types", [])),
            custom_signatures=signatures,
        )
