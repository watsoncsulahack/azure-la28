"""Build the research catalog from manually reviewed source transcriptions.

No geometry is inferred here. Source labels, dates and unresolved scopes are
retained. Run from any directory with Python 3; no third-party packages needed.
"""
import csv
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
SOURCES = [
    ('S01', 'Coliseum Technical Guide — Draft 2024', 'Los Angeles Memorial Coliseum', '2024 (draft)', 'operational-reference', 'official-technical-guide-2024.pdf', 'https://lacoliseum.com/wp-content/uploads/2024/12/Coliseum_Technical_Guide_Draft2024.pdf', '65 pages. Principal post-2019 reference; not a certified as-built survey.'),
    ('S02', 'Promoter Guide, Rev 5.8 (12122020)', 'Los Angeles Memorial Coliseum', '2020-12-12', 'operational-reference-older', 'official-promoter-2020.pdf', 'https://lacoliseum.com/wp-content/uploads/2018/03/Promoter_Guide_5-6_r.pdf', '45 pages. Page 37 contains an undated dimensioned drawing; publication date does not establish drawing date.'),
    ('S03', 'Project Restart Master Plan — Commencement Ceremonies', 'Los Angeles Memorial Coliseum', '2021-05-12', 'operational-reference-older', 'official-restart-2021.pdf', 'https://lacoliseum.com/wp-content/uploads/2018/03/LA-Coliseum-Project-Restart-Master-Plan-Commencement-Ceremonies-05122021.pdf', '37 pages. Appendix 5 supplies room/suite areas; COVID occupancy limits are not geometry.'),
    ('S04', 'National Historic Landmark nomination, 84003866', 'National Park Service', '1984', 'historic', 'nps-landmark-nomination.pdf', 'https://npgallery.nps.gov/NRHP/GetAsset/NHLS/84003866_text', '24 pages. Predates the 1993 field lowering and the 2019 tower.'),
    ('S05', 'University of Southern California Memorial Coliseum', 'DLR Group (renovation architect)', 'Undated; describes August 2019 completion', 'completed-project-description', 'dlr-coliseum.html', 'https://www.dlrgroup.com/work/university-of-southern-california-los-angeles-memorial-coliseum/', 'Explains retained perimeter/bowl and seven-story addition. Renovation area is not footprint.'),
    ('S06', 'United Airlines Field at Los Angeles Memorial Coliseum', 'USC Athletics', 'Undated; retrospective history', 'renovation-history', 'official-usc-facility.html', 'https://usctrojans.com/facilities/united-airlines-field-at-los-angeles-memorial-coliseum/2', 'Reports 1993 field lowering and 14 additional rows.'),
    ('S07', 'Coliseum Commission regular meeting agenda packet', 'Los Angeles Memorial Coliseum Commission', '2016-04-28', 'proposal-and-preservation-record', 'commission-2016-april.pdf', 'https://assets-us-01.kc-usercontent.com/0234f496-d2b7-00b6-17a4-b43e949b70a2/e4d96d5a-0dce-4149-a7b4-2455464bb2bf/160428%20Regular%20Meeting%20Agenda%20Packet.pdf', '134 pages. Includes revised project descriptions and historic-recordation conditions, not proof of completed HABS records.'),
    ('S08', 'Coliseum Commission special meeting agenda packet', 'Los Angeles Memorial Coliseum Commission', '2016-12-08', 'design-record', 'commission-2016-december.pdf', 'https://assets-us-01.kc-usercontent.com/0234f496-d2b7-00b6-17a4-b43e949b70a2/23bd91e4-d48e-4280-a79b-0c2338f518db/Agenda%20Packet-SpecialMeeting%2012.08.16.pdf', '41 pages. Page 32 / B-4 is a dimensioned bowl section at a video board with proposed tower-level reference lines; not a tower section or as-built survey.'),
    ('S09', 'The Huntington acquires the archive of John and Donald Parkinson', 'The Huntington', '2022-07-12', 'archive-location-lead', 'huntington-archive.html', 'https://www.huntington.org/watch-read-listen/news/news-release-huntington-acquires-archive-leading-early-20th-century-la', 'Confirms archive acquisition and Coliseum coverage; individual sheet inventory, current processing status and online availability not established.'),
    ('S10', 'Los Angeles Memorial Coliseum renovation case study', 'California Masonry Council / DLR Group project team', 'Undated; URL uploaded 2024-12', 'completed-project-description', 'masonry-case-study.pdf', 'https://californiamasonrycouncil.org/wp-content/uploads/2024/12/Los-Angeles-Memorial-Coliseum.pdf', '10 pages. Photos and material/design narrative; no complete measured drawing set located.'),
    ('S11', 'Los Angeles Memorial Coliseum Renovation, SCH 1990011065/7', 'California State Clearinghouse / CEQAnet', '2016', 'proposal-index', 'ceqa-2016.html', 'https://ceqanet.lci.ca.gov/1990011065/7', 'Official project description; use to locate the Second Addendum, not as as-built geometry.'),
]
SOURCE_MAP = {s[0]: s for s in SOURCES}
ROWS = []


