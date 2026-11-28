import * as THREE from './vendor/three.module.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {buildVenue,checkModel} from './model.js?v=0.3.0';
import {moveAgent,findSurface,movementVector,EXPLORE_SPEED,FAST_SPEED} from './navigation.js?v=0.3.0';
import {attachJoystick} from './joystick.js?v=0.3.0';
import {createMapCamera,resizeMapCamera} from './cameras.js?v=0.3.0';
import {attachLookControls} from './touch-look.js?v=0.3.0';
import {buildEvidenceOverlay} from './geospatial-overlay.js?v=0.3.0';

const $=s=>document.querySelector(s);
let toastTimer;
function toast(message){$('#toast').textContent=message;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),3500);}
function download(data,name,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([data],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),30000);}

async function main(){
  const spec=await fetch('./data/venue.json?v=0.3.0').then(r=>{if(!r.ok)throw Error('Model inputs could not be loaded.');return r.json();});
  const viewport=$('#viewport'),touchDevice=matchMedia('(pointer:coarse)').matches,motionQuery=matchMedia('(prefers-reduced-motion:reduce)');
  let renderer;
  try{renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});}catch{throw Error('This viewer requires WebGL and hardware acceleration.');}
  renderer.setPixelRatio(Math.min(devicePixelRatio,touchDevice?1.4:1.8));
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  // Static architecture has static shadows; avoid rendering a second full scene every frame.
  renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;
  renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.2;
  viewport.append(renderer.domElement);
  const scene=new THREE.Scene();scene.background=new THREE.Color('#dce6ec');scene.fog=new THREE.Fog('#dce6ec',650,1250);
  const eyeCamera=new THREE.PerspectiveCamera(54,innerWidth/innerHeight,.1,1800);
  const mapCamera=createMapCamera();
  const mapControls=new OrbitControls(mapCamera,renderer.domElement);
  mapControls.enableRotate=false;mapControls.enableDamping=true;mapControls.dampingFactor=.12;mapControls.screenSpacePanning=true;
  mapControls.minZoom=.45;mapControls.maxZoom=12;mapControls.zoomSpeed=1.2;
  mapControls.touches.ONE=THREE.TOUCH.PAN;mapControls.touches.TWO=THREE.TOUCH.DOLLY_PAN;
  mapControls.mouseButtons.LEFT=THREE.MOUSE.PAN;mapControls.mouseButtons.MIDDLE=THREE.MOUSE.DOLLY;mapControls.mouseButtons.RIGHT=THREE.MOUSE.PAN;
  const model=buildVenue(spec);scene.add(model.root);
  // GIS evidence is a visual-only layer. It is intentionally excluded from walkables/colliders.
  const evidence=await fetch('./data/geospatial-evidence.json?v=0.3.0').then(r=>{if(!r.ok)throw Error('Geospatial evidence not available');return r.json();});
  const overlay=buildEvidenceOverlay(spec,evidence);
  scene.add(overlay.group);
  overlay.group.visible=true;
  scene.add(new THREE.HemisphereLight('#eaf4ff','#8a8779',2.4));
  const sun=new THREE.DirectionalLight('#fff4db',3.3);sun.position.set(-190,330,-210);sun.castShadow=true;
  sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-300;sun.shadow.camera.right=300;sun.shadow.camera.top=250;sun.shadow.camera.bottom=-250;sun.shadow.camera.near=30;sun.shadow.camera.far=800;sun.shadow.normalBias=.12;sun.shadow.bias=-.00012;scene.add(sun);
  const fill=new THREE.DirectionalLight('#d4eaff',.7);fill.position.set(130,130,180);scene.add(fill);
  const p=spec.parameters,player=new THREE.Vector3(-48,.055,0),keys=new Set();
  let mode='first',yaw=-Math.PI/2,pitch=.04,fast=false,mapTap=null,grounds=false,selectedPoint=null,labels=true;
  let analog={x:0,y:0},visualY=player.y,gesturePointers=new Set(),lookControl=null;
  const joystick=attachJoystick($('#joystick'),$('#joystick-thumb'),v=>analog={x:v.x,y:v.y});
  const places={
    field:{name:'On the field',detail:'Field level · toward the peristyle',pos:[-48,.055,0],yaw:-Math.PI/2,pitch:.04},
    lower:{name:'Lower north bowl',detail:'Follow the open aisles up or down',pos:[0,7,-56],yaw:Math.PI,pitch:-.08},
    upper:{name:'Upper north bowl',detail:'North stands · field and south tower',pos:[0,29,-97],yaw:Math.PI,pitch:-.23},
    west:{name:'West bowl',detail:'West stands · toward the east arches',pos:[-126,20,0],yaw:-Math.PI/2,pitch:-.1},
    peristyle:{name:'Peristyle terrace',detail:'East plaza · field stairs ahead',pos:[151,p.streetHeight,20],yaw:Math.PI/2,pitch:.10},
    grounds:{name:'Surrounding grounds',detail:'North approach · exterior stairs toward the stands',pos:[0,p.streetHeight,-170],yaw:Math.PI,pitch:.1}
  };
  for(const level of spec.towerLevels){
    places[level.id]={name:level.label,detail:'South tower terrace · preview floor elevation',pos:[0,p.streetHeight+level.aboveStreet,70],yaw:0,pitch:-.1};
    const b=document.createElement('button');b.dataset.place=level.id;b.textContent=level.label;$('#tower-destinations').append(b);
  }
  function clearInput(){keys.clear();analog={x:0,y:0};joystick.reset();lookControl?.reset();mapTap=null;gesturePointers.clear();}
  function fitMap(showGrounds=false){
    const damping=mapControls.enableDamping;mapControls.enableDamping=false;mapControls.update();
    grounds=showGrounds;mapControls.target.set(0,0,0);mapCamera.position.set(0,600,0);mapCamera.zoom=1;
    resizeMapCamera(mapCamera,viewport.clientWidth,viewport.clientHeight,grounds);mapControls.update();
    mapControls.enableDamping=damping;
    $('#grounds-view').textContent=grounds?'Venue':'Grounds';
    $('#location-name').textContent=grounds?'Surrounding grounds':'The Coliseum';
    $('#location-detail').textContent='Overhead orthographic map · north up';
  }
  function resize(){
    const w=viewport.clientWidth,h=viewport.clientHeight;eyeCamera.aspect=w/h;eyeCamera.updateProjectionMatrix();
    resizeMapCamera(mapCamera,w,h,grounds);renderer.setSize(w,h);
  }
  function updateEye(dt=1){
    const reduced=motionQuery.matches;
    visualY=THREE.MathUtils.lerp(visualY,player.y,reduced?1:1-Math.exp(-dt*17));
    eyeCamera.position.set(player.x,visualY+1.65,player.z);
    eyeCamera.lookAt(player.x-Math.sin(yaw)*Math.cos(pitch),visualY+1.65+Math.sin(pitch),player.z-Math.cos(yaw)*Math.cos(pitch));
  }
  function setMode(next){
    clearInput();mode=next;mapControls.enabled=mode==='map';$('#app').dataset.mode=mode;
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
    for(const id of ['walk-controls','look-hint','crosshair','speed-button','desktop-hint'])$('#'+id).hidden=mode==='map';
    for(const id of ['map-hint','map-zoom','grounds-view'])$('#'+id).hidden=mode!=='map';
    $('#map-hotspots').hidden=mode!=='map';$('#position-pin').hidden=mode!=='map';
    if(mode==='map')fitMap(false);else{
      selectedPoint=null;$('#map-entry').hidden=true;$('#selected-pin').hidden=true;visualY=player.y;updateEye();
      $('#location-name').textContent='Explore the Coliseum';$('#location-detail').textContent='Joystick to move · swipe to look';
    }
  }
  function teleport(key){
    const d=places[key];if(!d)return;
    const y=findSurface(model,d.pos[0],d.pos[2],d.pos[1]);
    if(y===null){toast('This location has no modeled walking surface.');return;}
    player.set(d.pos[0],y,d.pos[2]);yaw=d.yaw;pitch=d.pitch;visualY=y;
    setMode('first');$('#location-name').textContent=d.name;$('#location-detail').textContent=d.detail;
    $('#places-dialog').close();viewport.focus({preventScroll:true});
  }
  const hotspotDefinitions=[['field','Field',[0,0,0]],['upper','North stands',[0,30,-95]],['peristyle','Peristyle',[145,p.streetHeight,0]],['grounds','Grounds',[0,p.streetHeight,-175]]];
  const hotspots=hotspotDefinitions.map(([key,label,pos])=>{
    const node=document.createElement('button');node.className='map-place';node.textContent=label;node.setAttribute('aria-label','Explore '+label);node.addEventListener('click',()=>teleport(key));$('#map-hotspots').append(node);return{node,position:new THREE.Vector3(...pos)};
  });
  document.querySelectorAll('[data-place]').forEach(b=>b.addEventListener('click',()=>teleport(b.dataset.place)));
  document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{setMode(b.dataset.mode);viewport.focus({preventScroll:true});}));
  $('#speed-button').addEventListener('click',()=>{
    fast=!fast;$('#speed-label').textContent=fast?'Fast':'Explore';$('#speed-button').setAttribute('aria-pressed',String(fast));
    $('#speed-button').setAttribute('aria-label',`Movement speed ${fast?'fast':'explore'}. Switch to ${fast?'explore':'fast'}.`);
  });
  $('#zoom-in').addEventListener('click',()=>{mapCamera.zoom=Math.min(12,mapCamera.zoom*1.4);mapCamera.updateProjectionMatrix();});
  $('#zoom-out').addEventListener('click',()=>{mapCamera.zoom=Math.max(.45,mapCamera.zoom/1.4);mapCamera.updateProjectionMatrix();});
  $('#grounds-view').addEventListener('click',()=>fitMap(!grounds));
  $('#reset-view').addEventListener('click',()=>mode==='map'?fitMap(grounds):teleport('field'));
  $('#places-open').addEventListener('click',()=>{clearInput();$('#places-dialog').showModal();});
  $('#help-open').addEventListener('click',()=>{clearInput();$('#help-dialog').showModal();});
  document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>$('#'+b.dataset.close).close()));
  for(const dialog of document.querySelectorAll('dialog')){
    dialog.addEventListener('click',e=>{if(e.target!==dialog)return;const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();});
    dialog.addEventListener('close',()=>viewport.focus({preventScroll:true}));
  }
  $('#seats-toggle').addEventListener('change',e=>{model.components.seats.visible=e.target.checked;renderer.shadowMap.needsUpdate=true;});
  const setGisVisible=visible=>{overlay.group.visible=visible;$('#gis-toggle').checked=visible;
    $('#gis-button').setAttribute('aria-pressed',String(visible));
    $('#gis-button').textContent=visible?'GIS ON':'GIS OFF';
    toast(visible?'Provisional GIS evidence visible — not verified pedestrian geometry.':'GIS context hidden.');};
  $('#gis-toggle').addEventListener('change',e=>setGisVisible(e.target.checked));
  $('#gis-button').addEventListener('click',()=>setGisVisible(!overlay.group.visible));
  $('#labels-toggle').addEventListener('change',e=>labels=e.target.checked);
  const canvas=renderer.domElement;
  lookControl=attachLookControls(canvas,{enabled:()=>mode==='first',onStart:()=>viewport.focus({preventScroll:true}),onDelta:(dx,dy)=>{yaw-=dx*.0045;pitch=THREE.MathUtils.clamp(pitch-dy*.0035,-1.2,1.2);}});
  canvas.addEventListener('contextmenu',e=>e.preventDefault());
  canvas.addEventListener('pointerdown',e=>{
    if(e.pointerType==='mouse'&&e.button!==0)return;
    if(mode!=='map')return;
    gesturePointers.add(e.pointerId);
    mapTap=gesturePointers.size===1?{id:e.pointerId,x:e.clientX,y:e.clientY}:null;
  });
  canvas.addEventListener('pointermove',e=>{
    if(mapTap?.id===e.pointerId&&Math.hypot(e.clientX-mapTap.x,e.clientY-mapTap.y)>8)mapTap=null;
  });
  function selectMapPoint(e){
    const r=canvas.getBoundingClientRect(),ndc=new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);
    const ray=new THREE.Raycaster();mapCamera.updateMatrixWorld();ray.setFromCamera(ndc,mapCamera);
    const hit=ray.intersectObjects(model.walkables.filter(m=>m.visible&&m.parent.visible),false).find(h=>h.face.normal.y>.3);
    if(!hit){toast('Tap the stadium or a modeled walking area.');return;}
    // Use the same navigation surface sampler as walking so the selected level is consistent.
    const y=findSurface(model,hit.point.x,hit.point.z,hit.point.y);if(y===null)return;
    const center=new THREE.Vector3(hit.point.x,y+.85,hit.point.z);
    if(model.colliders.some(b=>b.distanceToPoint(center)<.25)){toast('Choose an open walking area.');return;}
    selectedPoint=new THREE.Vector3(hit.point.x,y,hit.point.z);$('#map-entry').hidden=false;
  }
  canvas.addEventListener('pointerup',e=>{
    if(mode==='map'&&mapTap?.id===e.pointerId&&gesturePointers.size===1)selectMapPoint(e);
    gesturePointers.delete(e.pointerId);mapTap=null;
  });
  function cancelPointer(e){gesturePointers.delete(e.pointerId);mapTap=null;}
  canvas.addEventListener('pointercancel',cancelPointer);canvas.addEventListener('lostpointercapture',cancelPointer);
  $('#explore-point').addEventListener('click',()=>{if(!selectedPoint)return;player.copy(selectedPoint);visualY=player.y;setMode('first');viewport.focus({preventScroll:true});});
  $('#cancel-point').addEventListener('click',()=>{selectedPoint=null;$('#map-entry').hidden=true;$('#selected-pin').hidden=true;});
  const keyCodes=['KeyW','KeyA','KeyS','KeyD','ShiftLeft','ShiftRight','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'];
  window.addEventListener('keydown',e=>{
    if(mode!=='first'||document.querySelector('dialog[open]')||['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))return;
    if(keyCodes.includes(e.code)){keys.add(e.code);e.preventDefault();}
  });
  window.addEventListener('keyup',e=>keys.delete(e.code));window.addEventListener('blur',clearInput);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)clearInput();});
  $('#export-model').addEventListener('click',async()=>{
    const button=$('#export-model');button.disabled=true;toast('Preparing the model download…');
    try{
      const r=await fetch('./coliseum-0.2.0.glb');if(!r.ok)throw Error('Base GLB unavailable');
      download(await r.arrayBuffer(),'coliseum-0.2.0-base-geometry.glb','model/gltf-binary');
      toast('Downloaded original base GLB. GIS evidence is separately downloadable as JSON.');
    }catch(error){console.error(error);toast('The download could not start. Please try again.');}
    finally{button.disabled=false;}
  });
  function placeScreenNode(node,point){
    const v=point.clone().project(mapCamera),w=viewport.clientWidth,h=viewport.clientHeight;
    node.hidden=v.z< -1||v.z>1||Math.abs(v.x)>1||Math.abs(v.y)>1;
    node.style.left=`${(v.x*.5+.5)*w}px`;node.style.top=`${(-v.y*.5+.5)*h}px`;
  }
  window.addEventListener('resize',resize);resize();teleport('field');
  const report=checkModel(model);window.coliseumModel={revision:spec.revision,report,evidenceManifest:evidence.manifest,
    overlaySummary:{streetSegments:overlay.streets,curbRamps:overlay.curbRamps,navMeshesAdded:0},
    get cameraType(){return mode==='map'?'OrthographicCamera':'PerspectiveCamera';}};
  $('#loading').remove();
  const clock=new THREE.Clock();
  let locationElapsed=0;
  renderer.setAnimationLoop(()=>{
    const dt=Math.min(clock.getDelta(),.1),dialogOpen=!!document.querySelector('dialog[open]');
    if(mode==='map')mapControls.update();
    else if(!dialogOpen){
      let forward=-analog.y+Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown'));
      let side=analog.x+Number(keys.has('KeyD'))-Number(keys.has('KeyA'));
      if(keys.has('ArrowLeft'))yaw+=dt*1.6;if(keys.has('ArrowRight'))yaw-=dt*1.6;
      const speed=fast||keys.has('ShiftLeft')||keys.has('ShiftRight')?FAST_SPEED:EXPLORE_SPEED;
      if(forward||side){
        const{dx,dz}=movementVector(side,forward,yaw,speed,dt);moveAgent(model,player,dx,dz);
        locationElapsed+=dt;
        if(locationElapsed>.4){
          locationElapsed=0;
          const insideBowl=(player.x/(p.bowlLength/2))**2+(player.z/(p.bowlWidth/2))**2<=1;
          let name='Surrounding grounds',detail='Explore the paths, approaches and exterior stairs';
          if(player.x>118&&player.x<170&&Math.abs(player.z)<56){name='Peristyle terrace';detail='East plaza · field stairs through the central arch';}
          else if(Math.abs(player.x)<p.towerLength/2&&player.z>69&&player.z<100&&player.y>p.streetHeight-.2){name='South tower terrace';detail='Use Places to visit another tower level';}
          else if(insideBowl){
            if(player.y<1){name='Field level';detail='Explore the field and seating aisles';}
            else{const side=Math.abs(player.x)/(p.bowlLength/2)>Math.abs(player.z)/(p.bowlWidth/2)?(player.x>0?'east':'west'):(player.z>0?'south':'north');name=`${player.y<p.rimHeight*.5?'Lower':'Upper'} ${side} bowl`;detail='Open aisles connect the field and upper rim';}
          }
          $('#location-name').textContent=name;$('#location-detail').textContent=detail;
        }
      }
      updateEye(dt);
    }
    const camera=mode==='map'?mapCamera:eyeCamera;
    if(mode==='map'){
      mapCamera.updateMatrixWorld();for(const h of hotspots){placeScreenNode(h.node,h.position);h.node.hidden||=!labels;}
      placeScreenNode($('#position-pin'),player);
      if(selectedPoint)placeScreenNode($('#selected-pin'),selectedPoint);else $('#selected-pin').hidden=true;
    }
    $('#compass-needle').style.transform=mode==='map'?'rotate(0rad)':`rotate(${-yaw}rad)`;
    renderer.render(scene,camera);
  });
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();clearInput();toast('Graphics were interrupted. Reload to restart the viewer.');});
}
main().catch(error=>{console.error(error);$('#loading').innerHTML='';const title=document.createElement('strong'),detail=document.createElement('span');title.textContent='The model could not start';detail.textContent=error.message;$('#loading').append(title,detail);});
