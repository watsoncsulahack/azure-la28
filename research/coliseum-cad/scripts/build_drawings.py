"""Native, meter-based DXF geometry/dimensions with A2 paper layouts and PDF previews."""
import os,json,math,csv,argparse
from pathlib import Path
os.environ.setdefault('MPLBACKEND','Agg')
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[3]/'work/coliseum-cad/matplotlib'))
import ezdxf
from ezdxf import units
from ezdxf.addons.drawing import Frontend,RenderContext,layout,config
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path,default=Path(__file__).resolve().parents[1]);args=parser.parse_args();root=args.package.resolve();spec=json.loads((root/'inputs/venue.json').read_text());p=spec['parameters']
source_dir=root.parent/'coliseum-dimensions';sources={r['measurement_id']:r for r in csv.DictReader((source_dir/'dimensions.csv').open())}
OUTLINE='A-REFR-SRCE';EST='A-REFR-ESTM';HIST='A-AREA-HIST';SEAT='A-SEAT-ESTM';DIM='A-ANNO-DIMS';TEXT='A-ANNO-NOTE';DATUM='A-ANNO-DATM'
layers={OUTLINE:(7,'CONTINUOUS',35),EST:(8,'DASHED',18),HIST:(30,'DASHED',25),SEAT:(8,'CONTINUOUS',13),DIM:(3,'CONTINUOUS',18),TEXT:(7,'CONTINUOUS',18),DATUM:(4,'CENTER',13)}
register=[];drawing_reports=[]
def new_doc(sheet,title,subtitle,scale=1000,center=(0,0),view_height=None):
 doc=ezdxf.new('R2013',setup=True);doc.units=units.M;doc.header['$INSUNITS']=6;doc.header['$MEASUREMENT']=1;doc.header['$LUNITS']=2;doc.header['$LUPREC']=4
 doc.appids.add('COLISEUM_REF')
 for name,(color,linetype,weight)in layers.items():doc.layers.new(name,dxfattribs={'color':color,'linetype':linetype,'lineweight':weight})
 doc.dimstyles.new('REFERENCE_M',dxfattribs={'dimtxt':2.5,'dimasz':2.2,'dimexe':1.0,'dimexo':.7,'dimgap':.7,'dimdec':2,'dimtad':1,'dimclrd':3,'dimclre':3,'dimclrt':7,'dimzin':0,'dimtih':0,'dimtoh':0})
 msp=doc.modelspace();paper=doc.layouts.new(sheet);paper.page_setup(size=(594,420),margins=(10,10,10,10),units='mm')
 paper.add_lwpolyline([(0,0),(574,0),(574,400),(0,400)],close=True,dxfattribs={'color':7,'lineweight':35})
 paper.add_line((0,50),(574,50));paper.add_line((450,0),(450,50))
 def pt(s,x,y,h=2.5):paper.add_text(s,dxfattribs={'height':h,'insert':(x,y),'color':7})
 pt('LOS ANGELES MEMORIAL COLISEUM',12,37,4);pt(title,12,27,3.5);pt(subtitle,12,18,2.3)
 pt('REFERENCE RECONSTRUCTION | NOT AS-BUILT / NOT FOR CONSTRUCTION',12,8,2.2)
 pt(sheet,462,33,6);pt('REV R001  |  2026-11-27',462,21,2.6);pt(f'1:{scale} on A2 | metres',462,9,2.5)
 paper.add_viewport(center=(287,225),size=(554,320),view_center_point=center,view_height=view_height or 320*scale/1000)
 return doc,msp,paper

def text(msp,s,x,y,h=2.5,layer=TEXT,width=None):
 if width:return msp.add_mtext(s,dxfattribs={'char_height':h,'insert':(x,y),'width':width,'layer':layer})
 return msp.add_text(s,dxfattribs={'height':h,'insert':(x,y),'layer':layer})

