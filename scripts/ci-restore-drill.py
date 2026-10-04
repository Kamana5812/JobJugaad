"""Encrypted local CI restore proof, with a process-only key and no uploaded database artifact."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet
from sqlalchemy.engine import make_url
env=dict(os.environ);env['BACKUP_ENCRYPTION_KEY']=Fernet.generate_key().decode()
url=make_url(env['DATABASE_URL'])
if url.host not in ('127.0.0.1','localhost') or url.database!='jobjugaad_test_utf8': raise RuntimeError('Disposable CI database required.')
with tempfile.TemporaryDirectory() as directory:
    path=str(Path(directory)/'snapshot.encrypted')
    subprocess.run([sys.executable,'-m','operations.backup','backup','--path',path,'--colleges','10219'],env=env,check=True)
    env['DATABASE_URL']=url.set(database='jobjugaad_restore_ci').render_as_string(hide_password=False)
    env['ALLOW_RESTORE_DATABASE']='yes'
    subprocess.run([sys.executable,'-m','operations.backup','restore-drill','--path',path],env=env,check=True)
print(json.dumps({'restore_drill':'passed','scope':'Disposable CI tenant only; not a live database backup.'}))

