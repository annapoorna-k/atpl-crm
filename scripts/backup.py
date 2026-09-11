#!/usr/bin/env python3
"""Back up the current Compose project's PostgreSQL database without printing credentials."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parent.parent
folder=root/'backups'
folder.mkdir(exist_ok=True)
target=folder/('atplcrm-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.dump')
with target.open('wb') as output:
    result=subprocess.run(['docker','compose','exec','-T','db','pg_dump','-U','atplcrm','-d','atplcrm','-Fc'],cwd=root,stdout=output)
if result.returncode:
    raise SystemExit('Backup failed. The incomplete file must not be used for restore.')
target.chmod(0o600)
print(f'Backup written: {target}. Restore rehearsal is required before production use.')
