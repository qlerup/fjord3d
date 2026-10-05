"""Preserve mounted data before updating a pre-Fjord3D installation."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys


def prepare(root: Path) -> bool:
    result = subprocess.run(['docker', 'inspect', 'fjordshare'], capture_output=True, text=True)
    if result.returncode:
        return False
    row = json.loads(result.stdout)[0]
    current = subprocess.run(['docker', 'inspect', 'fjord3d'], capture_output=True, text=True)
    if not current.returncode and json.loads(current.stdout)[0].get('State', {}).get('Running'):
        raise RuntimeError('Fjord3D already runs alongside the legacy container; automatic migration stopped')
    if row.get('Config', {}).get('Labels', {}).get('com.docker.compose.service') != 'fjordshare':
        raise RuntimeError('The legacy container does not belong to the expected app')
    mounts = {m['Destination']: m['Source'] for m in row.get('Mounts', []) if m.get('Type') == 'bind'}
    keys = {'DATA_DIR': '/data', 'UPLOADS_HOST_DIR': '/uploads', 'THUMBS_HOST_DIR': '/thumbs'}
    if not all(mounts.get(target) for target in keys.values()):
        raise RuntimeError('Could not verify all existing data mounts')
    path = root / '.env'
    text = path.read_text(encoding='utf-8') if path.exists() else ''
    values = {key: mounts[target] for key, target in keys.items()}
    values['FJORDHUB_APP_ID'] = 'fjord3d'
    for key, value in values.items():
        if '\n' in value or '\r' in value:
            raise ValueError('Invalid mounted path')
        line = key + '=' + json.dumps(value, ensure_ascii=False)
        pattern = r'(?m)^' + key + '=.*$'
        if re.search(pattern, text):
            text = re.sub(pattern, lambda match: line, text)
        else:
            text = text.rstrip() + '\n' + line + '\n'
    backup = root / '.env.before-fjord3d'
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(text, encoding='utf-8')
    path.chmod(0o600)
    return True


if __name__ == '__main__':
    prepare(Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]))
