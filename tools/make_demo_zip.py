"""
make_demo_zip.py
Creates a small sample "vulnerable" source-code .zip you can upload in the
Static tab for a demo. Run once:  python make_demo_zip.py
It writes sample_vulnerable_site.zip next to this script and prints its path.
"""
import zipfile
from pathlib import Path

FILES = {
    "app.py": (
        "import pickle, subprocess\n"
        'AWS_ACCESS_KEY = "AKIAABCDEFGHIJKLMNOP"\n'
        'DB_PASSWORD = "SuperSecret123!"\n'
        "def load_prefs(raw):\n"
        "    return pickle.loads(raw)  # unsafe deserialisation\n"
        "def backup(name):\n"
        '    subprocess.call(f"tar -czf b.tar.gz {name}", shell=True)\n'
        "def run(expr):\n"
        "    return eval(expr)\n"
    ),
    "login.php": (
        "<?php\n"
        "$user = $_POST['username'];\n"
        "$query = \"SELECT * FROM users WHERE username = '\" + $user + \"'\";\n"
        "system($_GET['cmd']);\n"
        "?>\n"
    ),
    "main.js": "function render(c){ document.getElementById('o').innerHTML = c; }\n",
    ".env": "SECRET_KEY=prod-secret-please-dont-leak-1234567890\nDEBUG=True\n",
    "requirements.txt": "flask==2.0.1\nrequests==2.25.0\n",
    "old_dump.sql": "-- pretend dump\nSELECT 1;\n",
}

out = Path(__file__).parent / "sample_vulnerable_site.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for name, body in FILES.items():
        zf.writestr(name, body)

print("Created:", out.resolve())
