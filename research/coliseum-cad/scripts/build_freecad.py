"""Create native CAD solids from reference parameters; run with a FreeCAD-enabled Python.

No STEP files are used. FreeCAD stores geometry internally in millimeters.
"""
import argparse,sys,json,math,hashlib
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--freecad-lib',default='/usr/lib/freecad-python3/lib');args=parser.parse_args()
sys.path.insert(0,args.freecad_lib)
import FreeCAD as App
import Part

package=args.package.resolve();work=args.work.resolve();work.mkdir(parents=True,exist_ok=True)
spec=json.loads((package/'inputs/venue.json').read_text());p=spec['parameters'];S=1000.0
V=lambda x,y,z:App.Vector(x*S,y*S,z*S)
doc=App.newDocument('Coliseum_Reference_R001')
doc.Label='Coliseum | Reference R001 | metres displayed'
parameters=doc.addObject('App::FeaturePython','ReferenceParameters');parameters.Label='Reference parameters (internal mm; project m)'
for key,value in p.items():
 if key in ['visualRows','visualSeatSpacing','peristyleOpeningHalfAngle']:continue
 parameters.addProperty('App::PropertyLength',key,'Dimensions (source and estimated)');setattr(parameters,key,value*S)
parameters.addProperty('App::PropertyString','AccuracyStatus','Reference');parameters.AccuracyStatus='Source-consistent approximation; physical +/-0.30 m target UNVERIFIED'
parameters.addProperty('App::PropertyString','CoordinateSystem','Reference');parameters.CoordinateSystem='X east, Y north, Z up; local field datum Z=0; NOT surveyed'
parameters.addProperty('App::PropertyString','InputSHA256','Reference');parameters.InputSHA256=hashlib.sha256((package/'inputs/venue.json').read_bytes()).hexdigest()
groups={}
for name,label in [('Field','Field reference'),('Bowl','Estimated seating-bowl profiles'),('Tower','South tower reference'),('Peristyle','Peristyle and cauldron reference')]:
 group=doc.addObject('App::DocumentObjectGroup',name);group.Label=label;groups[name]=group
records=[]
def annotate(obj,group,stable_id,label,evidence,sources,assumptions,color,level=None):
 obj.Label=label
 for name,value in [('StableId',stable_id),('EvidenceClass',evidence),('SourceIds',';'.join(sources)),('AssumptionIds',';'.join(assumptions)),('ColorHex',color),('TowerLevel',level or '')]:
  obj.addProperty('App::PropertyString',name,'Reference provenance');setattr(obj,name,value)
 groups[group].addObject(obj);records.append(obj);return obj

def add_shape(name,shape,group,label,evidence,sources,assumptions,color,level=None):
 obj=doc.addObject('Part::Feature',name);obj.Shape=shape
 return annotate(obj,group,name,label,evidence,sources,assumptions,color,level)

def box(name,l,w,h,x,y,z,group,label,sources,assumptions,color='#c3c1b6',level=None):
 obj=doc.addObject('Part::Box',name);obj.Length=l*S;obj.Width=w*S;obj.Height=h*S;obj.Placement.Base=V(x,y,z)
 return annotate(obj,group,name,label,'source-anchored; estimated details',sources,assumptions,color,level)

def ellipse_face(rx,ry,z):
 return Part.Face(Part.Wire([Part.Ellipse(V(0,0,z),rx*S,ry*S).toShape()]))

def sector_cutter(a0,a1,z,height):
 points=[V(0,0,z),V(600*math.cos(a0),600*math.sin(a0),z),V(600*math.cos(a1),600*math.sin(a1),z),V(0,0,z)]
 return Part.Face(Part.makePolygon(points)).extrude(V(0,0,height))

