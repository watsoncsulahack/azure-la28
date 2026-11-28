"""Finalize the executed acquisition/analysis record and verify preserved source bytes."""
from collections import Counter
from datetime import datetime,timezone
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import acquire

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
AUDIT=REPO/'analysis/coliseum-model/evidence-iteration'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()


def main():
    acquire.inventory()
    inv=json.loads((ROOT/'source-inventory.json').read_text())
    for row in inv['files']:
        path=ROOT/row['path']
        assert path.stat().st_size==row['bytes']
        assert sha(path)==row['sha256'],path
    selection=json.loads((ROOT/'reports/lidar-selection.json').read_text())
    cached={Path(r['path']).stem for r in inv['files']if r['path'].startswith('raw/ept-data/')}
    assert cached==set(selection['nodes']), 'Incomplete source-node inventory'
    # Independently check PR #1 extracts against every original municipal feature.
    municipal=[]
    raw=REPO/'datasets/paralympics/2026-11-27/raw'
    for name,prefix,expected in [('curb_ramps_aoi.geojson','curb_ramps',20),('street_segments_aoi.geojson','street_segments',10)]:
        source={}
        for path in raw.glob(prefix+'_batch_*.geojson'):
            for f in json.loads(path.read_text())['features']:
                source[int(f['properties']['OBJECTID'])]=f
        extract=json.loads((ROOT.parent/'data'/name).read_text())['features']
        assert len(extract)==expected
        for f in extract:
            original=source[int(f['properties']['OBJECTID'])]
            assert f['geometry']==original['geometry']
            assert f['properties']==original['properties']
        municipal.append({'extract':name,'features':len(extract),'geometry_and_attributes_identical_to_original':True,'original_feature_population':len(source)})
    acquire.dump(AUDIT/'municipal-extract-verification.json',municipal)
    blockers=json.loads((ROOT/'reports/native-acquisition-blocker.json').read_text())
    inv['native_acquisition_exception']=blockers
    followup=ROOT/'reports/native-retry-status.json'
    if followup.exists():
        current=json.loads(followup.read_text())
        inv['native_acquisition_current_status']={
            'status':current['status'],'complete_tiles':current['complete_tiles'],
            'required_tiles':current['required_tiles'],'report':'reports/native-retry-status.json',
            'note':'The older native_acquisition_exception is retained as historical provenance.'}
    inv['coverage_note']='AOI bounds describe the crop filter. Each raw EPT node may extend beyond it; exact node keys/bounds are in reports/lidar-selection.json. County complete intersecting features are not clipped.'
    acquire.dump(ROOT/'source-inventory.json',inv)
    diag=json.loads((ROOT/'reports/independent-diagnostics.json').read_text())
    dem=json.loads((ROOT/'reports/dem-assessment.json').read_text())
    discrepancy=[
      ('G-01','P1','BOUNDARY_UNRESOLVED','Field ellipse / playing-field area','10,213.40 m2 mesh top; 10,215.22 m2 analytic ellipse; guide 12,619.67 m2; 2008 county courtyard 12,472.43 m2','S01 M002/M017/M018/M019; LARIAC2 courtyard 1282840','Different endpoints/epochs; area difference is not established physical error','Match current field/field-court dimension endpoints before changing outline; do not force area'),
      ('G-02','P1','BOUNDARY_UNRESOLVED','Partial bowl / historic overall ellipse','Bowl group X span 297.703 m vs historic approximate 316.3824 m','S04 M158/M159; generated component bounds','Partial group excludes east opening; roof line and complete historic envelope differ','Establish same-boundary current controls; unresolved check now visible as M158'),
      ('G-03','P1','CONDITIONAL_OBSERVED_DISCREPANCY','Uniform seating-bowl profile',f"Conditional vertical median {diag['bowl_conditional_vertical_residual_m']['median_signed_m']:.3f} m; RMSE {diag['bowl_conditional_vertical_residual_m']['rmse_m']:.3f} m; not positional error",'All-depth USGS EPT; model 80 interpolated bands','Provisional pose; seat/fixture returns; hidden surfaces unobserved','Resolve frame; extract multi-sector sections; validate held-out profiles before replacing terraces'),
      ('G-04','P0','UNVERIFIED','Pedestrian circulation / schematic stairs','A009 connectors and estimated walkable/collision surfaces have no surveyed location or connectivity','MVP generator; A002/A006/A009','Traversal tests verify game mechanics only','Survey entrances, ramps, landings, stair flights, door/lift endpoints and clearances; retain schematic labels'),
      ('G-05','P0','PROVISIONAL_REGISTRATION','Horizontal and vertical alignment','Candidate county-courtyard pose; EPT 3857 vs native 6340 and DEM 26911; EPT vertical CRS absent','USGS EPT/native project metadata; candidate-registration.json','PROJ nominal horizontal operation accuracy 2 m; no accepted controls; unknown origin correspondence','Acquire surveyed horizontal control + NAVD88 benchmark; reconcile datums; withhold validation controls'),
      ('G-06','P0','DEM_FIELD_REJECTED_AS_CONTROL','Terrain raster over excavated field',f"Median field DEM minus point Z {dem['field_dem_minus_lidar_m']['median_signed_m']:.3f} m; exterior median absolute {dem['exterior_class2_dem_minus_lidar_m']['median_absolute_m']:.4f} m",'Actual USGS B23 1 m DEM and EPT','Same-survey derivative; field ground-class exclusion/interpolation is inferred cause','Retain both raw sources; do not move field to DEM; inspect ground classification and native metadata'),
      ('G-07','P1','SEMANTICS_UNVERIFIED','Point classification / coverage','Only classes 1/2/7/18; sampled field class 1; 515 bowl cells lack 3 usable first returns','Actual EPT classifications and withheld flags','2D cell occupancy is not complete 3D coverage; no observed hidden interiors','Retain explicit missing masks; manually classify exposed structures for relevant comparisons; no accessible-route promotion'),
      ('G-08','P1','STALE_BOUNDARY_CONTROL','County stadium polygon','Principal stadium and courtyard DATE_=2008; dataset includes 33 features from 2020','County feature OBJECTID 1325059 / 1282840','Roof-line representation; no current tower control or verified HEIGHT/ELEV units','Use as historical spatial context; compare current scan/as-built footprint and retain per-feature epochs'),
      ('G-09','P1','ACQUISITION_BLOCKED','Native LAZ confirmation','Two current native tiles identified; incomplete transfer and HTTP 429 probe','USGS TNM exact URLs / native-acquisition-blocker.json','EPT succeeded; native delivery WKT not inspected','Retry once host permits; verify original WKT/vertical datum and tile classifications; preserve throttling exception'),
      ('G-10','P0','NOT_READY_FOR_PHYSICAL_SIMULATION','Model completeness and acceptance','No complete feature accepted for SR-3D-10; original requirement unchanged','Requirements; source/mesh traceability; independent diagnostics','No feature-specific approved tolerance; under-stand/topology/clearance observations missing','Approve CR-3D-001 and scope; obtain use-critical evidence; keep permanent and event-time overlays separate')]
    if followup.exists() and current['status']=='ACQUIRED_AND_INSPECTED':
        discrepancy=[('G-09','P1','RESOLVED_NATIVE_ACQUISITION','Native LAZ confirmation',
            'Both complete tiles acquired: 127749507 bytes; 29118711 decoded points; embedded EPSG:6340/5703 NAVD88-Geoid18 confirmed',
            'Native source bytes, native-extraction.json and native-retry-status.json',
            'Original HTTP429 blocker retained as historical provenance; same-survey native/EPT agreement is encoding consistency only',
            'Preserve raw source files and checksums; use native coordinates for subsequent analysis; model registration remains provisional')if row[0]=='G-09'else row for row in discrepancy]
    with (AUDIT/'discrepancy-register.csv').open('w',newline='')as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['id','priority','status','component','observation','evidence','limitation','recommended_action']);w.writerows(discrepancy)
    products=[]
    for parent in [ROOT/'derived',ROOT/'reports',AUDIT]:
        for p in sorted(parent.rglob('*')):
            if p.is_file() and p.suffix in ['.json','.csv','.png','.npz','.tif']:
                products.append({'path':str(p.relative_to(REPO)),'bytes':p.stat().st_size,'sha256':sha(p)})
    versions={n:importlib.metadata.version(n)for n in ['numpy','scipy','pyproj','rasterio','shapely','laspy','lazrs','matplotlib']}
    acquire.dump(ROOT/'products-manifest.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
      'python':sys.version,'packages':versions,'raw_objects_verified':len(inv['files']),
      'raw_bytes_verified':sum(r['bytes']for r in inv['files']),
      'source_inventory_sha256':sha(ROOT/'source-inventory.json'),'ept_raw_node_hashes_verified':len(cached),
      'transformations':['All-depth EPT traversal and XY bounding-box crop; source Z unchanged; classification/return/withheld flags retained',
        'County complete features requested with outSR=4326; source metadata retained',
        'DEM window crop in source EPSG:26911, no vertical conversion/resampling',
        'Diagnostic local frame from 2008 courtyard MRR; vertical fit from west field patch; east patch withheld',
        '1 m first-return median grid; >=3 returns; classes7/18 and withheld flags excluded; no gap filling'],
      'products':products,'model_geometry_adopted_from_sources':False,'physical_acceptance':'NOT_VALIDATED'})
    print(json.dumps({'raw_objects_verified':len(inv['files']),'raw_bytes_verified':sum(r['bytes']for r in inv['files']),
      'ept_nodes':len(cached),'municipal':municipal,'products':len(products)},indent=2))


if __name__=='__main__':main()
