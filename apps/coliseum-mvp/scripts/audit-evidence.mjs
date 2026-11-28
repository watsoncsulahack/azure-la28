// Inventory actual generated meshes, including estimates embedded in generator code.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {buildVenue,checkModel} from '../dist/model.js';
import * as THREE from '../dist/vendor/three.module.js';
const spec=JSON.parse(await readFile(new URL('../dist/data/venue.json',import.meta.url)));
const model=buildVenue(spec), report=checkModel(model);
const out=new URL('../../../analysis/coliseum-model/evidence-iteration/',import.meta.url);
await mkdir(out,{recursive:true});
const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';
const csv=(keys,rows)=>[keys,...rows.map(r=>keys.map(k=>r[k]))].map(row=>row.map(quote).join(',')).join('\n')+'\n';
const rows=[];
model.root.updateMatrixWorld(true);
for(const component of spec.components){
  const group=model.components[component.id];
  group.traverse(mesh=>{
    if(!mesh.isMesh)return;
    const b=new THREE.Box3().setFromObject(mesh);
    const path=[];for(let n=mesh;n&&n!==group;n=n.parent)path.unshift(`${n.parent.children.indexOf(n)}:${n.name||'unnamed'}`);
    rows.push({component:component.id,mesh:mesh.name,snapshotMeshPath:component.id+'/'+path.join('/'),sourceMeasurementIds:component.measurementIds.join(';'),
      assumptionIds:component.assumptionIds.join(';'),evidence:component.evidenceClass,
      geometryStatus:'ESTIMATED_OR_UNVERIFIED',physicalValidation:'NOT_VALIDATED',
      sourceScope:'Component references anchor selected dimensions only; they do not validate this whole mesh.',
      minX:b.min.x,minY:b.min.y,minZ:b.min.z,maxX:b.max.x,maxY:b.max.y,maxZ:b.max.z,
      instances:mesh.isInstancedMesh?mesh.count:1,
      generator:'apps/coliseum-mvp/dist/model.js',inputs:'apps/coliseum-mvp/dist/data/venue.json'});
  });
}
assert.equal(new Set(rows.map(r=>r.snapshotMeshPath)).size,rows.length);
await writeFile(new URL('component-traceability.csv',out),csv(Object.keys(rows[0]),rows));
const field=model.components.field.getObjectByName('field-envelope');
const pos=field.geometry.getAttribute('position'),index=field.geometry.index;
let topArea=0;
for(let i=0;i<(index?.count??pos.count);i+=3){
  const ids=[0,1,2].map(j=>index?index.getX(i+j):i+j);
  const v=ids.map(j=>new THREE.Vector3().fromBufferAttribute(pos,j));
  if(v.every(p=>Math.abs(p.y)<1e-6))topArea+=Math.abs((v[1].x-v[0].x)*(v[2].z-v[0].z)-(v[1].z-v[0].z)*(v[2].x-v[0].x))/2;
}
assert(report.notValidatedChecks.some(c=>c.measurementId==='M158'));
assert.equal(report.independentPhysicalChecks,0);
const diagnostics={meshCount:rows.length,fieldMeshTopPlanAreaM2:topArea,
  analyticEllipseAreaM2:Math.PI*spec.parameters.fieldLength*spec.parameters.fieldWidth/4,
  guidePlayingAreaM2:135837*.3048**2,
  boundaryEquivalenceEstablished:false,
  bowlSpanXM:report.componentBounds.bowl.max[0]-report.componentBounds.bowl.min[0],
  modelChecks:report,
  independentPhysicalAcceptanceChecks:0,
  estimatedScope:'Every complete component remains physically unverified; selected spans have verified source transcription only.'};
await writeFile(new URL('model-diagnostics.json',out),JSON.stringify(diagnostics,null,2)+'\n');
const source=await readFile(new URL('../dist/model.js',import.meta.url),'utf8');
const constants=source.split('\n').map((line,i)=>({line:i+1,code:line.trim()}))
  .filter(r=>/\d/.test(r.code)&&!/^\/\//.test(r.code))
  .map(r=>({...r,classification:'REVIEW_ESTIMATE_OR_ALGORITHM',physicalValidation:'NOT_VALIDATED',
    note:'Includes algorithms, rendering and physical literals. No hardcoded length/placement gains measured status by inclusion in a sourced component.'}));
await writeFile(new URL('generator-constants.csv',out),csv(Object.keys(constants[0]),constants));
console.log(JSON.stringify({meshes:rows.length,fieldTopAreaM2:topArea,notValidated:report.notValidatedChecks.length}));