def dim(doc,msp,sheet,name,p1,p2,base,angle,measurement_id=None,estimate=False):
 suffix=f' m [{measurement_id}]' if measurement_id else ' m [EST]'
 if measurement_id in ['M158','M159']:suffix=' m [APPROX HIST]'
 override=msp.add_linear_dim(base=base,p1=p1,p2=p2,angle=angle,dimstyle='REFERENCE_M',text='<>'+suffix,dxfattribs={'layer':DIM});override.render();entity=override.dimension
 entity.set_xdata('COLISEUM_REF',[(1000,name),(1000,measurement_id or 'ESTIMATE'),(1000,'REFERENCE_ONLY')])
 value=float(entity.get_measurement())
 register.append({'sheet':sheet,'dimension_id':name,'measurement_id':measurement_id or '', 'model_value_m':value,'source_value_m':sources.get(measurement_id,{}).get('si_value',''),'evidence':'estimated' if estimate else 'historic-approximate' if measurement_id in ['M158','M159'] else 'source-reported','source_url':sources.get(measurement_id,{}).get('source_url','')})

def ellipse(msp,rx,ry,layer,start=0,end=math.tau):return msp.add_ellipse((0,0),major_axis=(rx,0,0),ratio=ry/rx,start_param=start,end_param=end,dxfattribs={'layer':layer})
def rect(msp,x0,y0,x1,y1,layer):return msp.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],close=True,dxfattribs={'layer':layer})
def datum(msp,z,label,left=-175,right=175,label_x=None):
 msp.add_line((left,z),(right,z),dxfattribs={'layer':DATUM});text(msp,label,left+1 if label_x is None else label_x,z+1.5,2.1)
def save(doc,sheet):
 path=root/'drawings'/f'{sheet}.dxf';doc.saveas(path);audit=ezdxf.readfile(path).audit()
 if audit.has_errors:raise RuntimeError(f'DXF audit failed: {sheet}')
 drawing_reports.append({'sheet':sheet,'auditErrors':len(audit.errors),'auditFixes':len(audit.fixes),'nativeDimensions':len(doc.modelspace().query('DIMENSION')),'unitCode':doc.header['$INSUNITS']})
 return path

# A-101: plan coordinates are true project metres, with field centre at (0,0).
doc,msp,paper=new_doc('A-101','REFERENCE GENERAL ARRANGEMENT PLAN','X east / Y north | field-centred local grid | source and estimated geometry distinguished')
L,W=p['bowlLength'],p['bowlWidth'];ellipse(msp,L/2,W/2,HIST)
for i in range(4,p['visualRows']+1,4):
 t=i/p['visualRows'];rx=p['innerBowlLength']/2+(L/2-3.8-p['innerBowlLength']/2)*t;ry=p['innerBowlWidth']/2+(W/2-3.8-p['innerBowlWidth']/2)*t
 ranges=[(.48,math.tau-.48)] if t<=.36 else [(.48,math.tau-2.14),(math.tau-1,math.tau-.48)]
 for a,b in ranges:ellipse(msp,rx,ry,SEAT,a,b)
ellipse(msp,p['fieldLength']/2,p['fieldWidth']/2,EST);rect(msp,-p['footballLength']/2,-p['footballWidth']/2,p['footballLength']/2,p['footballWidth']/2,OUTLINE)
rect(msp,-p['towerLength']/2,-p['towerZ']-p['towerDepth']/2,p['towerLength']/2,-p['towerZ']+p['towerDepth']/2,EST)
text(msp,'SOUTH TOWER [EST]',-29,-86,3);text(msp,'Footprint / individual floor elevations unverified',-53,-92,2)
z=-p['peristyleSpan']/2;small=(p['peristyleSpan']-p['centralArchBay'])/14
for i in range(15):
 bay=p['centralArchBay'] if i==7 else small;cz=z+bay/2;z+=bay;cx=p['peristyleX']-.0028*cz*cz;rect(msp,cx-p['peristyleDepth']/2,-cz-bay/2,cx+p['peristyleDepth']/2,-cz+bay/2,EST)