def add(component, quantity, value, unit, source, page='', printed='', status=None,
        evidence='stated-text', notes='', original=None, datum=''):
    factor = {'ft': .3048, 'ft2': .09290304, 'm': 1, 'm2': 1}.get(unit)
    si_unit = {'ft': 'm', 'ft2': 'm2', 'm': 'm', 'm2': 'm2'}.get(unit, '')
    ROWS.append(dict(
        measurement_id=f'M{len(ROWS)+1:03}', component=component, quantity=quantity,
        original_measurement=original or f'{value:g} {unit}', value=value, unit=unit,
        si_value=round(value*factor, 6) if factor else '', si_unit=si_unit,
        source_id=source, pdf_page=page, printed_page=printed,
        configuration_status=status or SOURCE_MAP[source][4],
        evidence_type=evidence, datum_or_scope=datum, notes=notes,
        source_url=SOURCE_MAP[source][6] + (f'#page={page}' if page else ''),
    ))


def feet(ft, inches=0):
    return ft + inches/12


# Principal measurements: 2024 guide, PDF page 8 / printed page 6.
for component, val, note in [
    ('Coliseum reported area', 784080, 'Also reported as 18 acres. Boundary and area convention are not defined; not established as building footprint.'),
    ('Playing field reported area', 135837, 'Event/field area label; do not assume this equals the football rectangle or the older page-37 area polygons.'),
    ('Field court (cement)', 12800, 'Separate field-court area.'),
    ('Peristyle Deck', 11000, 'Reported event-space area; not enough to establish its shape.'),
    ('Peristyle Plaza', 28850, 'Reported event-space area.'),
    ('Olympic Plaza South', 16100, 'Reported event-space area.'),
    ('Olympic Plaza Center', 17600, 'Reported event-space area.'),
    ('Olympic Plaza North', 18400, 'Reported event-space area.'),
]: add(component, 'area', val, 'ft2', 'S01', 8, 6, notes=note)
for component, quantity, ft, inch, datum in [
    ('Field court (cement)', 'length',160,0,'Field court, not the football playing rectangle'),
    ('Field court (cement)', 'width',80,0,'Field court, not the football playing rectangle'),
    ('Street level above field', 'vertical separation',40,9,'Field to street; generic street datum in guide, no surveyed benchmark'),
    ('Last seating row above field', 'vertical separation',115,8,'Field to last seating row'),
    ('Last seating row above street', 'vertical separation',74,11,'Street to last seating row'),
    ('Scholarship Club Tower above street', 'height',109,4,'Street to tower height; exact roof/parapet endpoint not defined'),
    ('Olympic Cauldron above street', 'height',123,6,'Street to cauldron; endpoint differs or conflicts with older historic torch description'),
]: add(component,quantity,feet(ft,inch),'ft','S01',8,6,original=f'{ft} ft {inch} in',datum=datum)
add('Peristyle', 'arch count', 15, 'count', 'S01',8,6,notes='Historic description identifies one central arch plus seven smaller arches on each side.')
for component,quantity,val,notes in [
    ('Field envelope', 'east-west extent',560,'Guide states East to West; endpoints not dimensioned on this page.'),
    ('Field envelope', 'north-south width, larger reported value',250,'Source presents 250 ft – 222 ft; station locations are not supplied.'),
    ('Field envelope', 'north-south width, smaller reported value',222,'Retain as a range; not a constant rectangle width.'),
    ('Maximum football configuration','length',360,'Includes the full football layout; distinct from complete field envelope.'),
    ('Maximum football configuration','width',160,''),
    ('Maximum rugby configuration','length',350,'Page 8 gives 60 m x 107 m rounded, while page 21 gives 350 ft x 196 ft; preserve convention.'),
    ('Maximum rugby configuration','width',196,''),
    ('Maximum soccer configuration','length',330,''),
    ('Maximum soccer configuration','width',210,''),
]: add(component,quantity,val,'ft','S01',21,19,notes=notes)
for component,length,width in [('Coliseum Boardroom',34,22),('North Office 1A',34,20),('North Office 1B',24,22),('Game Management Trailer',30,60)]:
    add(component,'length',length,'ft','S01',11,9)
    add(component,'width',width,'ft','S01',11,9)
