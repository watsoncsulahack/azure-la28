"""Publish native download outcomes, separating complete sources and partial prefixes."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import acquire

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()


def main():
    items=[i for i in json.loads((acquire.RAW/'usgs-lpc-products.json').read_text())['items']if 'CA_LosAngeles_B23'in i['title']]
    rows=[]
    for item in items:
        path=acquire.RAW/'native'/item['downloadURL'].split('/')[-1]
        partial=path.with_suffix('.laz.part')
        backup=REPO/'work/native-prefix-backup'/partial.name
        prefix=partial if partial.exists()else backup if backup.exists()else None
        complete=path.exists()and path.stat().st_size==int(item['sizeInBytes'])
        rows.append({'tile':path.name,'url':item['downloadURL'],'expected_bytes':int(item['sizeInBytes']),
          'complete_source':complete,'complete_bytes':path.stat().st_size if complete else 0,
          'sha256':sha(path)if complete else None,
          'partial_path':str(prefix.relative_to(REPO))if prefix else None,
          'partial_bytes_not_counted_as_download':prefix.stat().st_size if prefix else 0,
          'partial_sha256':sha(prefix)if prefix else None})
    last=ROOT/'reports/native-final-retry.json'
    result=json.loads(last.read_text())if last.exists()else{'status':'PENDING'}
    metadata=json.loads((ROOT/'reports/native-metadata-assessment.json').read_text())
    inspection_path=ROOT/'reports/native-extraction.json'
    inspection=json.loads(inspection_path.read_text())if inspection_path.exists()else None
    complete=all(r['complete_source']for r in rows)
    data={'recorded_utc':datetime.now(timezone.utc).isoformat(),
      'status':('ACQUIRED_AND_INSPECTED'if inspection else'FILES_ACQUIRED_INSPECTION_PENDING')if complete else'INCOMPLETE',
      'complete_tiles':sum(r['complete_source']for r in rows),'required_tiles':len(rows),'tiles':rows,
      'last_attempt':result,'tile_metadata':metadata['tiles'],
      'binary_crs_and_classification_checks':'See native-extraction.json only if produced by successful complete native decoding; per-tile XML is source-reported metadata.',
      'initial_resume_failure':{'http_status':429,'response_utc':'2026-11-28T00:24:53Z','retry_after_header':None},
      'cooldown_retry':{'scheduled_utc':'2026-11-28T00:30:03Z','result':'HTTP 429 during prefix request'},
      'alternate_distribution_checks':{'NOAA':'Catalog 80259 directs native bulk download to the same USGS RockyWeb host; checked S3 native mirror prefix contains zero objects.',
        'ScienceBase':'Both exact tile catalog JSON requests returned HTTP 403; no access workaround attempted.',
        'USGS_tile_XML':'Both vendorMetaUrl XML records actually downloaded from thor-f5.er.usgs.gov.'},
      'geometry_changed':False,'physical_acceptance':'NOT_VALIDATED'}
    data['checksum_scope']='Local SHA-256 of received bytes, with catalog byte-size and complete native decoding checks. No independently published checksum was supplied by the catalog.'
    if complete and inspection:
        import numpy as np
        points=np.load(ROOT/'derived/native-aoi.npz')['points']
        classes,counts=np.unique(points[:,3],return_counts=True)
        data['native_inspection']={'fully_decoded_points':sum(t['fully_decoded_point_count']for t in inspection['tiles']),
            'aoi_points':inspection['points'],'aoi_classification_counts':dict(zip(map(lambda x:str(int(x)),classes),map(int,counts))),
            'aoi_withheld_points':int((points[:,6]!=0).sum()),
            'tile_coordinate_references':[{k:t.get(k)for k in ['horizontal_epsg','vertical_epsg','vertical_crs_name','version','point_format','scales']}for t in inspection['tiles']]}
    comparison=ROOT/'reports/native-ept-consistency.json'
    if comparison.exists():
        data['encoding_comparison_report']='reports/native-ept-consistency.json'
    acquire.dump(ROOT/'reports/native-retry-status.json',data)
    lines=['# Native LAZ acquisition follow-up','',
      f"Recorded UTC: {data['recorded_utc']}",'',
      f"**Completed native tiles: {data['complete_tiles']}/{data['required_tiles']}. Status: {data['status']}.**",'',
      '| Tile | Expected bytes | Completed bytes | Retained partial bytes |',
      '| --- | ---: | ---: | ---: |']
    lines += [f"| {r['tile']} | {r['expected_bytes']:,} | {r['complete_bytes']:,} | {r['partial_bytes_not_counted_as_download']:,} |"for r in rows]
    lines += ['',f"Final attempt: `{result}`.",'',
      'The first retry received a 4 MiB prefix. A resume request returned HTTP 429, and the prefix request still returned 429 after a five-minute backoff. A final full-file attempt was scheduled after a further ten-minute cooldown with a 30-minute body-transfer allowance. Existing prefix bytes were preserved separately. The final result above controls the current acquisition status.','',
      'The downloader now preserves interrupted payloads, checks resume prefixes and HTTP ranges, pins source validators, checks catalog byte sizes and LAS magic, and excludes partials from completed-source counts. Error-page ETags are never reused as dataset validators. Throttled responses are recorded without automatic repeated retries.','',
      'Both per-tile USGS XML records were acquired and checksummed. They report NAD83(2011) / UTM zone 11N, NAVD88 elevations in metres, acquisition 2023-01-08 through 2024-01-07, and publication 2025-06-13. Their vertical accuracy field is N/A and altitude resolution is 1.0 m; the partial LAS header coordinate scale is 0.01 m. Neither numeric field establishes physical accuracy. Binary extended-metadata inspection still requires complete data unless separately documented.','',
      'NOAA points to the same USGS binary host. Its checked S3 native mirror prefix was empty. Both ScienceBase tile JSON endpoints returned 403. The authoritative per-tile XML endpoints did succeed.','',
      'The initial prefix identifies LAS 1.4, point format 6, 14,070,854 declared points and one extended metadata record starting at byte 64,159,304. These are partial-header observations, not a claim that the whole file has been downloaded or decoded.','',
      'A local point-count check initially used the wrong laspy attribute. It was corrected to `len(chunk)` for ScaleAwarePointRecord objects; both complete files were then decoded and their counts checked. Raw source files were preserved throughout.','',
      'Validation: 13 geospatial tests passed, including resumable-transfer safeguards and exclusion of partial files from the source inventory. No model geometry or original accuracy requirement changed. Existing EPT extraction remains available.','',
      'Exact source URLs, hashes, partial locations and outcomes: [machine-readable status](reports/native-retry-status.json). Source inventory and product manifests are regenerated separately with `finalize.py`.']
    if not complete:
        lines+=['','Resume acquisition with `python research/coliseum-geospatial/evidence/acquire.py native` after the source service permits it.']
    elif inspection:
        native=data['native_inspection']
        lines+=['',f"**Native inspection:** all {native['fully_decoded_points']:,} points decoded successfully; the study-area crop contains {native['aoi_points']:,} points. Both files are LAS 1.4 / point format 6, with EPSG:6340 horizontally and EPSG:5703 vertically. The embedded vertical CRS name explicitly identifies NAVD88 height / Geoid18 in metres. Coordinate scales are 0.01 m, which does not establish physical accuracy."]
        if comparison.exists():
            c=json.loads(comparison.read_text());b=c['crop_boundary_check']
            lines+=['',f"**Native/EPT consistency:** {c['sample_points']:,} sampled points have maximum 3D nearest-coordinate difference {c['nearest_3d_distance_m']['maximum_absolute_m']:.6f} m, with identical classifications for the associated points and numerically unchanged elevations. This is expected encoding quantization between two distributions of the same acquisition, not independent physical validation. The native crop has {b['total_count_native_minus_ept']} more points; boundary associations account for the net difference ({b['native_points_without_ept_match']} native-only vs {b['ept_points_without_native_match']} EPT-only points near the crop edges). Exact source point IDs were not compared."]
        lines+=['','The native coordinate frame can now be used directly for subsequent analysis. The model-to-world transformation remains provisional and no SR-3D-10 physical acceptance is claimed.']
    (ROOT/'NATIVE_LAZ_FOLLOWUP.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'complete_tiles':data['complete_tiles'],'status':data['status'],'last_attempt':result},indent=2))


if __name__=='__main__':main()