msp.add_line((-178,0),(179,0),dxfattribs={'layer':DATUM});msp.add_line((0,-128),(0,126),dxfattribs={'layer':DATUM})
text(msp,'A',-177,3,4);text(msp,'A',174,3,4);text(msp,'B',3,122,4);text(msp,'B',3,-126,4);text(msp,'N',0,145,4)
msp.add_line((0,130),(0,141),dxfattribs={'layer':DATUM});msp.add_solid([(0,144),(-1.5,140),(1.5,140),(1.5,140)],dxfattribs={'layer':DATUM})
dim(doc,msp,'A-101','D001',(-L/2,0),(L/2,0),(0,133),0,'M158')
dim(doc,msp,'A-101','D002',(0,-W/2),(0,W/2),(-187,0),90,'M159')
dim(doc,msp,'A-101','D003',(-p['fieldLength']/2,0),(p['fieldLength']/2,0),(0,52),0,'M017')
dim(doc,msp,'A-101','D004',(0,-p['fieldWidth']/2),(0,p['fieldWidth']/2),(97,0),90,'M018')
dim(doc,msp,'A-101','D005',(-p['footballLength']/2,0),(p['footballLength']/2,0),(0,-33),0,'M020')
dim(doc,msp,'A-101','D006',(0,-p['footballWidth']/2),(0,p['footballWidth']/2),(-63,0),90,'M021')
text(msp,'PLAN NOTES\\PField ellipse is interpolated. The reported smaller width 67.6656 m [M019] has no known station.\\P20 contour bands shown for legibility; 80 model bands are an estimate, not an actual row inventory.\\PPeristyle has 15 arches [M016]; individual arch sizes are estimated.',190,105,2.4,width=82)
text(msp,'LEGEND\\PSolid: source-anchored extent\\PDashed: estimated outline\\PHistoric envelope: approximate\\PDimensions are references; no blanket construction tolerance applies.',190,-33,2.4,width=82)
text(msp,'A-A: see A-201 | B-B: see A-202. Not georeferenced. All dimensions in metres.',-150,-144,2.4)
paths=[save(doc,'A-101')]

# A-201: east-west section. East bowl is open at the peristyle in the adopted model.
doc,msp,paper=new_doc('A-201','LONGITUDINAL SECTION A-A','At project Y=0 | horizontal X east / vertical Z up | profile is inferred',750,center=(0,34),view_height=240)
rise=p['rimHeight']/p['visualRows'];profile=[(-L/2,p['rimHeight']),(-(L/2-3.8),p['rimHeight'])]
for i in range(p['visualRows']-1,-1,-1):
 x=-(p['innerBowlLength']/2+(L/2-3.8-p['innerBowlLength']/2)*i/p['visualRows']);profile.extend([(x,(i+1)*rise),(x,i*rise)])
msp.add_lwpolyline(profile,dxfattribs={'layer':EST});msp.add_line((-p['fieldLength']/2,0),(p['fieldLength']/2,0),dxfattribs={'layer':OUTLINE})
base=p['streetHeight'];x=p['peristyleX'];archtop=base+p['centralArchHeight'];ctop=base+p['cauldronAboveStreet']
rect(msp,x-p['peristyleDepth']/2,base,x+p['peristyleDepth']/2,archtop,EST);rect(msp,x-2,archtop,x+2,ctop-2,EST);rect(msp,x-3.4,ctop-2,x+3.4,ctop,EST)
datum(msp,0,'LOCAL FIELD REFERENCE +0.000 m',label_x=-70);datum(msp,base,'GENERIC STREET REFERENCE +12.4206 m [M011]',label_x=-70);datum(msp,p['rimHeight'],'LAST ROW +35.2552 m [M012]',label_x=-70)
dim(doc,msp,'A-201','D007',(-168,0),(-168,p['rimHeight']),(-187,0),90,'M012')
dim(doc,msp,'A-201','D008',(-125,0),(-125,base),(-112,0),90,'M011')
dim(doc,msp,'A-201','D009',(-145,base),(-145,p['rimHeight']),(-155,0),90,'M013')
dim(doc,msp,'A-201','D010',(x,base),(x,ctop),(162,0),90,'M015')
text(msp,'PERISTYLE / CAULDRON\\POverall cauldron reference height is source-reported. Arch profile, pedestal and top endpoint interpretation remain estimated.',-20,81,2.4,width=160)
text(msp,'SECTION NOTES\\PThe historic bowl length does not establish the current bowl profile.\\PStreet is a local reference convention, not a survey benchmark or a level-ground claim.\\PThe 2015/2016 design elevations are not used as field-relative as-built levels.',-165,-30,2.4,width=310)
paths.append(save(doc,'A-201'))

