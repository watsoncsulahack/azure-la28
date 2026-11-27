import {readFile,writeFile} from 'node:fs/promises';
import {buildVenue} from '../dist/model.js';
import {GLTFExporter} from '../dist/vendor/GLTFExporter.js';

// Browser FileReader equivalent for the texture-free binary exporter under Node.
globalThis.FileReader=class{
  readAsArrayBuffer(blob){blob.arrayBuffer().then(value=>{this.result=value;this.onloadend?.();}).catch(error=>this.onerror?.(error));}
  readAsDataURL(blob){blob.arrayBuffer().then(value=>{this.result=`data:${blob.type};base64,${Buffer.from(value).toString('base64')}`;this.onloadend?.();}).catch(error=>this.onerror?.(error));}
};
const spec=JSON.parse(await readFile(new URL('../dist/data/venue.json',import.meta.url)));
const model=buildVenue(spec);
const glb=await new GLTFExporter().parseAsync(model.root,{binary:true,onlyVisible:false});
const bytes=Buffer.from(glb);
if(bytes.toString('utf8',0,4)!=='glTF')throw Error('Invalid GLB header');
const jsonSize=bytes.readUInt32LE(12);
const gltf=JSON.parse(bytes.toString('utf8',20,20+jsonSize).trim());
const nodes=gltf.nodes.map(n=>n.name);
for(const c of spec.components)if(!nodes.includes(c.id))throw Error(`Missing exported component ${c.id}`);
if(!gltf.extensionsUsed?.includes('EXT_mesh_gpu_instancing'))throw Error('Seating instance transforms were not preserved');
const target=new URL(`../dist/coliseum-${spec.revision}.glb`,import.meta.url);
await writeFile(target,bytes);
console.log(JSON.stringify({file:target.pathname,bytes:bytes.length,nodes:gltf.nodes.length,meshInstancing:true,componentIdentitiesPreserved:true}));
