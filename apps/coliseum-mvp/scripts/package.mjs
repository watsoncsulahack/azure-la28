import {readFile,writeFile,mkdir,readdir} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
const root=new URL('../',import.meta.url);
const spec=JSON.parse(await readFile(new URL('dist/data/venue.json',root)));
const manifest={...spec,researchUrl:'https://github.com/watsoncsulahack/azure-la28/tree/main/research/coliseum-dimensions',referenceDrawingInspected:'S01 PDF p.5 site plan visually inspected; no metric registration or traced outline.'};
await writeFile(new URL('dist/data/manifest.json',root),JSON.stringify(manifest,null,2)+'\n');
const result=spawnSync('python',['-c',`from pathlib import Path
import zipfile
root=Path(${JSON.stringify(root.pathname)})
with zipfile.ZipFile(root/'dist/coliseum-mvp-source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ['README.md','package.json','scripts','dist']:
  p=root/name
  for f in ([p] if p.is_file() else sorted(p.rglob('*'))):
   if f.is_file() and f.suffix!='.zip': z.write(f,f.relative_to(root))
print('Source ZIP packaged')`],{stdio:'inherit'});
if(result.status!==0)process.exit(result.status??1);
