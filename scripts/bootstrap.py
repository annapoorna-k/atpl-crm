#!/usr/bin/env python3
"""Create local-only secrets without overwriting an existing configuration."""
import secrets
import argparse
from pathlib import Path

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--instance', choices=['US', 'INTERNATIONAL'], default='INTERNATIONAL')
args = parser.parse_args()
us = args.instance == 'US'
env = root / ('.env.us' if us else '.env')
if env.exists():
    print(f'Existing {env.name} preserved.')
else:
    env.write_text(f'COMPOSE_PROJECT_NAME=atplcrm-{"us" if us else "international"}\nINSTANCE_TYPE={args.instance}\nPORT={8083 if us else 8082}\nAPP_SECRET='+secrets.token_urlsafe(48)+'\nPOSTGRES_PASSWORD='+secrets.token_urlsafe(24)+'\nDEMO_PASSWORD='+secrets.token_urlsafe(16)+'\n')
    env.chmod(0o600)
    print(f'Created {env.name} with generated local credentials. Demo email: alex@atplcrm.local. Password is DEMO_PASSWORD in {env.name}.')
