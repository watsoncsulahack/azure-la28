"""IFC4 and GLB from tessellation of a reopened native FreeCAD reference file."""
import argparse,json,struct,uuid,hashlib
from pathlib import Path
import numpy as np
import ifcopenshell
import ifcopenshell.api.project,ifcopenshell.api.root,ifcopenshell.api.context,ifcopenshell.api.unit
import ifcopenshell.api.aggregate,ifcopenshell.api.spatial,ifcopenshell.api.geometry,ifcopenshell.api.pset

ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--work',type=Path,required=True);args=ap.parse_args();root=args.package.resolve()
data=json.loads((args.work/'cad-meshes.json').read_text());spec=json.loads((root/'inputs/venue.json').read_text());cad_path=root/'models/coliseum-reference-R001.FCStd';cad_hash=hashlib.sha256(cad_path.read_bytes()).hexdigest()
model=ifcopenshell.api.project.create_file(version='IFC4')
def entity(cls,name,key):
 e=ifcopenshell.api.root.create_entity(model,ifc_class=cls,name=name);e.GlobalId=ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL,'coliseum-reference/R001/'+key).hex);return e
project=entity('IfcProject','Coliseum Reference R001','project');project.Description='Independent reconstruction reference; no verified physical +/-0.30 m accuracy; not for construction.'
metre=model.createIfcSIUnit(UnitType='LENGTHUNIT',Name='METRE');area=model.createIfcSIUnit(UnitType='AREAUNIT',Name='SQUARE_METRE');volume=model.createIfcSIUnit(UnitType='VOLUMEUNIT',Name='CUBIC_METRE');ifcopenshell.api.unit.assign_unit(model,units=[metre,area,volume])
context=ifcopenshell.api.context.add_context(model,context_type='Model');context.Precision=1e-6
body=ifcopenshell.api.context.add_context(model,context_type='Model',context_identifier='Body',target_view='MODEL_VIEW',parent=context)
site=entity('IfcSite','Local reference site (not georeferenced)','site');building=entity('IfcBuilding','Los Angeles Memorial Coliseum','building')
ifcopenshell.api.aggregate.assign_object(model,products=[site],relating_object=project);ifcopenshell.api.aggregate.assign_object(model,products=[building],relating_object=site)
for e in [site,building]:ifcopenshell.api.geometry.edit_object_placement(model,product=e,matrix=np.eye(4),is_si=True)
storeys={}
for level in spec['towerLevels']:
 e=entity('IfcBuildingStorey',level['label']+' (estimated elevation)',level['id']);e.Elevation=spec['parameters']['streetHeight']+level['aboveStreet'];storeys[level['id']]=e
 ifcopenshell.api.aggregate.assign_object(model,products=[e],relating_object=building)
 matrix=np.eye(4);matrix[2,3]=e.Elevation;ifcopenshell.api.geometry.edit_object_placement(model,product=e,matrix=matrix,is_si=True)
 prop=ifcopenshell.api.pset.add_pset(model,product=e,name='Coliseum_Reference');ifcopenshell.api.pset.edit_pset(model,pset=prop,properties={'StableId':level['id'],'ElevationEvidence':'Estimated; level identity from S01 plans','SourceDrawingIds':'D03;D04;D05;D06;D07;D08'})
for component in data['components']:
 obj=entity('IfcBuildingElementProxy',component['name'],component['id']);obj.ObjectType=component['group']+' reference component'
 vertices=np.array(component['vertices']);origin=np.array(component['bounds']['min']);local=(vertices-origin).tolist()
 representation=ifcopenshell.api.geometry.add_mesh_representation(model,context=body,vertices=[local],faces=[component['faces']],unit_scale=1.0)
 for item in representation.Items:
  if hasattr(item,'Closed'):item.Closed=component['solid']
 ifcopenshell.api.geometry.assign_representation(model,product=obj,representation=representation)
 container=storeys.get(component['towerLevel'],building);ifcopenshell.api.spatial.assign_container(model,products=[obj],relating_structure=container)
 matrix=np.eye(4);matrix[:3,3]=origin;ifcopenshell.api.geometry.edit_object_placement(model,product=obj,matrix=matrix,is_si=True)
 prop=ifcopenshell.api.pset.add_pset(model,product=obj,name='Coliseum_Reference')
 ifcopenshell.api.pset.edit_pset(model,pset=prop,properties={'StableId':component['id'],'ComponentGroup':component['group'],'EvidenceClass':component['evidenceClass'],'MeasurementAndDrawingIds':';'.join(component['sourceIds']),'AssumptionIds':';'.join(component['assumptionIds']),'Revision':'R001','TargetPhysicalAccuracyMetres':.30,'PhysicalAccuracyVerified':False,'GeometrySource':'Reopened FreeCAD document; tessellated BRep','NominalDeflectionMetres':.05,'FreeCADFileSHA256':cad_hash})
