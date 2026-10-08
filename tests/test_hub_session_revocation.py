"""Run the real app's auth hooks against an isolated database and mocked Hub."""
import os
from pathlib import Path
import subprocess
import sys


def test_active_session_revocation_and_outage(tmp_path):
    env = {**os.environ, 'DATA_DIR': str(tmp_path), 'FJORDHUB_URL': 'http://hub.test',
           'FJORDHUB_API_KEY': 'fixture-key', 'FJORDHUB_APP_ID': 'fjord3d'}
    script = '''
import app
people = [{'id':77, 'username':'Alice', 'role':'user'}]
app._hub_api = lambda *a, **kw: {'ok':True, 'items':people.copy()}
user = app._ensure_managed_local_user(people[0])
client = app.app.test_client()
assert b'hub-session.js' in client.get('/login').data
with client.session_transaction() as session:
    session.update(_user_id=str(user.id), _fresh=True, hub_user_id=77)
assert client.get('/api/auth/access').json['authenticated'] is True
snapshot = app.app.extensions['hub_session_snapshot']
snapshot.expires = 0
app._hub_api = lambda *a, **kw: {'ok':False}
assert client.get('/api/auth/access').status_code == 503
with client.session_transaction() as session:
    assert session['_user_id'] == str(user.id)
app._hub_api = lambda *a, **kw: {'ok':True, 'items':[]}
denied = client.get('/api/auth/access')
assert denied.status_code == 401 and denied.json['error_code'] == 'access_revoked'
assert client.get('/api/auth/access').json['error_code'] == 'access_revoked'
assert client.get('/api/files').status_code == 401
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=Path(__file__).resolve().parents[1],
                            env=env, capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
