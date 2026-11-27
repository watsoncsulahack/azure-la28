export function attachLookControls(canvas,{enabled,onDelta,onStart=()=>{}}){
  let pointer=null;
  const reset=()=>{pointer=null;};
  const down=e=>{
    if(!enabled()||pointer||(e.pointerType==='mouse'&&e.button!==0))return;
    e.preventDefault();pointer={id:e.pointerId,x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);onStart();
  };
  const move=e=>{
    if(!enabled()||pointer?.id!==e.pointerId)return;
    onDelta(e.clientX-pointer.x,e.clientY-pointer.y);pointer.x=e.clientX;pointer.y=e.clientY;
  };
  const end=e=>{if(pointer?.id===e.pointerId)reset();};
  canvas.addEventListener('pointerdown',down);canvas.addEventListener('pointermove',move);
  for(const name of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(name,end);
  return{reset,destroy(){reset();canvas.removeEventListener('pointerdown',down);canvas.removeEventListener('pointermove',move);for(const name of ['pointerup','pointercancel','lostpointercapture'])canvas.removeEventListener(name,end);}};
}
