export function joystickVector(dx,dy,radius=48,deadZone=.08){
  const distance=Math.hypot(dx,dy),fraction=Math.min(1,distance/radius);
  if(fraction<=deadZone)return{x:0,y:0,thumbX:dx,thumbY:dy};
  const strength=(fraction-deadZone)/(1-deadZone),unitX=dx/distance,unitY=dy/distance;
  return{x:unitX*strength,y:unitY*strength,thumbX:unitX*Math.min(distance,radius),thumbY:unitY*Math.min(distance,radius)};
}

export function attachJoystick(base,thumb,onChange){
  let pointer=null;
  const reset=()=>{pointer=null;thumb.style.transform='translate(0px, 0px)';base.classList.remove('active');onChange({x:0,y:0});};
  const update=e=>{const r=base.getBoundingClientRect(),v=joystickVector(e.clientX-r.left-r.width/2,e.clientY-r.top-r.height/2);thumb.style.transform=`translate(${v.thumbX}px, ${v.thumbY}px)`;onChange(v);};
  const down=e=>{if(pointer!==null)return;e.preventDefault();e.stopPropagation();pointer=e.pointerId;base.setPointerCapture(pointer);base.classList.add('active');update(e);};
  const move=e=>{if(e.pointerId!==pointer)return;e.preventDefault();update(e);};
  const end=e=>{if(e.pointerId===pointer)reset();};
  base.addEventListener('pointerdown',down);base.addEventListener('pointermove',move);
  for(const name of ['pointerup','pointercancel','lostpointercapture'])base.addEventListener(name,end);
  return{reset,destroy(){reset();base.removeEventListener('pointerdown',down);base.removeEventListener('pointermove',move);for(const name of ['pointerup','pointercancel','lostpointercapture'])base.removeEventListener(name,end);}};
}
