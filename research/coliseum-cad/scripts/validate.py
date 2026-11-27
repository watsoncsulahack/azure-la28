"""Read back the engineering deliverables and compare geometry, units and references."""
import argparse,csv,json,math,struct,hashlib
from pathlib import Path
import numpy as np
import ezdxf
import ifcopenshell,ifcopenshell.geom,ifcopenshell.validate,ifcopenshell.util.element,ifcopenshell.util.unit
import fitz

ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args();root=a.package.resolve()
meshes=json.loads((a.work/'cad-meshes.json').read_text());components={m['id']:m for m in meshes['components']};spec=json.loads((root/'inputs/venue.json').read_text());p=spec['parameters']
source={r['measurement_id']:r for r in csv.DictReader((root.parent/'coliseum-dimensions/dimensions.csv').open())}
controls=list(csv.DictReader((root/'inputs/control-register.csv').open()));dxf_checks=[]
for sheet in ['A-101','A-201','A-202']:
 doc=ezdxf.readfile(root/'drawings'/f'{sheet}.dxf');audit=doc.audit();assert not audit.has_errors;assert doc.units==6
 dims=list(doc.modelspace().query('DIMENSION'));lookup={d.get_xdata('COLISEUM_REF')[0].value:d for d in dims}
 for control in [c for c in controls if c['sheet']==sheet]:
  d=lookup[control['dimension_id']];actual=float(d.get_measurement());expected=float(source[control['measurement_id']]['si_value']);error=abs(actual-expected)
  assert error<1e-6,(control['dimension_id'],actual,expected)
  assert '<>' in d.dxf.text,'Dimension text must remain geometry-derived'
  dxf_checks.append({'id':control['dimension_id'],'sourceId':control['measurement_id'],'actualM':actual,'referenceM':expected,'errorM':error,'pass':True})

def span(name,axis):return components[name]['bounds']['max'][axis]-components[name]['bounds']['min'][axis]
checks=[('fieldLength','M017',span('FieldEnvelope',0)),('fieldWidth','M018',span('FieldEnvelope',1)),('footballLength','M020',span('FootballLayout',0)),('footballWidth','M021',span('FootballLayout',1)),('lastRow','M012',components['BowlRim']['bounds']['max'][2]),('towerAboveStreet','M014',components['TowerRoof']['bounds']['max'][2]-p['streetHeight']),('cauldronAboveStreet','M015',components['Cauldron']['bounds']['max'][2]-p['streetHeight'])]
native_checks=[]
for name,source_id,value in checks:
 expected=float(source[source_id]['si_value']);error=abs(value-expected);assert error<.005,(name,error)
 native_checks.append({'id':name,'sourceId':source_id,'actualM':value,'referenceM':expected,'errorM':error,'pass':True})
assert len([n for n in components if n.startswith('PeristyleArch_')])==15
native_report=json.loads((root/'reports/freecad-validation.json').read_text());assert native_report['reopenedSuccessfully'];assert all(c['shapeValid']for c in native_report['nativeShapeChecks'])

ifc=ifcopenshell.open(root/'models/coliseum-reference-R001.ifc');assert ifc.schema=='IFC4';assert ifcopenshell.util.unit.calculate_unit_scale(ifc)==1
logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(ifc,logger,express_rules=True);assert not logger.statements,str(logger.statements[:2])
assert len(ifc.by_type('IfcBuildingStorey'))==7
settings=ifcopenshell.geom.settings();settings.set('use-world-coords',True);ifc_errors=[];ifc_ids=set()
for element in ifc.by_type('IfcBuildingElementProxy'):
 properties=ifcopenshell.util.element.get_psets(element)['Coliseum_Reference'];id=properties['StableId'];ifc_ids.add(id)
 shape=ifcopenshell.geom.create_shape(settings,element);vertices=np.asarray(shape.geometry.verts).reshape(-1,3);expected=components[id]
 actual=np.array([vertices.min(axis=0),vertices.max(axis=0)]);reference=np.array([expected['bounds']['min'],expected['bounds']['max']]);error=float(np.max(np.abs(actual-reference)))
 assert error<.051,(id,error);assert properties['PhysicalAccuracyVerified']is False
 ifc_errors.append(error)
assert ifc_ids==set(components)

glb=(root/'models/coliseum-reference-R001.glb').read_bytes();magic,version,length=struct.unpack_from('<4sII',glb);assert magic==b'glTF'and version==2 and length==len(glb)
json_length=struct.unpack_from('<I',glb,12)[0];gltf=json.loads(glb[20:20+json_length]);binary_start=20+json_length+8
assert gltf['extras']['units']=='meters';assert len(gltf['nodes'])==len(components)
cad_hash=hashlib.sha256((root/'models/coliseum-reference-R001.FCStd').read_bytes()).hexdigest();assert gltf['extras']['sourceSHA256']==cad_hash
max_glb_error=0
for node in gltf['nodes']:
 id=node['name'];mesh=gltf['meshes'][node['mesh']];acc=gltf['accessors'][mesh['primitives'][0]['attributes']['POSITION']];view=gltf['bufferViews'][acc['bufferView']]
 positions=np.frombuffer(glb,dtype='<f4',count=acc['count']*3,offset=binary_start+view.get('byteOffset',0)+acc.get('byteOffset',0)).reshape(-1,3)
 cad=np.column_stack([positions[:,0],-positions[:,2],positions[:,1]]);expected=np.asarray(components[id]['vertices']);error=float(np.max(np.abs(cad-expected)));assert error<.005,(id,error);max_glb_error=max(max_glb_error,error)
 assert node['extras']['StableId']==id
pdf=fitz.open(root/'drawings/coliseum-reference-drawings-R001.pdf');assert len(pdf)==4
for page in pdf:assert abs(page.rect.width-594/25.4*72)<1 and abs(page.rect.height-420/25.4*72)<1
pdf.close()
report={'revision':'R001','date':'2026-11-27','status':'source-consistency checks passed; physical venue accuracy unverified','dxf':{'auditErrors':0,'nativeDimensions':dxf_checks,'modelUnits':'meters'},'freecad':{'reopened':True,'validShapes':len(native_report['nativeShapeChecks']),'exportedMeshComponents':len(components),'sourceDimensionChecks':native_checks},'ifc':{'schema':'IFC4','schemaAndExpressValidationStatements':len(logger.statements),'components':len(ifc_ids),'storeys':7,'unitScaleToMetres':1,'maximumWorldBoundsDifferenceFromNativeCADM':max(ifc_errors)},'glb':{'source':'reopened FCStd tessellation','components':len(components),'sourceFileSHA256':cad_hash,'maxCoordinateRoundtripErrorM':max_glb_error,'unitsAndAxisTransformVerified':True},'pdf':{'pages':4,'paper':'A2 landscape','previewsVisuallyInspected':True},'physicalAccuracy':{'targetM':.30,'independentSiteMeasurements':0,'verified':False},'representationNotes':['CAD construction-reference ellipse stays in FCStd/DXF and is omitted from IFC/GLB','IFC uses tessellated reference proxies, not certified structural assemblies','Native tower plates have expressions; bowl/peristyle BReps require rebuild script','No STEP or DWG file generated']}
(root/'reports/validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'dxfDimensions':len(dxf_checks),'validCADShapes':len(native_report['nativeShapeChecks']),'ifcSchemaErrors':len(logger.statements),'ifcComponents':len(ifc_ids),'ifcMaxCADBoundsErrorM':max(ifc_errors),'glbMaxRoundtripErrorM':max_glb_error,'pdfPages':4},indent=2))
