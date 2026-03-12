import os
import sys
from pathlib import Path

# Load master.env
env_path = Path("../../_knowledge/credentials/master.env")
if env_path.exists():
    for line in open(env_path):
        line = line.strip()
        if line and not line.startswith('#'):
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ[k] = v.strip('"\' ')

# Update missing SMTP_APP_PASSWORD correctly if it was unquoted
if os.environ.get('SMTP_APP_PASSWORD', '') == 'iumv':
    os.environ['SMTP_APP_PASSWORD'] = 'iumv zqsf qpnc yiqx'

# Inject Google SA
sa_path = Path("../../_knowledge/credentials/google-service-account.json")
if sa_path.exists():
    os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'] = sa_path.read_text()

sys.argv = ['run_test.py', '--once']

import main
main.main()
