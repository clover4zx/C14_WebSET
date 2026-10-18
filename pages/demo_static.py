"""
demo_static.py

Quick manual test harness for static_zip_analyzer.py.

Builds a small, synthetic "vulnerable website" source ZIP in a temp folder
(deliberately containing a hardcoded AWS key, a plaintext password, an
eval() call, an exposed .env file, etc.) and runs StaticZipAnalyzer against
it, so you can see the tool actually catching things without needing a real
DVWA/Juice Shop export handy yet.

Run with (from the repo root):
    python -m static.demo_static

Or just right-click this file in PyCharm and choose Run.
"""

import json
import shutil
import tempfile
import zipfile
from pathlib import Path

try:
    from .static_zip_analyzer import StaticZipAnalyzer
except ImportError:
    from static_zip_analyzer import StaticZipAnalyzer


def build_sample_vulnerable_zip() -> Path:
    src_dir = Path(tempfile.mkdtemp(prefix="webset_demo_src_"))

    (src_dir / "app.py").write_text(
        "import pickle\n"
        "import subprocess\n\n"
        "AWS_ACCESS_KEY = \"" + "AKIA" + "ABCDEFGHIJKLMNOP" + "\"\n"
        "DB_PASSWORD = \"SuperSecret123!\"\n\n"
        "def load_user_prefs(raw_bytes):\n"
        "    # BUG: unsafe deserialisation of untrusted data\n"
        "    return pickle.loads(raw_bytes)\n\n"
        "def run_backup(filename):\n"
        "    # BUG: shell=True with a filename that could be user-controlled\n"
        "    subprocess.call(f\"tar -czf backup.tar.gz {filename}\", shell=True)\n\n"
        "def debug_eval(expr):\n"
        "    return eval(expr)\n"
    )

    (src_dir / "login.php").write_text(
        "<?php\n"
        "$user = $_POST['username'];\n"
        "$pass = $_POST['password'];\n"
        "$query = \"SELECT * FROM users WHERE username = '\" + $user + \"'\";\n"
        "system($_GET['cmd']);\n"
        "?>\n"
    )

    (src_dir / "main.js").write_text(
        "function renderComment(comment) {\n"
        "  document.getElementById('out').innerHTML = comment;\n"
        "}\n"
    )

    (src_dir / ".env").write_text(
        "SECRET_KEY=prod-secret-please-dont-leak-1234567890\n"
        "DEBUG=True\n"
    )

    (src_dir / "requirements.txt").write_text("flask==2.0.1\nrequests==2.25.0\n")

    (src_dir / "old_dump.sql").write_text("-- pretend sql dump\nSELECT 1;\n")

    zip_path = Path(tempfile.mkdtemp(prefix="webset_demo_zip_")) / "sample_site.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in src_dir.rglob("*"):
            if file.is_file():
                zf.write(file, arcname=file.relative_to(src_dir))

    shutil.rmtree(src_dir, ignore_errors=True)
    return zip_path


def main():
    sample_zip = build_sample_vulnerable_zip()
    print(f"Built sample vulnerable zip at: {sample_zip}\n")

    analyzer = StaticZipAnalyzer(str(sample_zip))
    report = analyzer.analyze()

    print("=" * 70)
    print(f"Tech stack detected : {report['tech_stack']}")
    print(f"Dependencies found  : {len(report['dependencies'])}")
    for dep in report["dependencies"]:
        print(f"   - [{dep['manager']}] {dep['package']}")
    print(f"Total findings      : {report['total_findings']}")
    print(f"Severity summary    : {report['summary']}")
    print("=" * 70)

    for finding in report["findings"]:
        print(f"\n[{finding['severity']}] {finding['category']}")
        print(f"  Location: {finding['location']}" + (f":{finding['line']}" if finding['line'] else ""))
        if finding["snippet"]:
            print(f"  Snippet: {finding['snippet']}")
        print(f"  Why it matters: {finding['description']}")
        print(f"  Fix: {finding['recommendation']}")

    out_path = Path("sample_report.json")
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\nFull JSON report written to: {out_path.resolve()}")

    shutil.rmtree(sample_zip.parent, ignore_errors=True)


if __name__ == "__main__":
    main()