for component,area,notes in [
    ('Coliseum Boardroom',748,''),('North Office 1A',680,''),('North Office 1B',528,''),
    ('North Office 2',823,'Two component sizes listed as 20 x 15 ft and 33 x 16 ft imply 828 ft2, not 823 ft2; reconcile before scaling.'),
    ('Game Management Trailer',1800,''),('Meeting Room Level 2',399,''),
    ('Conference Room Level 5',593,''),('Heritage Concourse',19000,'Rounded event-space area; older guide gives 18,962 ft2.'),
]: add(component,'area',area,'ft2','S01',11,9,notes=notes)
for ref,name,area in [('G105','Home Locker Room',1950),('G105A','Home Locker split A',1392),('G105B','Home Locker split B',1146),('G112','Away Locker Room',1149),('G112A','Away Locker split A',546),('G112B','Away Locker split B',603),('G101','Home Equipment',414),('G106','Auxiliary Lockers',99),('G108','Home Trainers',532),('G111','Away Trainers',321),('G113','Away Equipment',201),('G114','Away Strategy/Media',746),('G116','Auxiliary Lockers',185),('G117','Auxiliary Lockers',152)]:
    add(f'{ref} {name}','area',area,'ft2','S01',10,8,notes='G105 splits total 2,538 ft2, exceeding listed parent 1,950 ft2; do not treat these as an additive partition.' if ref.startswith('G105') else '')
for ref,name,area in [('602','Security',678),('604','Instant Replay',121),('606','Medical Replay',122),('608','Skycam/Aux Radio',142),('610','National Radio',160),('612A','Game Ops/Clock',285),('618','Visitor AD',352),('620','Control Room',617),('622','Visitor Radio',194),('624A','Athletics/Aux',481),('626','Home Radio',161),('628','Home Coach',301),('630','Network TV',376),('632','Team Video',223),('634','Visitor Coach',295)]:
    add(f'Level 6 room {ref} {name}','area',area,'ft2','S01',18,16,notes='Some rooms can be joined or split; area alone does not locate walls.')
add('Reversible escalators','nominal width',4,'ft','S01',32,30,original='48 inches',notes='Source does not identify whether this is tread width or equipment width; not verified clear accessible-route width.')
for name,w,h in [('West video board',(150,3),(39,11)),('NE/SE video board, each',(99,7),(26,4)),('Peristyle display',(25,2),(12,0)),('Field-level display, each',(28,9),(3,7)),('Endzone board, each',(163,2),(3,7)),('Tunnel display',(44,5),(4,9))]:
    for q,(ft,inch) in [('width',w),('height',h)]:add(name,q,feet(ft,inch),'ft','S01',43,41,original=f'{ft} ft {inch} in',notes='Display face only; not support structure dimensions.')
