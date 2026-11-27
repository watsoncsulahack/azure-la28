import * as THREE from './vendor/three.module.js';

export function createMapCamera(){
  const camera=new THREE.OrthographicCamera(-200,200,200,-200,.1,1500);
  camera.up.set(0,0,-1);camera.position.set(0,600,0);camera.lookAt(0,0,0);
  return camera;
}

export function resizeMapCamera(camera,width,height,grounds=false){
  const aspect=width/height,spanX=grounds?555:390,spanZ=grounds?455:300;
  const halfHeight=Math.max(spanZ/2,spanX/(2*aspect));
  camera.left=-halfHeight*aspect;camera.right=halfHeight*aspect;camera.top=halfHeight;camera.bottom=-halfHeight;camera.updateProjectionMatrix();
}