model.header.file_name.name='coliseum-reference-R001.ifc';model.header.file_name.author=('Independent Coliseum research project',);model.header.file_name.organization=('Educational reconstruction reference',)
model.write(str(root/'models/coliseum-reference-R001.ifc'))

# glTF uses metres and Y up; map CAD (east,north,up) to (east,up,south).
binary=bytearray();views=[];accessors=[];meshes=[];nodes=[];materials=[];material_ids={}
def append_buffer(array,target):
 while len(binary)%4:binary.append(0)
 offset=len(binary);raw=array.tobytes();binary.extend(raw);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(raw),'target':target});return len(views)-1

def accessor(array,type,component_type,target,bounds=False):
 i=append_buffer(array,target);a={'bufferView':i,'byteOffset':0,'componentType':component_type,'count':len(array),'type':type}
 if bounds:a.update(min=array.min(axis=0).astype(float).tolist(),max=array.max(axis=0).astype(float).tolist())
 accessors.append(a);return len(accessors)-1

def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
for comp in data['components']:
 cad=np.asarray(comp['vertices'],dtype=np.float64);positions=np.column_stack([cad[:,0],cad[:,2],-cad[:,1]]).astype('<f4');faces=np.asarray(comp['faces'],dtype='<u4')
 normals=np.zeros_like(positions);tri=positions[faces];face_normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
 for col in range(3):np.add.at(normals,faces[:,col],face_normals)
 length=np.linalg.norm(normals,axis=1);normals[length>0]/=length[length>0,None]
 color=comp['color']
 if color not in material_ids:
  rgb=[linear(int(color[i:i+2],16)/255) for i in [1,3,5]];material_ids[color]=len(materials);materials.append({'name':color,'doubleSided':not comp['solid'],'pbrMetallicRoughness':{'baseColorFactor':rgb+[1.0],'metallicFactor':0.0,'roughnessFactor':.84}})
 pos=accessor(positions,'VEC3',5126,34962,True);normal=accessor(normals.astype('<f4'),'VEC3',5126,34962);indices=accessor(faces.reshape(-1),'SCALAR',5125,34963)
 meshes.append({'name':comp['id'],'primitives':[{'attributes':{'POSITION':pos,'NORMAL':normal},'indices':indices,'material':material_ids[color]}]})
 nodes.append({'name':comp['id'],'mesh':len(meshes)-1,'extras':{'StableId':comp['id'],'EvidenceClass':comp['evidenceClass'],'SourceIds':comp['sourceIds'],'AssumptionIds':comp['assumptionIds']}})
gltf={'asset':{'version':'2.0','generator':'Coliseum reference R001 / reopened FreeCAD BRep tessellation'},'scene':0,'scenes':[{'name':'Coliseum Reference R001','nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':meshes,'materials':materials,'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors,'extras':{'revision':'R001','sourceFile':cad_path.name,'sourceSHA256':cad_hash,'units':'meters','coordinateTransform':'CAD [X east,Y north,Z up] -> GLB [X east,Y up,Z south]','physicalAccuracy':'unverified','tessellationDeflectionM':.05}}
js=json.dumps(gltf,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
with (root/'models/coliseum-reference-R001.glb').open('wb')as f:f.write(struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(binary)));f.write(struct.pack('<I4s',len(js),b'JSON'));f.write(js);f.write(struct.pack('<I4s',len(binary),b'BIN\0'));f.write(binary)
print(json.dumps({'IFC':'IFC4','components':len(nodes),'storeys':len(storeys),'glbBytes':12+8+len(js)+8+len(binary),'cadSourceSHA256':cad_hash}))
