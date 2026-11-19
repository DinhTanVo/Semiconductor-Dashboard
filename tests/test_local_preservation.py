from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def test_data_and_runtime_requirements_unchanged():
 for name,digest in json.loads((ROOT/'V5_PRESERVATION_MANIFEST.json').read_text()).items():
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
def test_no_deployment_dependencies():
 for name in ['render.yaml','wsgi.py','gunicorn.conf.py','requirements-render.txt']:assert not (ROOT/name).exists()
