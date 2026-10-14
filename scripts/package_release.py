"""Build an installable archive from the public runtime file allowlist."""
from pathlib import Path
import hashlib
import tomllib
import zipfile

root = Path(__file__).resolve().parents[1]
version = tomllib.loads((root / 'pyproject.toml').read_text())['project']['version']
files = ['__init__.py', 'plugin.py', 'generation.py', 'request_retry.py', 'triggers.py', 'delivery.py', 'prompts.py', 'gallery_upload.py', 'denia_outbox.py', 'denia_classification.py', 'LICENSE', 'pyproject.toml', 'README.md']
destination = root / 'dist'
destination.mkdir(exist_ok=True)
archive = destination / f'denia-novelai-{version}.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as package:
    for name in files:
        package.write(root / name, 'denia_novelai/' + name)
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.sha256').write_text(digest + '  ' + archive.name + '\n')
print(archive)
print('SHA256: ' + digest)