field_shape=ellipse_face(p['fieldLength']/2,p['fieldWidth']/2,-.25).extrude(V(0,0,.25))
add_shape('FieldEnvelope',field_shape,'Field','Field envelope | interpolated ellipse','source extents; estimated outline',['M017','M018','M019'],['A003'],'#426a4c')
l,w=p['footballLength'],p['footballWidth'];pts=[V(-l/2,-w/2,.015),V(l/2,-w/2,.015),V(l/2,w/2,.015),V(-l/2,w/2,.015),V(-l/2,-w/2,.015)]
add_shape('FootballLayout',Part.Face(Part.makePolygon(pts)),'Field','Maximum football layout | graphic surface','source-reported extent',['M020','M021'],['A008'],'#78a06e')
outer=[p['bowlLength']/2,p['bowlWidth']/2];inner=[p['innerBowlLength']/2,p['innerBowlWidth']/2]
reference=add_shape('HistoricBowlEnvelope',Part.Wire([Part.Ellipse(V(0,0,0),outer[0]*S,outer[1]*S).toShape()]),'Bowl','CONSTRUCTION REFERENCE | approximate historic envelope','historic approximate reference only',['M158','M159'],['A001'],'#886c48')
reference.addProperty('App::PropertyBool','ConstructionReference','Reference provenance');reference.ConstructionReference=True
east=sector_cutter(-p['peristyleOpeningHalfAngle'],p['peristyleOpeningHalfAngle'],-1,p['rimHeight']+3)
south=sector_cutter(-2.14,-1.0,-1,p['rimHeight']+3)
rows=p['visualRows'];rise=p['rimHeight']/rows
for i in range(rows):
 t0=i/rows;t1=(i+1)/rows;z=i*rise
 r0=[inner[a]+(outer[a]-3.8-inner[a])*t0 for a in [0,1]];r1=[inner[a]+(outer[a]-3.8-inner[a])*t1 for a in [0,1]]
 shape=ellipse_face(*r1,z).cut(ellipse_face(*r0,z)).extrude(V(0,0,rise)).cut(east)
 if t1>.36:shape=shape.cut(south)
 add_shape(f'BowlBand_{i+1:03}',shape,'Bowl',f'Estimated bowl band {i+1:02} of {rows}','historic approximate envelope; estimated profile',['M012','M013','M158','M159'],['A001','A002'],'#c3c1b6')
# Thin rim connects the interpolated seating profile to the provisional historic envelope.
z=p['rimHeight']-.45
rim=ellipse_face(*outer,z).cut(ellipse_face(outer[0]-4,outer[1]-4,z)).extrude(V(0,0,.45)).cut(east)
add_shape('BowlRim',rim,'Bowl','Last-row / rim reference','source height; provisional historic footprint',['M012','M158','M159'],['A001','A002'],'#ded5bf')

base=p['streetHeight'];tx,td,tz=p['towerLength'],p['towerDepth'],p['towerZ'];top=base+p['towerAboveStreet']
for level in spec['towerLevels']:
 y=base+level['aboveStreet']
 obj=box(level['id'].replace('-','_'),tx,td,.45,-tx/2,-tz-td/2,y-.45,'Tower',level['label']+' | estimated elevation',['M014',*next(c for c in spec['components'] if c['id']=='tower').get('drawingIds',[])],['A004'],'#ded5bf',level['id'])
 obj.setExpression('Length','ReferenceParameters.towerLength');obj.setExpression('Width','ReferenceParameters.towerDepth')
 obj.setExpression('Placement.Base.x','-ReferenceParameters.towerLength / 2')
 obj.setExpression('Placement.Base.y','-ReferenceParameters.towerZ - ReferenceParameters.towerDepth / 2')
 obj.setExpression('Placement.Base.z',f'ReferenceParameters.streetHeight + {level["aboveStreet"]*S} mm - 450 mm')
box('TowerRearWall',tx,1.8,p['towerAboveStreet']-.8,-tx/2,-tz-td/2,base,'Tower','Estimated tower rear envelope',['M014'],['A004'])
box('TowerWestCore',8,td,p['towerAboveStreet']-.8,-tx/2,-tz-td/2,base,'Tower','Estimated west tower core',['M014'],['A004'])
box('TowerEastCore',8,td,p['towerAboveStreet']-.8,tx/2-8,-tz-td/2,base,'Tower','Estimated east tower core',['M014'],['A004'])
roof=box('TowerRoof',tx+8,td+8,.8,-(tx+8)/2,-tz-(td+8)/2,top-.8,'Tower','Tower overall-height reference',['M014'],['A004'],'#ded5bf')
roof.setExpression('Placement.Base.z','ReferenceParameters.streetHeight + ReferenceParameters.towerAboveStreet - 800 mm')

