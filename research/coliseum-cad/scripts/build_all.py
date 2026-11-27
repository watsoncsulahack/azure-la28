"""Reproduce the CAD reference package with separate FreeCAD and CAD-tool Python runtimes."""
import argparse,subprocess,sys,os,hashlib,json,zipfile
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--freecad-python',default='/usr/bin/python3');ap.add_argument('--freecad-lib',default='/usr/lib/freecad-python3/lib');ap.add_argument('--work',type=Path);a=ap.parse_args()
root=Path(__file__).resolve().parents[1];work=(a.work or root.parents[1]/'work/coliseum-cad/build').resolve();work.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env['XDG_CACHE_HOME']=str(work/'cache');env['MPLCONFIGDIR']=str(work/'matplotlib')
steps=[ [a.freecad_python,str(root/'scripts/build_freecad.py'),'--package',str(root),'--work',str(work),'--freecad-lib',a.freecad_lib], [sys.executable,str(root/'scripts/build_ifc_glb.py'),'--package',str(root),'--work',str(work)], [sys.executable,str(root/'scripts/build_drawings.py'),'--package',str(root)], [sys.executable,str(root/'scripts/validate.py'),'--package',str(root),'--work',str(work)] ]
for command in steps:subprocess.run(command,check=True,env=env)
subprocess.run([sys.executable,str(root/'scripts/package_reference.py')],check=True,env=env)
