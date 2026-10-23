#!/usr/bin/env python3
"""Print the outcome of the last capture run (used by the workflow summary)."""
import json
import pathlib

p = pathlib.Path(__file__).resolve().parent.parent / "data" / "ledger" / "manifest.json"
if not p.exists():
    print("manifest missing")
    raise SystemExit(0)
m = json.loads(p.read_text(encoding="utf-8"))
run = m.get("last_run", {})
for r in run.get("results", []):
    print(f"{r.get('status')} {r.get('key')} {r.get('error', '')}")
ok = sum(1 for r in run.get("results", []) if r.get("status") == 200)
print(f"{ok}/{len(run.get('results', []))} HTTP 200")
