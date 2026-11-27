import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import * as THREE from '../dist/vendor/three.module.js';
import {buildVenue} from '../dist/model.js';
import {moveAgent,findSurface,movementVector,EXPLORE_SPEED,FAST_SPEED} from '../dist/navigation.js';
import {joystickVector,attachJoystick} from '../dist/joystick.js';
import {attachLookControls} from '../dist/touch-look.js';
import {createMapCamera,resizeMapCamera} from '../dist/cameras.js';

const spec=JSON.parse(await readFile(new URL('../dist/data/venue.json',import.meta.url)));
const model=buildVenue(spec),results={};
assert.equal(joystickVector(0,0).x,0);assert.equal(joystickVector(2,2).y,0);
const full=joystickVector(300,-300);assert(Math.abs(Math.hypot(full.x,full.y)-1)<1e-9);
assert(Math.abs(Math.hypot(full.thumbX,full.thumbY)-48)<1e-9);
assert(joystickVector(0,-24).y<0&&Math.abs(joystickVector(0,-24).y)<1);
results.analogDeadZoneClampAndDiagonal=true;

class Element extends EventTarget{
  style={};classList={add(){},remove(){}};captures=new Set();
  setPointerCapture(id){this.captures.add(id);}
  getBoundingClientRect(){return{left:0,top:0,width:132,height:132};}
}
function pointer(target,type,id,x,y){
  const event=new Event(type,{cancelable:true});Object.assign(event,{pointerId:id,clientX:x,clientY:y,pointerType:'touch',button:0});target.dispatchEvent(event);
}
const base=new Element(),thumb=new Element(),canvas=new Element();
let analog={x:0,y:0},lookX=0,lookY=0,enabled=true;
const joystick=attachJoystick(base,thumb,v=>analog=v);
const look=attachLookControls(canvas,{enabled:()=>enabled,onDelta:(x,y)=>{lookX+=x;lookY+=y;}});
pointer(base,'pointerdown',1,66,18);assert(analog.y<-.99);
pointer(canvas,'pointerdown',2,220,220);pointer(canvas,'pointermove',2,255,205);
assert.equal(lookX,35);assert.equal(lookY,-15);assert(analog.y<-.99,'Looking must not reset the movement thumb');
pointer(canvas,'pointerup',2,255,205);assert(analog.y<-.99);
pointer(base,'pointerup',99,66,18);assert(analog.y<-.99,'An unrelated finger must not release the joystick');
pointer(base,'pointerup',1,66,18);assert.equal(analog.x,0);assert.equal(analog.y,0);
for(const event of ['pointercancel','lostpointercapture']){pointer(base,'pointerdown',3,110,66);assert(analog.x>0);pointer(base,event,3,110,66);assert.equal(analog.x,0);}
pointer(base,'pointerdown',4,66,18);joystick.reset();assert.equal(analog.y,0);
enabled=false;pointer(canvas,'pointerdown',5,0,0);pointer(canvas,'pointermove',5,100,100);assert.equal(lookX,35,'Map mode must not use first-person swipe look');
joystick.destroy();look.destroy();
results.twoFingerMoveAndLook=true;results.releaseCancelAndReset=true;results.modeInputIsolation=true;

const first=movementVector(0,1,-Math.PI/2,EXPLORE_SPEED,1);
const diagonal=movementVector(1,1,0,EXPLORE_SPEED,1);
assert(Math.abs(Math.hypot(first.dx,first.dz)-8)<1e-9);
assert(Math.abs(Math.hypot(diagonal.dx,diagonal.dz)-8)<1e-9);
assert(FAST_SPEED===16&&EXPLORE_SPEED>2.2*3);
results.fasterMovementAndNormalizedDiagonals=true;

function traverse(start,end,speed){
  const position=new THREE.Vector3(...start);position.y=findSurface(model,position.x,position.z,position.y);
  const distance=Math.hypot(end[0]-position.x,end[2]-position.z),ux=(end[0]-position.x)/distance,uz=(end[2]-position.z)/distance;
  const count=Math.ceil(distance/(speed/30)),step=distance/count;
  for(let i=0;i<count;i++)moveAgent(model,position,ux*step,uz*step);
  assert(Math.hypot(position.x-end[0],position.z-end[2])<.15,`Traversal stalled at ${position.toArray()} toward ${end}`);
  assert(Math.abs(position.y-end[1])<.65,`Wrong destination height ${position.y} expected ${end[1]}`);
  return position;
}
for(const speed of [EXPLORE_SPEED,FAST_SPEED]){
  traverse([80,0,0],[205,spec.parameters.streetHeight,0],speed);
  traverse([205,spec.parameters.streetHeight,0],[80,0,0],speed);
  traverse([0,0,-35],[0,spec.parameters.rimHeight,-112],speed);
  traverse([0,spec.parameters.rimHeight,-112],[0,spec.parameters.streetHeight,-175],speed);
  traverse([0,spec.parameters.streetHeight,-175],[0,spec.parameters.rimHeight,-112],speed);
  traverse([0,spec.parameters.rimHeight,-112],[0,0,-35],speed);
}
results.fieldPlazaGroundsRoundTrip=true;results.bowlRimExteriorStairsRoundTrip=true;

const wallModel={...model,colliders:[new THREE.Box3(new THREE.Vector3(2,-2,-1),new THREE.Vector3(2.5,3,1))]};
const agent=new THREE.Vector3(0,.055,0);moveAgent(wallModel,agent,FAST_SPEED*.2,0);
assert(agent.x<2,'Fast movement must not tunnel through a narrow wall');results.fastCollisionSweeps=true;

const points=[[0,0],[88,0],[0,-55],[0,-90],[0,-130],[105,0],[180,0],[0,-175]];
for(const[x,z]of points){
  const y=findSurface(model,x,z);
  const ray=new THREE.Raycaster(new THREE.Vector3(x,150,z),new THREE.Vector3(0,-1,0));
  const actual=ray.intersectObjects(model.walkables,false).find(h=>h.face.normal.y>.3)?.point.y;
  assert(y!==null&&actual!==undefined&&Math.abs(y-actual)<.03,`Navigation/mesh mismatch at ${x},${z}: ${y} vs ${actual}`);
}
results.navigationMatchesRenderedSurfaces=true;

const camera=createMapCamera();assert(camera.isOrthographicCamera);
for(const[w,h]of [[390,844],[844,390],[1440,900]]){
  resizeMapCamera(camera,w,h);camera.updateMatrixWorld();
  const low=new THREE.Vector3(50,0,0).project(camera),high=new THREE.Vector3(50,50,0).project(camera);
  assert(Math.abs(low.x-high.x)<1e-9,'Map must preserve orthographic scale across heights');
  const north=new THREE.Vector3(0,0,-100).project(camera);assert(north.y>0,'North must appear at the top');
  assert(low.z>=-1&&low.z<=1,'Map labels must use the full -1 to +1 clip range');
  assert(Math.abs(new THREE.Vector3(160,0,0).project(camera).x)<1,'Venue must fit portrait and landscape');
}
results.orthographicNorthUpPortraitAndLandscape=true;
const reportPath=new URL('../dist/data/validation.json',import.meta.url);
const report=JSON.parse(await readFile(reportPath));report.mobileNavigationChecks=results;
report.browserVerification='Touch input event handlers, navigation geometry and camera math tested in Node. Browser rendering and real phone gestures unverified: the managed browser tool is unavailable.';
await writeFile(reportPath,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({mobileNavigationChecks:results},null,2));