# A-202: north-south section, north at left; tower occupies upper south bowl.
doc,msp,paper=new_doc('A-202','TRANSVERSE SECTION B-B','At project X=0 | horizontal south positive / vertical Z up | estimated tower levels',500,center=(0,30),view_height=160)
for sign,limit in [(-1,p['visualRows']),(1,int(p['visualRows']*.36))]:
 points=[(sign*p['innerBowlWidth']/2,0)]
 for i in range(limit):
  a=p['innerBowlWidth']/2+(W/2-3.8-p['innerBowlWidth']/2)*i/p['visualRows'];b=p['innerBowlWidth']/2+(W/2-3.8-p['innerBowlWidth']/2)*(i+1)/p['visualRows'];points.extend([(sign*a,(i+1)*rise),(sign*b,(i+1)*rise)])
 msp.add_lwpolyline(points,dxfattribs={'layer':EST})
msp.add_line((-p['fieldWidth']/2,0),(p['fieldWidth']/2,0),dxfattribs={'layer':OUTLINE})
base=p['streetHeight'];top=base+p['towerAboveStreet'];x=p['towerZ'];rect(msp,x-p['towerDepth']/2,base,x+p['towerDepth']/2,top,EST)
for level in spec['towerLevels']:
 z=base+level['aboveStreet'];msp.add_line((x-p['towerDepth']/2,z),(x+p['towerDepth']/2,z),dxfattribs={'layer':EST});text(msp,level['id'].upper()+' ~'+f'{z:.2f}',x+p['towerDepth']/2+3,z+.5,1.9)
datum(msp,0,'FIELD +0.000',-125,125);datum(msp,base,'STREET +12.4206 [M011]',-125,125);datum(msp,p['rimHeight'],'LAST ROW +35.2552 [M012]',-125,125)
dim(doc,msp,'A-202','D011',(x,base),(x,top),(134,0),90,'M014')
text(msp,'NORTH',-108,-10,3);text(msp,'SOUTH',82,-10,3)
text(msp,'TOWER LEVEL NOTES\\PSeven level identities come from S01 floor plans D03-D08.\\PIndividual floor elevations and footprint dimensions are estimates [A004].\\POverall top is +45.7454 m = street +33.3248 m [M014].\\PDo not interpret the design-section elevations M170-M175 as these levels.',-120,81,2.4,width=250)
text(msp,'Reconstruction target +/-0.30 m is unverified. It is not a construction or fabrication tolerance.',-120,-28,2.2)
paths.append(save(doc,'A-202'))

