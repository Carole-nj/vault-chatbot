"""List knowledge-base entries that still need verification by Vault Electronics staff.
Run before go-live:  python scripts/check_knowledge_base.py
"""
import json
import re
import sys
from pathlib import Path

kb = json.loads((Path(__file__).resolve().parents[1] / "data" / "knowledge_base.json").read_text(encoding="utf-8"))
todo = []
for name, e in kb["intents"].items():
    placeholders = re.findall(r"\[ADD [^\]]*\]", e["answer"])
    if placeholders or e.get("status") != "verified":
        todo.append((name, e.get("status", "draft"), placeholders))

print(f"{len(todo)} of {len(kb['intents'])} intents are not yet marked status=verified:\n")
for name, status, ph in todo:
    print(f"  - {name:26s} [{status}] {' '.join(ph)}")
print("\nSet \"status\": \"verified\" and remove [ADD ...] markers once Vault has confirmed each answer.")
sys.exit(1 if todo else 0)
