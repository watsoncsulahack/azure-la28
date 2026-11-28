"""Rebuild parameter provenance and source transcription checks without changing geometry."""
import csv
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
spec=json.loads((REPO/'apps/coliseum-mvp/dist/data/venue.json').read_text())
measurements={r['measurement_id']:r for r in csv.DictReader((REPO/'research/coliseum-dimensions/dimensions.csv').open())}


def write_csv(name,rows):
    with (OUT/name).open('w',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)


component_parameters={
 'field':['fieldLength','fieldWidth','footballLength','footballWidth'],
 'bowl':['bowlLength','bowlWidth','innerBowlLength','innerBowlWidth','rimHeight','visualRows','peristyleOpeningHalfAngle'],
 'seats':['visualRows','visualSeatSpacing'],
 'circulation':['streetHeight','rimHeight','innerBowlLength','innerBowlWidth','bowlLength','bowlWidth'],
 'tower':['towerLength','towerDepth','towerZ','towerAboveStreet','streetHeight'],
 'peristyle':['peristyleSpan','centralArchBay','centralArchHeight','smallArchHeight','archPierWidth','archCrownThickness','peristyleDepth','peristyleX','cauldronAboveStreet','streetHeight'],
 'context':['bowlLength','bowlWidth','rimHeight','streetHeight'],
 'displays':['westScreenWidth','westScreenHeight']}
rows=[]
for key,value in spec['parameters'].items():
    ev=spec['parameterEvidence'][key];mid=ev.get('measurementId','');source=measurements.get(mid,{})
    historic=source.get('configuration_status')=='historic'
    rows.append({'parameter':key,'value':value,
        'units':'count'if key=='visualRows'else('radians'if key=='peristyleOpeningHalfAngle'else'm'),
        'components':';'.join(k for k,v in component_parameters.items()if key in v),
        'measurement_id':mid,'source_id':source.get('source_id',''),
        'original_measurement':source.get('original_measurement',''),
        'expected_si':source.get('si_value',''),'source_url':source.get('source_url',''),
        'pdf_page':source.get('pdf_page',''),'printed_page':source.get('printed_page',''),
        'epoch_or_configuration':source.get('configuration_status','MVP engineering estimate'),
        'evidence_class':('historically_approximate'if historic else'source_reported')if mid else'engineering_estimate',
        'transcription_status':'CHECKED_NUMERIC_CONVERSION'if mid else'NOT_APPLICABLE',
        'independent_physical_status':'NOT_VALIDATED','source_uncertainty_m':'unknown; no feature-specific uncertainty supplied',
        'physical_acceptance_tolerance_m':'not selected/approved',
        'scope':source.get('datum_or_scope','')or ev.get('notes',''),
        'boundary_limitations':source.get('notes','')})
for level in spec['towerLevels']:
    rows.append({**dict.fromkeys(rows[0],''),'parameter':level['id']+'.aboveStreet','value':level['aboveStreet'],
        'units':'m','components':'tower','evidence_class':'engineering_estimate','independent_physical_status':'NOT_VALIDATED',
        'physical_acceptance_tolerance_m':'not selected/approved','scope':'Floor identity from guide plans; relative elevation is estimated, not the undatumed 2015 design elevation.'})
write_csv('parameter-traceability.csv',rows)

# Re-enter original ft/in controls, rather than testing the source register against itself.
controls=[('bowlLength','M158',1038,0),('bowlWidth','M159',738,0),
 ('streetHeight','M011',40,9),('rimHeight','M012',115,8),
 ('derivedStreetToLastRow','M013',74,11),('towerAboveStreet','M014',109,4),
 ('cauldronAboveStreet','M015',123,6),('fieldLength','M017',560,0),
 ('fieldWidth','M018',250,0),('footballLength','M020',360,0),('footballWidth','M021',160,0),
 ('westScreenWidth','M072',150,3),('westScreenHeight','M073',39,11)]
checks=[]
for key,mid,ft,inch in controls:
    expected=(ft+inch/12)*.3048
    actual=spec['parameters'][key]if key in spec['parameters']else spec['parameters']['rimHeight']-spec['parameters']['streetHeight']
    checks.append({'parameter':key,'measurement_id':mid,'original_ft':ft,'original_in':inch,
        'reference_m':expected,'input_m':actual,'residual_m':actual-expected,
        'conversion_check_tolerance_m':.00005,'status':'TRANSCRIPTION_MATCH'if abs(actual-expected)<.00005 else'FAIL',
        'physical_acceptance':False,'source_url':measurements[mid]['source_url']})
assert all(c['status']=='TRANSCRIPTION_MATCH'for c in checks)
sources=list(csv.DictReader((REPO/'research/coliseum-dimensions/sources.csv').open()))
hash_checks=[]
for sid,name in [('S01','guide2024.pdf'),('S04','nps1984.pdf')]:
    path=REPO/'research/coliseum-geospatial/evidence/raw'/name
    expected=next(s['sha256']for s in sources if s['source_id']==sid)
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    hash_checks.append({'source_id':sid,'original_register_sha256':expected,'new_download_sha256':actual,'identical':actual==expected})
report={'source_transcription_checks':checks,'passing':sum(c['status']=='TRANSCRIPTION_MATCH'for c in checks),
  'total':len(checks),'source_document_hash_checks':hash_checks,
  'method':'Source PDF text rechecked (S01 PDF pp8,21,43; S04 PDF p2), original ft/in controls converted independently; input comparison is transcription only.',
  'traceability':{'parameter_rows':len(rows),'all_spec_parameters_covered':set(spec['parameters'])<=set(r['parameter']for r in rows),
    'measured_independently_in_input_register':0},
  'unrepresented_controls':[{'measurement_id':mid,**measurements[mid]}for mid in ['M002','M019','M170','M171','M172','M173','M174','M175']],
  'input_geometry_changed':False}
(OUT/'transcription-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'transcription_matches':len(checks),'parameter_rows':len(rows),'source_hashes':hash_checks},indent=2))