with (root/'inputs/control-register.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(register[0]),lineterminator='\n');writer.writeheader();writer.writerows(register)
(root/'reports/dxf-validation.json').write_text(json.dumps({'drawings':drawing_reports,'dimensionCount':len(register),'units':'meters','physicalAccuracy':'unverified'},indent=2)+'\n')
# Render the actual paper layouts, including native DIMENSION blocks and viewports.
for path in paths:
 doc=ezdxf.readfile(path);fig=plt.figure(figsize=(594/25.4,420/25.4),dpi=100);ax=fig.add_axes([0,0,1,1]);ax.set_axis_off()
 ctx=RenderContext(doc);backend=MatplotlibBackend(ax);cfg=config.Configuration(background_policy=config.BackgroundPolicy.WHITE,color_policy=config.ColorPolicy.BLACK)
 Frontend(ctx,backend,config=cfg).draw_layout(doc.layouts.get(path.stem),finalize=True)
 # Frontend finalization may resize the Matplotlib figure. Restore the physical
 # A2 page so the paper-layout viewport scales remain meaningful when printed.
 fig.set_size_inches(594/25.4,420/25.4,forward=True);ax.set_position([0,0,1,1]);ax.set_aspect('equal',adjustable='box');ax.set_xlim(-10,584);ax.set_ylim(-10,410)
 fig.savefig(root/'drawings'/f'{path.stem}.pdf',dpi=150,facecolor='white',bbox_inches=None);fig.savefig(root/'reports'/f'{path.stem}.png',dpi=80,facecolor='white',bbox_inches=None);plt.close(fig)
# Cover explains the engineering status instead of implying a construction issue.
c=canvas.Canvas(str(root/'drawings/G-001.pdf'),pagesize=(594*mm,420*mm));c.setTitle('Coliseum reference drawings R001');c.setStrokeColor(HexColor('#253d49'));c.rect(10*mm,10*mm,574*mm,400*mm)
def cover(text,x,y,size=12):c.setFont('Helvetica',size);c.drawString(x*mm,y*mm,text)
cover('LOS ANGELES MEMORIAL COLISEUM',24,380,26);cover('Engineering reference package | R001 | 2026-11-27',24,365,17)
lines=[
 'PURPOSE: dimension-controlled reconstruction reference derived from public research; not an as-built survey.',
 'Units: metres. CAD / IFC axes: X east, Y north, Z up. Local field reference Z=0. No geographic survey control.',
 'Native FreeCAD storage uses millimetres with a documented 1000:1 conversion. DXF geometry is 1 unit = 1 metre.',
 'A-101: general arrangement plan, 1:1000 on A2. A-201: longitudinal section, 1:750. A-202: transverse section, 1:500.',
 'Native DXF dimension entities derive values from geometry. Source references are retained in dimension XDATA.',
 'Source-reported dimensions are transcribed references, not independent measurements or certified accuracy.',
 'Historic bowl envelope M158/M159 is approximate and predates later changes; it is provisional for this model.',
 'Bowl profiles, 80 visual bands, tower footprint and floor heights, peristyle details and field outline are estimates.',
 'MVP-only exterior paths and schematic stair connections are excluded from the engineering reference model.',
 'Reconstruction target: +/-0.30 m at agreed physical reference features. This target has NOT been verified.',
 'This is not a blanket construction tolerance. Dimensional decimal precision does not establish physical accuracy.',
 'Standards guide: NCS/UDS for drawing conventions; ISO 129-1 for dimension presentation; ISO 6284 for limit deviations.',
 'Material construction tolerances are discipline-specific, e.g. ACI 117 and AISC 303; no such tolerances are specified here.',
 'The package uses project drawing conventions; full compliance with purchased standards has not been audited.',
 'IFC4 opens in Bonsai for Blender and IFC-capable FreeCAD workflows. FCStd is the native FreeCAD document.',
 'GLB is tessellated from the reopened FreeCAD solids at nominal 0.05 m deflection; it is a lightweight reference view.',
 'Primary evidence: S01 Draft Technical Guide 2024; S04 NPS historic nomination. See source and control registers.',
 'Use the generator scripts to update and reproduce the files. Revision R001 is a reference-only issue.'
]
for i,line in enumerate(lines):cover(line,24,337-i*13,12)
cover('INDEPENDENT REFERENCE RECONSTRUCTION | NOT FOR CONSTRUCTION',24,35,16);c.showPage();c.save()
try:
 from pypdf import PdfWriter
 writer=PdfWriter()
 for file in ['G-001.pdf','A-101.pdf','A-201.pdf','A-202.pdf']:writer.append(str(root/'drawings'/file))
 with (root/'drawings/coliseum-reference-drawings-R001.pdf').open('wb')as f:writer.write(f)
except ImportError:
 import fitz
 result=fitz.open()
 for file in ['G-001.pdf','A-101.pdf','A-201.pdf','A-202.pdf']:
  source=fitz.open(root/'drawings'/file);result.insert_pdf(source);source.close()
 result.save(root/'drawings/coliseum-reference-drawings-R001.pdf');result.close()
print(json.dumps({'dxfFiles':len(paths),'nativeDimensions':len(register),'pdfSheets':4}))
