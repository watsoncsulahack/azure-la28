import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {buildVenue,checkModel} from '../dist/model.js';
import * as THREE from '../dist/vendor/three.module.js';
import {moveAgent} from '../dist/navigation.js';

const spec=JSON.parse(await readFile(new URL('../dist/data/venue.json',import.meta.url)));
const model=buildVenue(spec);
const report=checkModel(model);
assert.equal(new Set(spec.components.map(c=>c.id)).size,spec.components.length,'Component IDs must be unique');
assert.equal(spec.towerLevels.length,7,'Seven independently identified tower levels');
assert.equal(new Set(spec.towerLevels.map(l=>l.id)).size,7);
let triangles=0;
model.root.traverse(object=>{
  if(!object.isMesh)return;
  const position=object.geometry.getAttribute('position');
  assert(position.count>0,`${object.name}: nonempty mesh`);
  for(const n of position.array)assert(Number.isFinite(n),`${object.name}: finite geometry`);
  const normal=object.geometry.getAttribute('normal');
  if(normal)for(const n of normal.array)assert(Number.isFinite(n),`${object.name}: finite normals`);
  triangles+=(object.geometry.index?.count??position.count)/3*(object.count??1);
});
for(const check of report.checks)assert(check.pass,`${check.id}: ${check.error} exceeds implementation tolerance`);
// Actual ray/mesh intersections check navigation surfaces and open arch geometry.
function topSurface(x,z){
  const ray=new THREE.Raycaster(new THREE.Vector3(x,100,z),new THREE.Vector3(0,-1,0));
  return ray.intersectObjects(model.walkables,false).find(hit=>hit.face.normal.y>.3)?.point.y;
}
assert(Math.abs(topSurface(0,0))<.12,'Field surface must be near zero');
assert(topSurface(0,-88)>20,'Bowl destination must land on an elevated terrace');
assert(Math.abs(topSurface(150,22)-spec.parameters.streetHeight)<.01,'Peristyle terrace must be at street reference');
const archRay=new THREE.Raycaster(new THREE.Vector3(155,spec.parameters.streetHeight+5,0),new THREE.Vector3(-1,0,0),0,30);
const centralArch=model.components.peristyle.getObjectByName('arch-08');
assert.equal(archRay.intersectObject(centralArch,false).length,0,'Central arch opening must be traversable');
const pierRay=new THREE.Raycaster(new THREE.Vector3(155,spec.parameters.streetHeight+5,5.2),new THREE.Vector3(-1,0,0),0,30);
assert(pierRay.intersectObject(centralArch,false).length>0,'Arch pier must remain solid');
assert(model.colliders.length>30,'Architectural collision geometry must exist');
const visitor=new THREE.Vector3(0,.06,0);
moveAgent(model,visitor,1,0);assert(Math.abs(visitor.x-1)<.001,'Forward movement must retain the first axis');
moveAgent(model,visitor,1,1);assert(Math.abs(visitor.x-2)<.001&&Math.abs(visitor.z-1)<.001,'Diagonal movement must preserve both axes');
const collisionTest={...model,colliders:[new THREE.Box3(new THREE.Vector3(2.3,-1,0),new THREE.Vector3(4,4,2))]};
moveAgent(collisionTest,visitor,.4,0);assert(Math.abs(visitor.x-2)<.001,'Walking must not cross a solid obstacle');
const edgeX=spec.parameters.footballLength/2-.05;
const edgeVisitor=new THREE.Vector3(edgeX,.055,0);
const edgeTest={...model,walkables:[model.components.field.getObjectByName('football-playing-surface')],colliders:[]};
moveAgent(edgeTest,edgeVisitor,.8,0);assert(edgeVisitor.x===edgeX,'Walking must not step into unsupported space');
report.geometryChecks={finiteMeshes:true,uniqueComponentIds:true,sevenTowerLevels:true,openCentralArch:true,solidArchPier:true,fieldAndBowlSurfaces:true,triangles,visualSeatInstances:model.seatCount};
report.navigationChecks={axisMovement:true,diagonalMovement:true,solidObstacle:true,unsupportedEdge:true};
report.browserVerification='Not run: the managed browser-control tool is unavailable in this chat.';
await writeFile(new URL('../dist/data/validation.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({checks:report.checks.length,passed:report.checks.filter(c=>c.pass).length,maxSourceConsistencyErrorM:Math.max(...report.checks.map(c=>c.error)),geometry:report.geometryChecks,physicalAccuracy:report.physicalAccuracy},null,2));