z_along=-p['peristyleSpan']/2;small=(p['peristyleSpan']-p['centralArchBay'])/14
for i in range(15):
 bay=p['centralArchBay'] if i==7 else small;cz=z_along+bay/2;z_along+=bay
 cx=p['peristyleX']-.0028*cz*cz;cy=-cz;h=p['centralArchHeight'] if i==7 else p['smallArchHeight'];depth=p['peristyleDepth'];radius=(bay-p['archPierWidth'])/2
 opening_center=base+h-p['archCrownThickness']-radius
 wall=Part.makeBox(depth*S,bay*S,h*S,V(cx-depth/2,cy-bay/2,base))
 opening_rect=Part.makeBox((depth+2)*S,radius*2*S,(opening_center-base+.1)*S,V(cx-depth/2-1,cy-radius,base-.1))
 opening_round=Part.makeCylinder(radius*S,(depth+2)*S,V(cx-depth/2-1,cy,opening_center),App.Vector(1,0,0))
 shape=wall.cut(opening_rect).cut(opening_round)
 add_shape(f'PeristyleArch_{i+1:02}',shape,'Peristyle',f'Peristyle arch bay {i+1:02}','source arch count; estimated dimensions',['M016'],['A005'],'#d6ccad')
cauldron_top=base+p['cauldronAboveStreet'];column_base=base+p['centralArchHeight']+.6
ped=Part.makeCone(2.4*S,1.75*S,(cauldron_top-column_base-2)*S,V(p['peristyleX'],0,column_base))
add_shape('CauldronPedestal',ped,'Peristyle','Estimated cauldron pedestal','estimated geometry',['M015'],['A005'],'#a49f8d')
cup=Part.makeCone(1.6*S,3.4*S,2*S,V(p['peristyleX'],0,cauldron_top-2))
add_shape('Cauldron',cup,'Peristyle','Cauldron overall-height reference','source overall height; estimated form',['M015'],['A005'],'#d4ae57')

# Recompute and save an actual native FreeCAD document, then reopen before tessellation.
doc.recompute()
path=package/'models/coliseum-reference-R001.FCStd'
if path.exists():path.replace(work/'previous-reference.FCStd')
doc.saveAs(str(path));App.closeDocument(doc.Name)
doc=App.openDocument(str(path));doc.recompute()
meshes=[];checks=[]
for obj in doc.Objects:
 if not hasattr(obj,'StableId') or not hasattr(obj,'Shape') or obj.Shape.isNull():continue
 shape=obj.Shape
 if not shape.isValid():raise RuntimeError('Invalid CAD shape '+obj.Name)
 vertices,faces=shape.tessellate(50.0) # 50 mm nominal linear deflection, 0.05 m project units.
 bounds=shape.optimalBoundingBox(False,False) # Measure analytic BRep, never the cached display triangulation.
 checks.append({'id':obj.StableId,'shapeValid':True,'solidCount':len(shape.Solids),'triangleCount':len(faces),'exportedMesh':bool(faces)})
 if not faces:continue # CAD construction wires stay in FCStd and the DXF, not the rendered IFC/GLB.
 record={'id':obj.StableId,'name':obj.Label,'group':obj.InList[0].Name if obj.InList else '', 'evidenceClass':obj.EvidenceClass,'sourceIds':obj.SourceIds.split(';'),'assumptionIds':obj.AssumptionIds.split(';'),'color':obj.ColorHex,'towerLevel':obj.TowerLevel,'vertices':[[v.x/S,v.y/S,v.z/S] for v in vertices],'faces':[list(f) for f in faces],'solid':len(shape.Solids)>0,'bounds':{'min':[bounds.XMin/S,bounds.YMin/S,bounds.ZMin/S],'max':[bounds.XMax/S,bounds.YMax/S,bounds.ZMax/S]},'volumeM3':shape.Volume/S**3}
 meshes.append(record)
if len(meshes)<100:raise RuntimeError('Unexpectedly incomplete reference model')
(work/'cad-meshes.json').write_text(json.dumps({'revision':'R001','coordinates':'X east, Y north, Z up; meters','sourceFile':path.name,'tessellationDeflectionM':.05,'components':meshes},separators=(',',':')))
report={'freecadVersion':App.Version(),'reopenedSuccessfully':True,'nativeUnit':'millimeter','projectUnit':'meter','nativeShapeChecks':checks,'inputSHA256':hashlib.sha256((package/'inputs/venue.json').read_bytes()).hexdigest(),'associativity':'Tower plate sizes/placements and roof elevation include native expressions; generated bowl/peristyle BReps require the supplied rebuild script after input edits. Construction-reference wire is omitted from IFC/GLB.'}
(package/'reports/freecad-validation.json').write_text(json.dumps(report,indent=2)+'\n');App.closeDocument(doc.Name)
print(json.dumps({'file':str(path),'objects':len(meshes),'validatedNativeShapes':len(checks)}))