for name,val in [('Press box ribbon Level 2',373.2),('Press box ribbon Level 3',406.8)]:
    add(name,'display width',val,'ft','S01',43,41,notes='Display face length, not proven straight-line tower width.')
    add(name,'display height',3.5,'ft','S01',43,41,original='3 ft 6 in')

# Older official guide: preserve drawing ambiguity rather than assigning invented stations.
for label,ft,inch in [('Transverse span A',193,5),('Transverse span B',234,0),('Transverse span C',248,2),('Transverse span D',262,3),('Transverse span E',265,7),('Transverse span F',261,4),('Transverse span G',250,7),('Longitudinal span A',504,6),('Longitudinal span B',418,5),('Longitudinal span C',414,1),('Field-court span A',160,2),('Field-court span B',80,1),('Side clearance annotation',13,6),('Diagonal annotation',44,8)]:
    add(f'Older field drawing — {label}','annotated span',feet(ft,inch),'ft','S02',37,37,
        status='older-drawing-date-unconfirmed', evidence='dimensioned-drawing', original=f'{ft} ft {inch} in',
        datum='Drawing annotation; match its line endpoints visually on source page 37',
        notes='A–G transverse order is top-to-bottom with dimension labels upright (page rotated 180 degrees). These are not surveyed coordinates. Do not merge with 2024 envelope without registering and reconciling boundaries.')
for name,area in [('Central rectangle',63984),('Side polygon A',8950),('Side polygon B',9232),('End polygon A',4500),('End polygon B',7724)]:
    add('Older field drawing — '+name,'annotated area',area,'ft2','S02',37,37,status='older-drawing-date-unconfirmed',evidence='dimensioned-drawing',notes='Polygon annotation only; no equivalence established to 2024 playing-field area.')
for component,area,page in [('Founders Level 2 event space',11000,39),('Founders Level 3 event space',7628,40),('Club Level event space',9390,41),('Club Level west deck',770,41),('Club Level east deck',870,41),('Suite Level event space',2085,42),('1923 Club event space',11714,43),('Heritage Concourse event space',18962,44)]:
    add(component,'area',area,'ft2','S02',page,page,notes='Event-space area label, not entire gross floor plate. In particular, 2,085 ft2 must not be used as the whole suite floor.')

# Suite areas, not occupancy figures, transcribed from the 2021 plan's Appendix 5.
founders = {201:3601,205:666,206:697,207:697,208:666,209:686,210:694,211:694,212:1505,301:1478,302:694,303:688,304:679,305:672,306:685,307:685,308:674,309:687,310:694,311:694,312:1513}
suites = {501:1589,502:500,503:362,504:380,505:380,506:363,507:372,508:390,509:379,510:341,511:363,512:362,513:363,514:355,515:380,516:362,517:361,518:378,519:378,520:361,521:563,522:1859}
for suite,area in founders.items():
    add(f'Founders suite {suite}','reported area',area,'ft2','S03',22,21,notes='Scope of included deck/support space not defined; do not sum as net interior or gross floor area.')
for suite,area in suites.items():
    page=23 if suite<=514 else 24
    add(f'Level 5 suite {suite}','reported area',area,'ft2','S03',page,page-1,notes='Scope of included deck/support space not defined; not a width/depth measurement.')
# Loge-area entries omitted: merged cells in the source make individual assignment uncertain.

