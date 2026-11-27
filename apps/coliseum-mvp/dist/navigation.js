import * as THREE from './vendor/three.module.js';

export const EXPLORE_SPEED=8;
export const FAST_SPEED=16;

// Surface descriptions share their dimensions with the rendered geometry.
function heightOn(surface,x,z){
  if(!surface.mesh.visible||!surface.mesh.parent.visible)return null;
  if(surface.type==='rectangle')return x>=surface.minX&&x<=surface.maxX&&z>=surface.minZ&&z<=surface.maxZ?surface.height:null;
  if(surface.type==='ring'){
    const [ox,oz]=surface.outer,[ix,iz]=surface.inner;
    if(x*x/(ox*ox)+z*z/(oz*oz)>1+1e-8)return null;
    if(ix>0&&iz>0&&x*x/(ix*ix)+z*z/(iz*iz)<1-1e-8)return null;
    let a=Math.atan2(z/oz,x/ox);if(a<0)a+=Math.PI*2;
    const step=(surface.end-surface.start)/surface.segments;
    const segmentA=surface.start+(Math.floor((a-surface.start)/step)+.5)*step;
    return surface.skip?.(segmentA)?null:surface.height;
  }
  if(surface.type==='stairs'){
    const dx=x-surface.start[0],dz=z-surface.start[2],along=dx*surface.ux+dz*surface.uz,side=-dx*surface.uz+dz*surface.ux;
    if(along<-.001||along>surface.length+.001||Math.abs(side)>surface.width/2)return null;
    const t=THREE.MathUtils.clamp(along/surface.length,0,1);
    return THREE.MathUtils.lerp(surface.start[1],surface.end[1],Math.ceil(t*surface.count-1e-8)/surface.count);
  }
  return null;
}

export function findSurface(model,x,z,preferredY=null,{up=.62,down=.72,reachable=false}={}){
  if(model.navigationSurfaces?.length&&model.walkables===model.navigationWalkables){
    let best=null,bestScore=Infinity;
    for(const surface of model.navigationSurfaces){
      if(reachable&&surface.height!==undefined&&(surface.height>preferredY+up||surface.height<preferredY-down))continue;
      const y=heightOn(surface,x,z);if(y===null)continue;
      if(reachable&&(y>preferredY+up||y<preferredY-down))continue;
      const score=reachable||preferredY===null?-y:Math.abs(y-preferredY);
      if(score<bestScore){bestScore=score;best=y;}
    }
    return best;
  }
  const originY=reachable?preferredY+up:150;
  const ray=new THREE.Raycaster(new THREE.Vector3(x,originY,z),new THREE.Vector3(0,-1,0),0,reachable?up+down:300);
  const hits=ray.intersectObjects(model.walkables.filter(m=>m.visible&&m.parent.visible),false).filter(h=>h.face.normal.y>.3);
  if(preferredY!==null)hits.sort((a,b)=>Math.abs(a.point.y-preferredY)-Math.abs(b.point.y-preferredY));
  return hits[0]?.point.y??null;
}

export function surfaceHeight(model,x,z,currentY){return findSurface(model,x,z,currentY,{reachable:true});}

export function moveAgent(model,position,dx,dz){
  const steps=Math.max(1,Math.ceil(Math.hypot(dx,dz)/.18));
  for(let step=0;step<steps;step++)for(const[axis,delta]of [['x',dx/steps],['z',dz/steps]]){
    if(Math.abs(delta)<1e-10)continue;
    const next=position.clone();next[axis]+=delta;
    if(Math.hypot(next.x/420,next.z/335)>1)continue;
    const height=surfaceHeight(model,next.x,next.z,next.y);if(height===null)continue;
    next.y=height;const center=next.clone();center.y+=.85;
    if(model.colliders.some(b=>b.containsPoint(center)||b.distanceToPoint(center)<.23))continue;
    position.copy(next);
  }
  return position;
}

export function movementVector(side,forward,yaw,speed,dt){
  const scale=Math.max(1,Math.hypot(side,forward));side/=scale;forward/=scale;
  return {dx:(-Math.sin(yaw)*forward+Math.cos(yaw)*side)*speed*dt,dz:(-Math.cos(yaw)*forward-Math.sin(yaw)*side)*speed*dt};
}
