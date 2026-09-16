#!/usr/bin/env python3
"""Measure the local ATPLCRM scale acceptance endpoints without printing credentials."""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--instance", choices=["INTERNATIONAL", "US"], default="INTERNATIONAL")
parser.add_argument("--env-file", default="", help="Use a disposable Compose env file instead of the selected live-demo env.")
parser.add_argument("--report", default="")
args = parser.parse_args(); env_path = Path(args.env_file).resolve() if args.env_file else ROOT / (".env.us" if args.instance == "US" else ".env")
env = dict(line.split("=", 1) for line in env_path.read_text().splitlines() if line and not line.startswith("#") and "=" in line)
base = f"http://127.0.0.1:{env.get('PORT', '8082')}/api/v1/"
jar = http.cookiejar.CookieJar(); opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

def request(path, method="GET", body=None, csrf=""):
    payload = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if csrf: headers["X-CSRFToken"] = csrf
    with opener.open(urllib.request.Request(base + path, data=payload, headers=headers, method=method), timeout=30) as response: return json.loads(response.read())

csrf = request("session/")["csrf"]
csrf = request("session/", "POST", {"username": "alex@atplcrm.local", "password": env["DEMO_PASSWORD"]}, csrf)["csrf"]
checks = [
    ("Board/bootstrap working set", "bootstrap/", 2.0),
    ("Contact list", "productivity/lists/contacts/?page=1&page_size=25", 2.0),
    ("Opportunity list", "productivity/lists/opportunities/?page=1&page_size=25", 2.0),
    ("Ranked broad search", "data/search/?q=Scale%20Benchmark&page=1&page_size=20", 3.5),
    ("Full management report", "reports/analytics/?period=all", 10.0),
]
results=[]
for name, path, target in checks:
    started=time.perf_counter(); data=request(path); elapsed=time.perf_counter()-started
    count = data.get("total", len(data.get("records", [])))
    if name.startswith("Board/"): count = data.get("workspace_counts", {}).get("pursuits", 0)
    results.append({"check":name,"seconds":round(elapsed,3),"target_seconds":target,"passed":elapsed<=target,"records":count})
print(json.dumps(results, indent=2))
if args.report: Path(args.report).write_text(json.dumps({"instance":args.instance,"results":results},indent=2)+"\n")
if not all(row["passed"] for row in results): raise SystemExit("One or more scale targets were missed.")
