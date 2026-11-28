import * as THREE from './vendor/three.module.js';

export const GENERATOR_VERSION = '0.2.0';
const TAU = Math.PI * 2;
const lerp = THREE.MathUtils.lerp;
const radial = (rx, rz, a, y) => [rx * Math.cos(a), y, rz * Math.sin(a)];

export function buildVenue(spec) {
  const p = spec.parameters;
  const root = new THREE.Group();
  root.name = spec.id;
  root.userData = {venueId: spec.id, revision: spec.revision, units: 'meters', generatorVersion: GENERATOR_VERSION};
  const components = {};
  const walkables = [];
  const navigationSurfaces = [];
  const colliders = [];
  const anchors = {};
  const materials = {};
  function material(name, color, more = {}) {
    return materials[name] ||= new THREE.MeshStandardMaterial({color, roughness:.84, ...more});
  }
  const concrete = material('concrete', '#c3c1b6');
  const stone = material('stone', '#d6ccad');
  const darkStone = material('stone-shadow', '#a49f8d');
  const slab = material('slab', '#e0d9c5');
  const asphalt = material('paving', '#969d9e');
  const grass = material('grass', '#768978');
  const turf = material('turf', '#426a4c');
  const stripe = material('turf-stripe', '#3b6247');
  const paint = material('paint', '#e7e4d5');
  const cardinal = material('cardinal', '#852f39');
  const seatMat = material('seats', '#a2464c');
  const gold = material('gold', '#d4ae57', {metalness:.25,roughness:.5});
  const glass = material('glass', '#4c6977', {metalness:.35,roughness:.3});
  const dark = material('dark', '#253e49');
  function component(id) {
    const group = new THREE.Group(); group.name = id;
    group.userData = {componentId:id,...spec.components.find(c=>c.id===id)};
    components[id] = group; root.add(group); return group;
  }
  const context = component('context');
  const field = component('field');
  const bowl = component('bowl');
  const seats = component('seats');
  const circulation = component('circulation');
  const tower = component('tower');
  const peristyle = component('peristyle');
  const displays = component('displays');
  function box(parent,name,size,pos,mat,walk=false,solid=false) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size),mat);
    mesh.name=name; mesh.position.set(...pos); mesh.castShadow=true;mesh.receiveShadow=true;
    parent.add(mesh); if(walk){walkables.push(mesh);navigationSurfaces.push({type:'rectangle',mesh,height:pos[1]+size[1]/2,minX:pos[0]-size[0]/2,maxX:pos[0]+size[0]/2,minZ:pos[2]-size[2]/2,maxZ:pos[2]+size[2]/2});}
    if(solid)colliders.push(new THREE.Box3().setFromObject(mesh));
    return mesh;
  }
  function cylinder(parent,name,rt,rb,h,pos,mat,n=12) {
    const mesh=new THREE.Mesh(new THREE.CylinderGeometry(rt,rb,h,n),mat);
    mesh.name=name;mesh.position.set(...pos);mesh.castShadow=true;mesh.receiveShadow=true;parent.add(mesh);return mesh;
  }
  function ring(parent,name,ri,ro,y,h,mat,{start=0,end=TAU,segments=192,skip=null,walk=false}={}) {
    const vertices=[];
    const tri=(a,b,c)=>{
      const u=[b[0]-a[0],b[1]-a[1],b[2]-a[2]],v=[c[0]-a[0],c[1]-a[1],c[2]-a[2]];
      const cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
      if(cross[0]**2+cross[1]**2+cross[2]**2>1e-14)vertices.push(...a,...b,...c);
    };
    for(let j=0;j<segments;j++) {
      const a=lerp(start,end,j/segments),b=lerp(start,end,(j+1)/segments);
      if(skip?.((a+b)/2))continue;
      const ia=radial(...ri,a,y),ib=radial(...ri,b,y),oa=radial(...ro,a,y),ob=radial(...ro,b,y);
      tri(ia,ib,ob);tri(ia,ob,oa);
      if(h>0){
        const iab=radial(...ri,a,y-h),ibb=radial(...ri,b,y-h),oab=radial(...ro,a,y-h),obb=radial(...ro,b,y-h);
        tri(ia,iab,ibb);tri(ia,ibb,ib);tri(oa,ob,obb);tri(oa,obb,oab);
        tri(iab,oab,obb);tri(iab,obb,ibb);
        if(j===0||skip){tri(ia,oa,oab);tri(ia,oab,iab);tri(ib,ibb,obb);tri(ib,obb,ob);}
      }
    }
    const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geo.computeVertexNormals();
    const mesh=new THREE.Mesh(geo,mat);mesh.name=name;mesh.receiveShadow=true;mesh.castShadow=h>0;parent.add(mesh);
    if(walk){walkables.push(mesh);navigationSurfaces.push({type:'ring',mesh,inner:ri,outer:ro,height:y,skip,start,end,segments});}return mesh;
  }
  // Schematic preview stairs, not surveyed physical routes.
  function stairs(name,start,end,width){
    const dx=end[0]-start[0],dz=end[2]-start[2],length=Math.hypot(dx,dz),ux=dx/length,uz=dz/length;
    const count=Math.ceil(Math.abs(end[1]-start[1])/.21),verts=[];
    const point=(t,side,y)=>[lerp(start[0],end[0],t)-uz*side,y,lerp(start[2],end[2],t)+ux*side];
    const quad=(a,b,c,d)=>verts.push(...a,...b,...c,...a,...c,...d);
    for(let i=0;i<count;i++){
      const t0=i/count,t1=(i+1)/count,y=lerp(start[1],end[1],t1),prev=lerp(start[1],end[1],t0);
      quad(point(t0,width/2,y),point(t1,width/2,y),point(t1,-width/2,y),point(t0,-width/2,y));
      quad(point(t0,-width/2,prev),point(t0,width/2,prev),point(t0,width/2,y),point(t0,-width/2,y));
    }
    const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));geo.computeVertexNormals();
    const mesh=new THREE.Mesh(geo,slab);mesh.name=name;mesh.receiveShadow=true;mesh.castShadow=true;mesh.userData={assumptionId:'A009',purpose:'schematic exploration connector'};circulation.add(mesh);walkables.push(mesh);
    navigationSurfaces.push({type:'stairs',mesh,start,end,width,length,ux,uz,count,minHeight:Math.min(start[1],end[1]),maxHeight:Math.max(start[1],end[1])});
  }
  const outer=[p.bowlLength/2,p.bowlWidth/2];
  const inner=[p.innerBowlLength/2,p.innerBowlWidth/2];
  const step=p.rimHeight/p.visualRows;
  const gap=a=>Math.cos(a)>Math.cos(p.peristyleOpeningHalfAngle);
  const exteriorStairAngles=[Math.PI/2,Math.PI,3*Math.PI/2];
  const stairGap=a=>exteriorStairAngles.some(b=>Math.abs(Math.atan2(Math.sin(a-b),Math.cos(a-b)))<.045);
  const towerGap=(a,t)=>t>.36 && a>1.00 && a<2.14;
  // Earth is cut away inside the bowl: field-level geometry stays visible below street level.
  ring(context,'park-ground',[outer[0]+3,outer[1]+3],[420,335],p.streetHeight,.8,grass,{walk:true});
  ring(circulation,'outer-promenade',[outer[0],outer[1]],[outer[0]+13,outer[1]+13],p.streetHeight+.025,.15,asphalt,{walk:true});
  ring(context,'bowl-exterior-shell',[outer[0]-2.3,outer[1]-2.3],outer,p.rimHeight-1.1,p.rimHeight-p.streetHeight-1.1,stone,{skip:a=>gap(a)||stairGap(a)});
  ring(bowl,'rim-coping',[outer[0]-4,outer[1]-4],outer,p.rimHeight,.45,slab,{skip:gap,walk:true});
  // An ellipse is a provisional interpolation of the stated field envelope, not a traced as-built outline.
  ring(field,'field-envelope',[0,0],[p.fieldLength/2,p.fieldWidth/2],0,.25,turf,{walk:true});
  ring(circulation,'field-service-apron',[p.fieldLength/2,p.fieldWidth/2],inner,.03,.25,asphalt,{walk:true});
  const fl=p.footballLength,fw=p.footballWidth,end=fl/12;
  box(field,'football-playing-surface',[fl,.04,fw],[0,.035,0],turf,true);
  for(let i=0;i<10;i++)if(i%2===0)box(field,`turf-band-${i}`,[fl/12,.012,fw],[-fl/2+end+(i+.5)*fl/12,.061,0],stripe);
  for(const sign of [-1,1])box(field,`end-zone-${sign}`,[end,.025,fw],[sign*(fl/2-end/2),.075,0],cardinal);
  function line(name,x,z,w,d){return box(field,name,[w,.018,d],[x,.095,z],paint);}
  line('sideline-north',0,-fw/2,fl,.15);line('sideline-south',0,fw/2,fl,.15);
  for(let i=0;i<=12;i++)line(`yard-line-${i}`,-fl/2+i*end,0,.13,fw);
  for(let i=0;i<=100;i++){const x=-fl/2+end+i*(fl-2*end)/100;for(const z of [-3.1,3.1])line(`hash-${i}-${z}`,x,z,.1,.6);}
  for(const sign of [-1,1]){
    const x=sign*(fl/2+.6);
    cylinder(field,`goalpost-base-${sign}`,.12,.12,3,[x,1.5,0],gold);
    box(field,`goalpost-crossbar-${sign}`,[.15,.15,5.64],[x,3.05,0],gold);
    for(const z of [-2.82,2.82])cylinder(field,`goalpost-upright-${sign}-${z}`,.07,.07,5.5,[x,5.8,z],gold);
  }
  // Equal visual bands interpolate between measured overall heights. They are not a surveyed row inventory.
  const seatTransforms=[];const dummy=new THREE.Object3D();
  for(let row=0;row<p.visualRows;row++) {
    const t0=row/p.visualRows,t1=(row+1)/p.visualRows;
    const r0=[lerp(inner[0],outer[0]-3.8,t0),lerp(inner[1],outer[1]-3.8,t0)];
    const r1=[lerp(inner[0],outer[0]-3.8,t1),lerp(inner[1],outer[1]-3.8,t1)];
    const y=(row+1)*step;
    ring(bowl,`terrace-${String(row+1).padStart(3,'0')}`,r0,r1,y,step+.05,row%7===0?slab:concrete,{skip:a=>gap(a)||towerGap(a,t1),walk:true});
    const rx=lerp(r0[0],r1[0],.62),rz=lerp(r0[1],r1[1],.62);
    const circumference=Math.PI*(3*(rx+rz)-Math.sqrt((3*rx+rz)*(rx+3*rz)));
    const count=Math.floor(circumference/p.visualSeatSpacing);
    for(let s=0;s<count;s++){
      const a=s/count*TAU;
      const aisleDistance=Math.abs(((a+TAU/72)%(TAU/36))-TAU/72);
      if(gap(a)||towerGap(a,t1)||aisleDistance<1.1/Math.min(rx,rz))continue;
      seatTransforms.push({x:rx*Math.cos(a),y:y+.31,z:rz*Math.sin(a),a:Math.atan2(-Math.cos(a)/rx,-Math.sin(a)/rz)});
    }
  }
  const backs=new THREE.InstancedMesh(new THREE.BoxGeometry(.45,.48,.075),seatMat,seatTransforms.length);
  const pans=new THREE.InstancedMesh(new THREE.BoxGeometry(.45,.075,.38),seatMat,seatTransforms.length);
  backs.name='instanced-seat-backs';pans.name='instanced-seat-pans';
  for(let i=0;i<seatTransforms.length;i++){
    const s=seatTransforms[i];dummy.position.set(s.x,s.y,s.z);dummy.rotation.set(0,s.a,0);dummy.updateMatrix();backs.setMatrixAt(i,dummy.matrix);
    dummy.translateZ(-.15);dummy.position.y-=.20;dummy.updateMatrix();pans.setMatrixAt(i,dummy.matrix);
  }
  backs.instanceMatrix.needsUpdate=true;pans.instanceMatrix.needsUpdate=true;backs.receiveShadow=true;pans.receiveShadow=true;seats.add(backs,pans);
  // Street-level reference ring follows the interpolated bowl at its matching height.
  const streetT=p.streetHeight/p.rimHeight;
  const streetRx=lerp(...[inner[0],outer[0]-3.8,streetT]);
  const streetRz=lerp(...[inner[1],outer[1]-3.8,streetT]);
  ring(circulation,'street-reference-walk',[streetRx-.8,streetRz-.8],[streetRx+1.7,streetRz+1.7],p.streetHeight+.10,.16,slab,{skip:gap,walk:true});
  // Peristyle terrace connects the east opening to the surrounding street-level landscape.
  box(circulation,'peristyle-terrace',[48,.7,112],[142,p.streetHeight-.35,0],stone,true);
  stairs('east-field-to-plaza-stairs',[inner[0]-.6,.03,0],[119,p.streetHeight,0],6);
  for(const [i,a]of exteriorStairAngles.entries())stairs(`exterior-stairs-${i+1}`,radial(outer[0]+37,outer[1]+37,a,p.streetHeight+.04),radial(outer[0]-.2,outer[1]-.2,a,p.rimHeight),5);
  const aisleVertices=[];
  for(let row=0;row<p.visualRows;row++)for(let j=0;j<36;j++){
    const a=j/36*TAU,t0=row/p.visualRows,t1=(row+1)/p.visualRows;if(gap(a)||towerGap(a,t1))continue;
    const y=(row+1)*step+.015,rx0=lerp(inner[0],outer[0]-3.8,t0),rz0=lerp(inner[1],outer[1]-3.8,t0),rx1=lerp(inner[0],outer[0]-3.8,t1),rz1=lerp(inner[1],outer[1]-3.8,t1);
    const half=.85/Math.min(rx0,rz0),v0=radial(rx0,rz0,a-half,y),v1=radial(rx0,rz0,a+half,y),v2=radial(rx1,rz1,a+half,y),v3=radial(rx1,rz1,a-half,y);
    aisleVertices.push(...v0,...v1,...v2,...v0,...v2,...v3);
  }
  const aisleGeo=new THREE.BufferGeometry();aisleGeo.setAttribute('position',new THREE.Float32BufferAttribute(aisleVertices,3));aisleGeo.computeVertexNormals();
  const aisles=new THREE.Mesh(aisleGeo,slab);aisles.name='bowl-exploration-aisles';aisles.receiveShadow=true;circulation.add(aisles);
  // Schematic context paths; physical layout remains unverified.
  ring(circulation,'outer-grounds-loop',[outer[0]+24,outer[1]+24],[outer[0]+32,outer[1]+32],p.streetHeight+.045,.15,asphalt,{walk:true});
  box(circulation,'east-approach-plaza',[65,.12,124],[194,p.streetHeight,0],stone,true);
  box(circulation,'north-approach-path',[9,.12,65],[0,p.streetHeight,-168],slab,true);
  box(circulation,'south-approach-path',[9,.12,65],[0,p.streetHeight,168],slab,true);
  box(circulation,'west-approach-path',[70,.12,9],[-210,p.streetHeight,0],slab,true);
  box(context,'north-context-drive',[510,.12,15],[0,p.streetHeight-.02,-213],asphalt,true);
  box(context,'south-context-drive',[510,.12,15],[0,p.streetHeight-.02,213],asphalt,true);
  box(context,'west-context-drive',[15,.12,441],[-255,p.streetHeight-.02,0],asphalt,true);
  box(context,'east-context-drive',[15,.12,441],[255,p.streetHeight-.02,0],asphalt,true);
  // Curved historic wall assembled from fifteen actual open arch profiles.
  let z=-p.peristyleSpan/2;
  const smallWidth=(p.peristyleSpan-p.centralArchBay)/14;
  const wallThickness=p.peristyleDepth;
  for(let i=0;i<15;i++) {
    const bay=i===7?p.centralArchBay:smallWidth;
    const cz=z+bay/2;z+=bay;
    const h=i===7?p.centralArchHeight:p.smallArchHeight;
    const opening=bay-p.archPierWidth;
    const radius=opening/2,centerY=h-p.archCrownThickness-radius;
    const shape=new THREE.Shape();shape.moveTo(-bay/2,0);shape.lineTo(bay/2,0);shape.lineTo(bay/2,h);shape.lineTo(-bay/2,h);shape.closePath();
    const hole=new THREE.Path();hole.moveTo(-radius,0);hole.lineTo(-radius,centerY);hole.absarc(0,centerY,radius,Math.PI,0,true);hole.lineTo(radius,0);hole.closePath();shape.holes.push(hole);
    const geo=new THREE.ExtrudeGeometry(shape,{depth:wallThickness,bevelEnabled:false,curveSegments:14});geo.translate(0,0,-wallThickness/2);
    const mesh=new THREE.Mesh(geo,stone);mesh.name=`arch-${String(i+1).padStart(2,'0')}`;mesh.rotation.y=Math.PI/2;
    const px=p.peristyleX-.0028*cz*cz;mesh.position.set(px,p.streetHeight,cz);mesh.castShadow=true;mesh.receiveShadow=true;peristyle.add(mesh);
    for(const zz of [cz-bay/2+.34,cz+bay/2-.34]){
      const c=new THREE.Box3(new THREE.Vector3(px-wallThickness/2,p.streetHeight,zz-.45),new THREE.Vector3(px+wallThickness/2,p.streetHeight+h,zz+.45));colliders.push(c);
    }
    box(peristyle,`arch-cornice-${i}`,[wallThickness+1,.55,bay+.08],[px,p.streetHeight+h+.25,cz],slab);
  }
  const cauldronTop=p.streetHeight+p.cauldronAboveStreet;
  const centralTop=p.streetHeight+p.centralArchHeight;
  const columnBase=centralTop+.6;
  cylinder(peristyle,'cauldron-pedestal',1.75,2.4,cauldronTop-columnBase-2,[p.peristyleX,(columnBase+cauldronTop-2)/2,0],darkStone,16);
  cylinder(peristyle,'olympic-cauldron',3.4,1.6,2,[p.peristyleX,cauldronTop-1,0],gold,24);
  // Modern south tower: seven plan levels; floor heights and footprint are estimates.
  const tx=p.towerLength,td=p.towerDepth,tz=p.towerZ,base=p.streetHeight,top=base+p.towerAboveStreet;
  box(tower,'tower-rear-wall',[tx,p.towerAboveStreet-1,1.8],[0,(base+top-1)/2,tz+td/2],stone,false,true);
  box(tower,'tower-west-core',[8,p.towerAboveStreet-1,td],[-tx/2+4,(base+top-1)/2,tz],stone,false,true);
  box(tower,'tower-east-core',[8,p.towerAboveStreet-1,td],[tx/2-4,(base+top-1)/2,tz],stone,false,true);
  const levels=spec.towerLevels;
  for(let i=0;i<levels.length;i++){
    const y=base+levels[i].aboveStreet;
    const floor=box(tower,levels[i].id,[tx,.45,td],[0,y-.225,tz],slab,true);
    floor.userData={levelId:levels[i].id,label:levels[i].label,evidence:'estimated elevation; level identity from S01 plans'};
    const next=i===levels.length-1?top-.8:base+levels[i+1].aboveStreet;
    const gh=Math.max(.2,next-y-.55);
    box(tower,`glazed-front-${i}`,[tx-16,gh,.25],[0,y+gh/2+.2,tz-td/2+.6],glass,false,true);
    box(tower,`balcony-${i}`,[tx-5,.35,3],[0,y-.1,tz-td/2-1.0],slab,true);
    for(let x=-tx/2+12;x<tx/2-7;x+=8)box(tower,`mullion-${i}-${x}`,[.22,gh,.45],[x,y+gh/2+.2,tz-td/2+.4],stone);
  }
  box(tower,'tower-roof',[tx+8,.8,td+8],[0,top-.4,tz-1.8],slab);
  // Exterior buttresses and landscape are deliberately simple contextual geometry.
  for(let i=0;i<60;i++){
    const a=i/60*TAU;if(gap(a)||stairGap(a))continue;
    const x=outer[0]*Math.cos(a),zz=outer[1]*Math.sin(a);
    const pier=box(context,`perimeter-pier-${i}`,[1.5,p.rimHeight-p.streetHeight-2,2],[x,(p.rimHeight+p.streetHeight-2)/2,zz],darkStone);
    pier.rotation.y=-Math.atan2(zz/outer[1]**2,x/outer[0]**2);
  }
  for(let i=0;i<48;i++){
    const a=i/48*TAU;const r=i%2?1.22:1.32;
    const x=(outer[0]+20)*r*Math.cos(a),zz=(outer[1]+18)*r*Math.sin(a);
    cylinder(context,`tree-trunk-${i}`,.25,.37,6.8,[x,p.streetHeight+3.4,zz],darkStone,7);
    const crown=new THREE.Mesh(new THREE.IcosahedronGeometry(4.2,1),material('tree', '#486957'));
    crown.scale.set(1,1.3,1);crown.position.set(x,p.streetHeight+8.2,zz);crown.castShadow=true;context.add(crown);
  }
  const westScreenWidth=p.westScreenWidth,westScreenHeight=p.westScreenHeight;
  box(displays,'west-display-frame',[1.5,westScreenHeight+1,westScreenWidth+1],[-143,29,0],stone);
  box(displays,'west-display-face',[.18,westScreenHeight,westScreenWidth],[-142.1,29,0],dark);
  for(const zz of [-17,17])box(displays,`west-display-support-${zz}`,[1.1,17,1.1],[-143,14.5,zz],darkStone);
  anchors.field=new THREE.Vector3(0,0,0);
  anchors.street=new THREE.Vector3(0,p.streetHeight,0);
  anchors.lastRow=new THREE.Vector3(0,p.rimHeight,0);
  anchors.towerTop=new THREE.Vector3(0,top,tz);
  anchors.cauldronTop=new THREE.Vector3(p.peristyleX,cauldronTop,0);
  root.updateMatrixWorld(true);
  const landmarks=[
    {name:'The peristyle',position:[p.peristyleX,cauldronTop+1,0]},
    {name:'Scholarship Club Tower',position:[0,top+3,tz]},
    {name:'The field',position:[0,2,0]}
  ];
  return {root,components,walkables,navigationSurfaces,navigationWalkables:walkables,colliders,anchors,landmarks,seatCount:seatTransforms.length,spec};
}