# Historic geometry: useful baseline, explicitly not the current field configuration.
for component,q,val,notes in [
    ('Historic bowl ellipse','approximate length',1038,'NPS says about; the modern outer shell may be similar, but current extent is not surveyed here.'),
    ('Historic bowl ellipse','approximate midpoint width',738,'A true ellipse is only a baseline: the eastern peristyle and south tower require separate geometry.'),
    ('Historic rim above field','height',106,'Historic field datum, not current field elevation.'),
    ('Historic field','length',684,'Predates 1993 lowering and removal of running track.'),
    ('Historic field','width',345,'Not the 2024 field envelope.'),
    ('Historic field below grade','depth',32,'Not current guide depth of 40 ft 9 in.'),
    ('Historic middle seating berm above concourse','approximate height',27,'Approximate construction description, not current floor elevation.'),
    ('Historic Olympic torch above street','height',107,'NPS endpoint/datum differs or conflicts with 2024 cauldron height of 123 ft 6 in; unresolved.'),
]: add(component,q,val,'ft','S04',2,'Description / item 7',notes=notes)
add('Historic seating bowl','row count',79,'count','S04',2,'Description / item 7',notes='Historic three banks of 25, 29 and 25; not the current row inventory.')
add('1993 field lowering','change in elevation',11,'ft','S06',notes='Historical intervention, not a current measured depth below grade.')
add('1993 added seating','new rows',14,'count','S06',notes='Do not add mechanically to a historic row count to infer current seating geometry.')
add('1993 sideline separation','reported upper bound',54,'ft','S06',notes='First rows between goalposts reported no more than 54 ft from sideline, replacing prior 120 ft; not a uniform all-around clearance.')

# Design-record section: the absolute datum is not defined on the sheet.
for name,ft,inch in [('Level One — Yard',39,6),('Level Two — Founders 1',51,6),('Level Three — Founders 2',63,6),('Level Four — Club',75,6),('Level Five — Suite',101,6),('Level Six — Press',115,6)]:
    add(name,'labeled design elevation',feet(ft,inch),'ft','S08',32,'B-4 / embedded sheet 41',status='2015-design-approved-2016-not-as-built',evidence='dimensioned-drawing',original=f'{ft} ft {inch} in',datum='Sheet elevation datum not established; NOT verified height above field or sea level',notes='Drawing dated 08/18/15; marked Approved July 28, 2016. Horizontal lines reference proposed tower levels on a bowl/video-board section, not a cut through the tower.')
add('Proposed seating tread','depth',2.75,'ft','S08',30,'B-2 / embedded sheet 23',status='2015-design-approved-2016-not-as-built',original='33 inches',notes='Proposed bowl modifications; cannot establish every existing tread or stair riser.')


