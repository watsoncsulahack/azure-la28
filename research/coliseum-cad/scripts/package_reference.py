"""Package current validated assets without regenerating geometry."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parents[1]
manifest={'revision':'R001','date':'2026-11-27','units':'meters; native FCStd storage millimeters','accuracyStatus':'source consistency checked; +/-0.30 m physical accuracy NOT verified','files':[]}
for directory in ['drawings','models','inputs','reports']:
 for f in sorted((root/directory).rglob('*')):
  if not f.is_file()or f.suffix in ['.FCBak','.FCStd1']:continue
  manifest['files'].append({'path':str(f.relative_to(root)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(root/'coliseum-engineering-reference-R001.zip','w',zipfile.ZIP_DEFLATED)as z:
 for f in sorted(root.rglob('*')):
  if f.is_file()and f.suffix not in ['.zip','.FCBak','.FCStd1','.pyc']and'__pycache__'not in f.parts:z.write(f,f.relative_to(root))
print('Reference package manifest and ZIP written')
