"""
Tele Satış CRM — Hızlı Test Koşturucusu
Tek döngü modunda çalıştırarak sistemi test eder.

Kullanım:
    python run_test.py

Not: .env dosyasının doğru yapılandırılmış olması gerekir.
"""
import os
import sys

# .env dosyasından environment variable'ları yükle
from pathlib import Path
env_path = Path(".env")
if env_path.exists():
    for line in open(env_path):
        line = line.strip()
        if line and not line.startswith('#'):
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ[k] = v.strip('"\' ')

sys.argv = ['run_test.py', '--once']

import main
main.main()
