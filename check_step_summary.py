#!/usr/bin/env python3
"""Fetch the check run output for the pytest step to see which tests fail."""
import json
import urllib.request
import sys

REPO = "yuan111-max/skill-tester"
RUN_ID = 27193254290

# Get the check suite for this run
url = f"https://api.github.com/repos/{REPO}/commits/main/check-runs?per_page=20"
req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "python"})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

for cr in data.get("check_runs", []):
    output = cr.get("output") or {}
    name = cr.get("name", "")
    if name in ("test (3.10)", "test (3.11)", "test (3.12)"):
        summary = output.get("summary", "")
        text = output.get("text", "")
        print(f"\n=== {name} ===")
        if summary:
            print(f"SUMMARY ({len(summary)} chars):")
            print(summary[:2000])
        if text:
            print(f"TEXT ({len(text)} chars):")
            print(text[:3000])
        if not summary and not text:
            print("(no output summary)")
            print(f"All output keys: {list(output.keys())}")
