"""Generate V6-style reports without changing the V5 local application."""
import argparse
from reporting.src.export_reports import export
if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--executable", "--browser-executable", default=None, help="Optional Chromium executable path")
    p.add_argument("--notes-json", default=None)
    a=p.parse_args()
    export(a.executable,a.notes_json)