def write_csv(name, rows, fields=None):
    with (ROOT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


prior_sources = {}
if (ROOT/'sources.csv').exists():
    with (ROOT/'sources.csv').open(newline='') as f:
        prior_sources = {row['source_id']: row for row in csv.DictReader(f)}
source_rows=[]
for sid,title,publisher,date,status,filename,url,notes in SOURCES:
    path=ROOT/'raw'/filename
    prior = prior_sources.get(sid, {})
    source_rows.append(dict(source_id=sid,title=title,publisher=publisher,document_date=date,
        configuration_status=status,url=url,local_reference=f'raw/{filename}',
        downloaded_bytes=path.stat().st_size if path.exists() else prior.get('downloaded_bytes', ''),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else prior.get('sha256', ''),
        reviewed_on='2026-11-27',notes=notes))
write_csv('sources.csv',source_rows)
write_csv('dimensions.csv',ROWS)

DRAWINGS=[]
for source,page,label,coverage,kind,limitation in [
    ('S01',5,'3','Site plan: stadium, tower, surrounding gates and park context','site-plan','Embedded raster; draft download instruction has no usable link annotation.'),
    ('S01',9,'7','Locker rooms and associated facilities','floor-plan','Room outlines; not a fully dimensioned architectural sheet.'),
    ('S01',11,'9','Heritage Concourse / tower Level 1','floor-plan','No complete wall-dimension chains or physical floor elevations.'),
    ('S01',13,'11','Founders Levels 2 and 3 (two plans)','floor-plans','Same page contains two different levels; register separately.'),
    ('S01',15,'13','Club Level 4 / loge / upper-concourse connections','floor-plan','Room IDs, stairs and elevators visible; verify topology before routing.'),
    ('S01',17,'15','Suite Level 5','floor-plan','Room/suite outlines and circulation; no complete dimensions.'),
    ('S01',19,'17','Press Level 6','floor-plan','Includes operational access descriptions; not a clearance survey.'),
    ('S01',20,'18','Rooftop / 1923 Club Level 7','floor-plan','Not proof that every outdoor/roof segment is public.'),
    ('S02',37,'37','Field court, field perimeter, cross-widths and polygon areas','dimensioned-plan','Underlying drawing undated; numeric differences from 2024 guide unresolved.'),
    ('S02',39,'39','Founders Level 2, lounge, photos and small tower section locator','presentation-plan','Section locator is schematic, not a measured construction section.'),
    ('S02',40,'40','Founders Level 3','presentation-plan','Area labels refer to event spaces.'),
    ('S02',41,'41','Club Level 4, loge and decks','presentation-plan','Use with more detailed 2024 plan.'),
    ('S02',42,'42','Suite Level 5 and lounge','presentation-plan','2,085 ft2 event-space label is not whole floor area.'),
    ('S02',43,'43','1923 Club / rooftop','presentation-plan','No physical elevations.'),
    ('S02',44,'44','Heritage Concourse','presentation-plan','Event-space perimeter not surveyed building footprint.'),
    ('S02',45,'45','Press Level 6','presentation-plan','Room labels may reflect earlier operational assignments.'),
    ('S08',30,'B-2 / sheet 23','Proposed seating bowl modifications and 33-inch tread','design-diagram','Design dated 2015; approved stamp 2016; not as-built.'),
    ('S08',32,'B-4 / sheet 41','Bowl section at video board, proposed tower-level reference lines','dimensioned-section','NOT a section through tower. Sheet datum not defined; no field/sea-level assumption.'),
    ('S08',29,'B-1 / sheet 7','Proposed south-tower perspective','design-perspective','Visual design reference, not a measured elevation.'),
]:
    DRAWINGS.append(dict(drawing_id=f'D{len(DRAWINGS)+1:02}',source_id=source,pdf_page=page,
        printed_label=label,coverage=coverage,drawing_type=kind,limitations=limitation,
        url=SOURCE_MAP[source][6]+f'#page={page}'))
write_csv('drawing-index.csv',DRAWINGS)

# Self-contained, searchable reference. No dependencies, remote scripts or raw source files.
data=json.dumps({'measurements':ROWS,'sources':source_rows,'drawings':DRAWINGS}).replace('</','<\\/')
template='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LA Memorial Coliseum — dimensions reference</title><style>
body{font:16px system-ui;margin:0;background:#f4f5f7;color:#19212b}main{max-width:1400px;margin:auto;padding:28px}h1{margin-bottom:8px}p{max-width:1000px;line-height:1.6}input,select{font:inherit;padding:10px;margin:5px 10px 5px 0;max-width:100%}input{width:330px}.tools{position:sticky;top:0;background:#f4f5f7;padding:8px 0;z-index:1}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;background:white;font-size:14px}td,th{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #ddd}th{background:#dce4ec}td small{display:block;color:#52606d;margin-top:6px}a{color:#1851a1}details{background:white;margin:16px 0;padding:15px}.count{font-weight:600}code{font-size:13px}
</style><main><h1>Los Angeles Memorial Coliseum: dimensions reference</h1>
<p>Documented measurements and drawing references reviewed November 27, 2026. The 2024 guide is a draft operational reference. Historic, older and design-only measurements retain their own status. This is a research catalog, not a survey or a reconstructed model.</p>
<p>Lengths convert using exactly 1 foot = 0.3048 metre. Displayed decimals do not imply survey accuracy. Areas constrain size; they do not establish wall positions. <a href="README.md">Read findings and unresolved conflicts</a>.</p>
<div class="tools"><label>Find <input id="query" placeholder="field, tower, suite 501, height…"></label><label>Source <select id="source"><option value="">All sources</option></select></label><label>Status <select id="status"><option value="">All configurations</option></select></label><label>Units <select id="units"><option value="original">Source units</option><option value="si">Metric conversion</option></select></label><p id="count" class="count"></p></div>
<div class="scroll"><table><thead><tr><th>ID / component</th><th>Measurement</th><th>Source</th><th>Configuration and interpretation</th></tr></thead><tbody id="rows"></tbody></table></div>
<details><summary>Drawing index</summary><div id="drawings"></div></details><details><summary>Source documents and archive lead</summary><div id="sources"></div></details>
</main><script>const DATA=__DATA__;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const el=id=>document.getElementById(id);
for(const s of DATA.sources){let o=document.createElement('option');o.value=s.source_id;o.textContent=s.source_id+' — '+s.title;el('source').append(o)}
for(const s of [...new Set(DATA.measurements.map(r=>r.configuration_status))]){let o=document.createElement('option');o.value=s;o.textContent=s;el('status').append(o)}
function render(){const q=el('query').value.toLowerCase();const rows=DATA.measurements.filter(r=>(!el('source').value||r.source_id===el('source').value)&&(!el('status').value||r.configuration_status===el('status').value)&&JSON.stringify(r).toLowerCase().includes(q));el('count').textContent=rows.length+' of '+DATA.measurements.length+' measurement records';el('rows').innerHTML=rows.map(r=>{const metric=el('units').value==='si'&&r.si_unit;const v=metric?Number(r.si_value).toLocaleString(undefined,{maximumFractionDigits:3})+' '+r.si_unit:r.original_measurement;return '<tr><td>'+esc(r.measurement_id)+'<br><b>'+esc(r.component)+'</b></td><td>'+esc(r.quantity)+'<br><b>'+esc(v)+'</b>'+(metric?'<small>Source: '+esc(r.original_measurement)+'</small>':'')+'</td><td><a target="_blank" rel="noreferrer" href="'+esc(r.source_url)+'">'+esc(r.source_id)+(r.pdf_page?' · PDF p. '+r.pdf_page:'')+'</a><small>'+esc(r.evidence_type)+'</small></td><td>'+esc(r.configuration_status)+'<small>'+esc(r.datum_or_scope)+'</small><small>'+esc(r.notes)+'</small></td></tr>'}).join('')}
for(const id of ['query','source','status','units'])el(id).addEventListener('input',render);
el('drawings').innerHTML=DATA.drawings.map(d=>'<p><a target="_blank" rel="noreferrer" href="'+esc(d.url)+'">'+esc(d.drawing_id)+' · '+esc(d.source_id)+' PDF p. '+d.pdf_page+'</a> — '+esc(d.coverage)+'<br><small>'+esc(d.limitations)+'</small></p>').join('');
el('sources').innerHTML=DATA.sources.map(s=>'<p><a target="_blank" rel="noreferrer" href="'+esc(s.url)+'">'+esc(s.source_id)+' — '+esc(s.title)+'</a><br>'+esc(s.publisher)+' · '+esc(s.document_date)+'<br><small>'+esc(s.notes)+'</small></p>').join('');render();</script></html>'''
(ROOT/'dimension-explorer.html').write_text(template.replace('__DATA__',data))

with zipfile.ZipFile(ROOT/'coliseum-dimensions-research.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in ['README.md','dimensions.csv','sources.csv','drawing-index.csv','dimension-explorer.html','build_catalog.py']:
        if (ROOT/name).exists():z.write(ROOT/name,arcname='coliseum-dimensions/'+name)
print(f'Built {len(ROWS)} measurements, {len(SOURCES)} sources, {len(DRAWINGS)} drawing references.')