export function checkModel(model) {
  const {components:c,anchors:a,spec}=model;
  const bounds=id=>new THREE.Box3().setFromObject(c[id]);
  const allBounds=Object.fromEntries(Object.keys(c).map(id=>{const b=bounds(id);return [id,{min:b.min.toArray(),max:b.max.toArray()}]}));
  const fieldMesh=c.field.getObjectByName('field-envelope');fieldMesh.geometry.computeBoundingBox();
  const fb=fieldMesh.geometry.boundingBox;
  const span=(mesh,axis)=>{mesh.geometry.computeBoundingBox();return mesh.geometry.boundingBox.max[axis]-mesh.geometry.boundingBox.min[axis];};
  const p=spec.parameters;
  const checks=[
    ['field-envelope-length','M017',fb.max.x-fb.min.x,p.fieldLength],
    ['field-envelope-max-width','M018',fb.max.z-fb.min.z,p.fieldWidth],
    ['football-length','M020',span(c.field.getObjectByName('football-playing-surface'),'x'),p.footballLength],
    ['football-width','M021',span(c.field.getObjectByName('football-playing-surface'),'z'),p.footballWidth],
    ['field-to-street','M011',a.street.y-a.field.y,p.streetHeight],
    ['field-to-last-row','M012',allBounds.bowl.max[1],p.rimHeight],
    ['street-to-last-row','M013',allBounds.bowl.max[1]-a.street.y,22.8346],
    ['tower-above-street','M014',allBounds.tower.max[1]-a.street.y,p.towerAboveStreet],
    ['cauldron-above-street','M015',allBounds.peristyle.max[1]-a.street.y,p.cauldronAboveStreet],
    ['peristyle-arch-count','M016',c.peristyle.children.filter(n=>/^arch-\d+$/.test(n.name)).length,15],
    ['west-screen-width','M072',span(c.displays.getObjectByName('west-display-face'),'z'),p.westScreenWidth],
    ['west-screen-height','M073',span(c.displays.getObjectByName('west-display-face'),'y'),p.westScreenHeight]
  ];
  return {revision:spec.revision,generatorVersion:GENERATOR_VERSION,units:'meters',targetPhysicalToleranceM:.30,
    scope:'Generated geometry checked against chosen published controls. These are source-consistency checks, not independent measurements of the venue.',
    physicalAccuracy:'UNVERIFIED: the full model is not certified within 0.30 m of the physical venue.',
    physicalAcceptance:{status:'NOT_VALIDATED',targetStatus:'provisional engineering target',
      requirementId:'SR-3D-10',featureTolerancesApproved:false,
      note:'Implementation tolerances below test generator arithmetic, not physical positional accuracy.'},
    notValidatedChecks:[{id:'historic-provisional-envelope-length',measurementId:'M158',
      actual:allBounds.bowl.max[0]-allBounds.bowl.min[0],expected:p.bowlLength,status:'BOUNDARY_UNRESOLVED',
      reason:'Partial bowl group excludes the east opening; historic approximate overall ellipse endpoints are not equivalent. No pass/fail tolerance assigned.'},
      {id:'field-varying-width',measurementId:'M019',status:'BOUNDARY_UNRESOLVED',
        reason:'Guide minimum 222 ft has no established station or corresponding modeled boundary.'}],
    checks:checks.map(([id,measurementId,actual,expected])=>({id,measurementId,actual,expected,error:Math.abs(actual-expected),implementationTolerance:id==='peristyle-arch-count'?0:.005,pass:Math.abs(actual-expected)<.005})),
    componentBounds:allBounds,estimatedGeometry:spec.assumptions,independentPhysicalChecks:0};
}
