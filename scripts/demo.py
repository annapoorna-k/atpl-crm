#!/usr/bin/env python3
"""Operate a safe, repeatable ATPLCRM local client-demo workspace."""
from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent


def env_path(instance: str) -> Path:
    return ROOT / (".env.us" if instance == "US" else ".env")


def values(path: Path) -> dict[str, str]:
    if not path.exists(): raise SystemExit(f"{path.name} does not exist. Run scripts/bootstrap.py first.")
    result = {}
    for line in path.read_text().splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1); result[key] = value
    project = result.get("COMPOSE_PROJECT_NAME", "")
    if project not in {"atplcrm-international", "atplcrm-us"}: raise SystemExit("Refusing to operate an unexpected Compose project.")
    return result


def compose(path: Path, *args: str, capture=False):
    return subprocess.run(["docker", "compose", "--env-file", str(path), *args], cwd=ROOT, check=True, capture_output=capture, text=capture)


def backup(path: Path, project: str, reason: str = "backup") -> Path:
    folder = ROOT / "backups"; folder.mkdir(exist_ok=True)
    target = folder / f"{project}-{reason}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.dump"
    with target.open("wb") as output:
        subprocess.run(["docker", "compose", "--env-file", str(path), "exec", "-T", "db", "pg_dump", "-U", "atplcrm", "-d", "atplcrm", "-Fc"], cwd=ROOT, check=True, stdout=output)
    target.chmod(0o600); return target


def status(path: Path, config: dict[str, str]):
    port = config.get("PORT", "8082")
    with urlopen(f"http://127.0.0.1:{port}/api/health/", timeout=5) as response:
        print(f"{config['COMPOSE_PROJECT_NAME']}: HTTP {response.status}, {response.read().decode()}")
    print("Credentials: use a documented @atplcrm.local account and DEMO_PASSWORD from the selected env file.")


def reset(path: Path, config: dict[str, str], confirmation: str, skip_backup: bool):
    if confirmation != "RESET-ATPLCRM": raise SystemExit("Reset cancelled. Pass --confirm RESET-ATPLCRM to destroy and recreate this demo database.")
    if not skip_backup:
        target = backup(path, config["COMPOSE_PROJECT_NAME"], "before-reset"); print(f"Safety backup: {target}")
    compose(path, "down", "--volumes", "--remove-orphans")
    compose(path, "up", "-d", "--build", "--wait")
    print(f"Reset complete: http://127.0.0.1:{config.get('PORT', '8082')}")


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("command", choices=["status", "backup", "reset"])
parser.add_argument("--instance", choices=["INTERNATIONAL", "US"], default="INTERNATIONAL")
parser.add_argument("--confirm", default="")
parser.add_argument("--skip-backup", action="store_true")
args = parser.parse_args(); path = env_path(args.instance); config = values(path)
if args.command == "status":
    status(path, config)
elif args.command == "backup":
    print(f"Backup written: {backup(path, config['COMPOSE_PROJECT_NAME'])}")
else:
    reset(path, config, args.confirm, args.skip_backup)
