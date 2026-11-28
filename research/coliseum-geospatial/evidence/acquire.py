#!/usr/bin/env python3
"""Acquire bounded real data; preserve upstream bytes and log every HTTP response.

EPT traversal includes every intersecting node at every depth (no preview/LOD limit).
Raw files are cached, never modified. Delete individual cached files to reacquire.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw'
DERIVED = ROOT / 'derived'
REPORTS = ROOT / 'reports'
AOI = [-118.2923, 34.0109, -118.2839, 34.0170]
EPT = 'https://s3-us-west-2.amazonaws.com/usgs-lidar-public/CA_LosAngeles_1_B23/'
BUILDING = ('https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/'
            'Countywide_Building_Outlines_%282020%29/FeatureServer')
USGS_META = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/metadata/'
             'CA_LosAngeles_B23/CA_LosAngeles_1_B23/')
URLS = {
    'usgs-lpc-products.json': 'https://tnmaccess.nationalmap.gov/api/v1/products?' + urlencode({
        'bbox': ','.join(map(str, AOI)), 'datasets': 'Lidar Point Cloud (LPC)', 'max': 50}),
    'ept.json': EPT + 'ept.json',
    'ept-hierarchy-root.json': EPT + 'ept-hierarchy/0-0-0-0.json',
    'building-layer.json': BUILDING + '/0?f=pjson',
    'building-service.json': BUILDING + '?f=pjson',
    'building-item.json': 'https://www.arcgis.com/sharing/rest/content/items/e6a1e375e12a4fe6849d896a26ec028a?f=pjson',
    'county-terms.html': 'https://egis-lacounty.hub.arcgis.com/pages/terms-of-use',
    'noaa-dem.html': 'https://www.fisheries.noaa.gov/inport/item/80274',
    'usgs-summary.pdf': USGS_META + 'reports/USGS_CA_LosAngeles_1_B23_Summary_Report.pdf',
    'usgs-workunit.pdf': USGS_META + 'reports/LA_County_Report_WU300609.pdf',
    'guide2024.pdf': 'https://lacoliseum.com/wp-content/uploads/2024/12/Coliseum_Technical_Guide_Draft2024.pdf',
    'nps1984.pdf': 'https://npgallery.nps.gov/NRHP/GetAsset/NHLS/84003866_text',
    'usgs-products.json': 'https://tnmaccess.nationalmap.gov/api/v1/products?' + urlencode({
        'bbox': ','.join(map(str, AOI)), 'datasets': 'Digital Elevation Model (DEM) 1 meter', 'max': 30}),
}


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def fetch(name, url):
    path = RAW / name
    receipt = path.with_suffix(path.suffix + '.receipt.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        for attempt in range(3):
            try:
                with urlopen(Request(url, headers={'User-Agent': 'IS699-Coliseum-Evidence/1.0'}), timeout=45) as r:
                    meta = {'url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                            'http_status': r.status, 'etag': r.headers.get('ETag'),
                            'http_date': r.headers.get('Date'),
                            'last_modified': r.headers.get('Last-Modified'),
                            'content_type': r.headers.get('Content-Type')}
                    started = time.monotonic()
                    partial = path.with_suffix(path.suffix+'.part')
                    with partial.open('wb') as output:
                        while chunk := r.read(1024*1024):
                            output.write(chunk)
                            if time.monotonic()-started > 180:
                                raise TimeoutError('Transfer exceeded 180 s total body-read budget')
                partial.replace(path)
                dump(receipt, meta)
                break
            except Exception as e:
                partial = path.with_suffix(path.suffix+'.part')
                received = partial.stat().st_size if partial.exists() else 0
                partial.unlink(missing_ok=True)
                if attempt == 2 or isinstance(e,HTTPError) and e.code==429:
                    dump(receipt, {'url': url, 'error': repr(e), 'attempts': attempt+1,
                                   'http_status': e.code if isinstance(e,HTTPError) else None,
                                   'partial_bytes_discarded': received,
                                   'attempted_utc': datetime.now(timezone.utc).isoformat()})
                    raise
                time.sleep(1)
    if not receipt.exists():
        # Initial exploratory retrievals predated this recorder. Do not invent headers/time.
        dump(receipt, {'url': url, 'retrieved_utc': None,
                      'file_mtime_utc': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                      'note': 'Cached initial retrieval; file mtime is an acquisition-time proxy; headers unavailable.'})
    return path


def metadata():
    with ThreadPoolExecutor(max_workers=5) as ex:
        for name, path in zip(URLS, ex.map(lambda kv: fetch(*kv), URLS.items())):
            print(name, path.stat().st_size, flush=True)


def buildings():
    query = BUILDING + '/0/query?'
    params = {'f': 'json', 'where': '1=1', 'geometry': ','.join(map(str, AOI)),
              'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
              'spatialRel': 'esriSpatialRelIntersects', 'returnIdsOnly': 'true'}
    ids = json.loads(fetch('building-ids.json', query + urlencode(params)).read_text())
    if ids.get('error') or not ids.get('objectIds'):
        raise ValueError(ids)
    wanted = sorted(ids['objectIds'])
    features = []
    for start in range(0, len(wanted), 250):
        params = {'f': 'geojson', 'objectIds': ','.join(map(str, wanted[start:start+250])),
                  'outFields': '*', 'outSR': 4326, 'returnGeometry': 'true'}
        page = json.loads(fetch(f'building-features-{start}.geojson', query + urlencode(params)).read_text())
        features.extend(page['features'])
    actual = [int(f['properties']['OBJECTID']) for f in features]
    if sorted(actual) != wanted:
        raise ValueError('Missing or duplicated county features')
    dump(DERIVED / 'buildings.geojson', {'type': 'FeatureCollection', 'features': features})
    print('County features:', len(features), flush=True)


def node_bounds(key, bounds):
    depth, x, y, z = map(int, key.split('-'))
    size = [(bounds[j+3] - bounds[j]) / 2**depth for j in range(3)]
    lo = [bounds[j] + [x, y, z][j] * size[j] for j in range(3)]
    return lo + [lo[j]+size[j] for j in range(3)]


def intersects_xy(a, b):
    return a[0] <= b[2] and a[3] >= b[0] and a[1] <= b[3] and a[4] >= b[1]


def lidar():
    import laspy
    import numpy as np
    from pyproj import Transformer
    ept = json.loads(fetch('ept.json', EPT+'ept.json').read_text())
    transform = Transformer.from_crs(4326, ept['srs']['horizontal'], always_xy=True)
    w, s = transform.transform(*AOI[:2]); e, n = transform.transform(*AOI[2:])
    crop = [w, s, e, n]
    pending, visited, nodes = ['0-0-0-0'], set(), {}
    while pending:
        key = pending.pop()
        if key in visited:
            continue
        visited.add(key)
        name = 'ept-hierarchy-root.json' if key == '0-0-0-0' else f'ept-hierarchy/{key}.json'
        hierarchy = json.loads(fetch(name, EPT+f'ept-hierarchy/{key}.json').read_text())
        for node, count in hierarchy.items():
            if not intersects_xy(node_bounds(node, ept['bounds']), crop):
                continue
            if count == -1:
                pending.append(node)
            elif count > 0:
                nodes[node] = count
    dump(REPORTS/'lidar-selection.json', {'aoi_epsg4326': AOI, 'ept_horizontal_crs': ept['srs'],
         'crop_native': crop, 'hierarchy_pages': sorted(visited), 'nodes': nodes,
         'method': 'All intersecting nodes at every depth. No resolution or depth cutoff.'})
    print('EPT selected nodes:', len(nodes), 'uncropped points:', sum(nodes.values()), flush=True)
    def get(key):
        return key, fetch(f'ept-data/{key}.laz', EPT+f'ept-data/{key}.laz')
    arrays = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for index, (key, path) in enumerate(ex.map(get, sorted(nodes))):
            cloud = laspy.read(path)
            if len(cloud.points) != nodes[key]:
                raise ValueError(f'EPT count mismatch {key}')
            x, y, z = np.asarray(cloud.x), np.asarray(cloud.y), np.asarray(cloud.z)
            mask = (x >= w) & (x <= e) & (y >= s) & (y <= n)
            arrays.append(np.column_stack((x[mask], y[mask], z[mask], np.asarray(cloud.classification)[mask],
                                           np.asarray(cloud.return_number)[mask], np.asarray(cloud.withheld)[mask],
                                           np.asarray(cloud['ClassFlags'])[mask])))
            if index % 20 == 0:
                print('read', index+1, '/', len(nodes), flush=True)
    points = np.concatenate(arrays)
    DERIVED.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(DERIVED/'lidar-aoi.npz', points=points)
    dump(REPORTS/'lidar-extraction.json', {'points': len(points), 'columns': ['easting_3857', 'northing_3857', 'z_source_m', 'classification', 'return_number', 'las_withheld', 'ept_ClassFlags'],
         'bounds': [points[:,:3].min(axis=0).tolist(), points[:,:3].max(axis=0).tolist()],
         'node_count': len(nodes), 'all_intersecting_nodes_downloaded': True,
         'vertical_datum': 'EPT has no vertical CRS; original project reports NAVD88/GEOID18. Confirm against native delivery before absolute-height acceptance.'})


def dem():
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.warp import transform_bounds
    catalog = json.loads(fetch('usgs-products.json', URLS['usgs-products.json']).read_text())
    current = [i for i in catalog['items'] if 'CA_LosAngeles_B23' in i['title']]
    if len(current) != 1:
        raise ValueError('Ambiguous current DEM selection')
    item = current[0]
    # Preserve the complete tile, rather than presenting a range-read crop as raw data.
    path = fetch('dem/'+item['downloadURL'].split('/')[-1], item['downloadURL'])
    with rasterio.open(path) as src:
        bb = transform_bounds(4326, src.crs, *AOI, densify_pts=21)
        win = from_bounds(*bb, src.transform).round_offsets().round_lengths()
        data = src.read(1, window=win)
        profile = src.profile.copy(); profile.update(width=data.shape[1], height=data.shape[0], transform=src.window_transform(win), compress='deflate')
        DERIVED.mkdir(parents=True, exist_ok=True)
        with rasterio.open(DERIVED/'dem-aoi.tif', 'w', **profile) as dst:
            dst.write(data, 1)
        dump(REPORTS/'dem-extraction.json', {'catalog_item': item, 'crs_wkt': src.crs.to_wkt(),
             'resolution': src.res, 'source_bounds': list(src.bounds), 'crop_window': list(win.flatten()),
             'crop_shape': data.shape, 'source_tags': src.tags(), 'nodata': src.nodata,
             'vertical_datum': 'Project NAVD88/GEOID18; verify tile metadata before absolute-height acceptance.',
             'limitation': '1 m bare earth, derived from same lidar survey; not independent validation of that survey.'})


def native_metadata(selected):
    import xml.etree.ElementTree as ET
    rows=[]
    for item in selected:
        url=item['vendorMetaUrl']
        path=fetch('native-metadata/'+url.split('/')[-1],url)
        xml=ET.parse(path)
        value=lambda key:xml.findtext('.//'+key)
        rows.append({'tile':path.stem,'metadata_url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'publication_date':value('pubdate'),'acquisition_start':value('begdate'),'acquisition_end':value('enddate'),
            'horizontal_reference':value('gridsysn'),'vertical_datum':value('altdatum'),
            'vertical_units':value('altunits'),'reported_altitude_resolution':value('altres'),
            'reported_vertical_accuracy':value('vertaccr')})
    report=REPORTS/'native-metadata-assessment.json'
    previous=json.loads(report.read_text())if report.exists()else{}
    dump(report,{**previous,'tiles':rows,
        'interpretation':'Per-tile source metadata, not decoded native-file CRS or measured site accuracy. XML altitude resolution 1.0 m and partial LAS coordinate scale 0.01 m are distinct metadata; neither establishes site accuracy.'})


def native():
    import laspy
    import numpy as np
    from pyproj import Transformer
    from native_transfer import fetch_native
    catalog = json.loads(fetch('usgs-lpc-products.json', URLS['usgs-lpc-products.json']).read_text())
    selected = [i for i in catalog['items'] if 'CA_LosAngeles_B23' in i['title']]
    if len(selected) != 2:
        raise ValueError('Expected two current native tiles; review changed catalog')
    native_metadata(selected)
    downloads=[]
    for item in selected:
        path=fetch_native(RAW/'native'/item['downloadURL'].split('/')[-1],
                          item['downloadURL'],int(item['sizeInBytes']))
        downloads.append((item,path))
    arrays, headers = [], []
    for item,path in downloads:
        with laspy.open(path) as src:
            crs = src.header.parse_crs()
            if crs is None:
                raise ValueError('Native LAS has no CRS')
            horizontal = crs.sub_crs_list[0] if crs.is_compound else crs
            vertical = crs.sub_crs_list[1] if crs.is_compound else None
            t = Transformer.from_crs(horizontal, 4326, always_xy=True)
            headers.append({'item': item, 'crs_wkt': crs.to_wkt(), 'point_count': src.header.point_count,
                            'horizontal_epsg': horizontal.to_epsg(),
                            'vertical_epsg': vertical.to_epsg()if vertical else None,
                            'vertical_crs_name': vertical.name if vertical else None,
                            'scales': src.header.scales.tolist(), 'offsets': src.header.offsets.tolist(),
                            'creation_date': str(src.header.creation_date), 'version': str(src.header.version),
                            'point_format': src.header.point_format.id})
            decoded = 0
            for cloud in src.chunk_iterator(1000000):
                decoded += len(cloud)
                x, y, z = np.asarray(cloud.x), np.asarray(cloud.y), np.asarray(cloud.z)
                lon, lat = t.transform(x, y)
                mask = (lon >= AOI[0]) & (lon <= AOI[2]) & (lat >= AOI[1]) & (lat <= AOI[3])
                # Retain overlap and withheld flags so analytical filters can be audited.
                arrays.append(np.column_stack((x[mask], y[mask], z[mask], np.asarray(cloud.classification)[mask],
                    np.asarray(cloud.return_number)[mask], np.asarray(cloud.overlap)[mask],
                    np.asarray(cloud.withheld)[mask])))
            if decoded != src.header.point_count:
                raise ValueError(f'Native LAZ decoded count mismatch: {path.name}')
            headers[-1]['fully_decoded_point_count'] = decoded
        print('Native tile read:', path.name, flush=True)
    points = np.concatenate(arrays)
    DERIVED.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(DERIVED/'native-aoi.npz', points=points)
    dump(REPORTS/'native-extraction.json', {'tiles': headers, 'aoi_epsg4326': AOI, 'points': len(points),
        'columns': ['source_x', 'source_y', 'source_z', 'classification', 'return_number', 'overlap', 'withheld'],
        'vertical_reference': 'Read native WKT and original project report; do not infer vertical datum from plausible Z values.'})


def inventory():
    rows = []
    for path in sorted(RAW.rglob('*')):
        if not path.is_file() or path.name.endswith('.receipt.json') or path.suffix=='.part':
            continue
        receipt = path.with_suffix(path.suffix+'.receipt.json')
        if not receipt.exists():
            continue
        meta = json.loads(receipt.read_text())
        rows.append({'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **meta})
    failures=[json.loads(p.read_text()) for p in RAW.rglob('*.receipt.json') if 'error' in json.loads(p.read_text())]
    partials=[json.loads(p.read_text())for p in RAW.rglob('*.part.receipt.json')]
    dump(ROOT/'source-inventory.json', {'aoi_epsg4326': AOI, 'files': rows,'failed_acquisitions':failures,
         'incomplete_transfers_not_counted_as_sources':partials,
         'storage': 'raw/ is a local immutable cache, intentionally excluded from Git. Reacquire with acquire.py; verify hashes before reuse.',
         'license': {'USGS': 'US federal public-domain elevation data; attribution and source metadata retained.',
             'county': 'LARIAC / County of Los Angeles / Pictometry / EagleView; county terms and item license apply; no engineering/survey suitability warranty.',
             'architecture': 'Publisher rights retained; PDFs cached for research, not redistributed.'}})


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('stage', choices=['metadata', 'buildings', 'lidar', 'native', 'dem', 'inventory', 'all'])
    args = ap.parse_args()
    try:
        for name, fn in [('metadata', metadata), ('buildings', buildings), ('lidar', lidar), ('dem', dem), ('native', native)]:
            if args.stage in [name, 'all']:
                try:
                    fn()
                except Exception as error:
                    if args.stage != 'all':
                        raise
                    dump(REPORTS/f'{name}-stage-error.json',{'stage':name,'error':repr(error),
                         'status':'BLOCKED; other stages continue'})
                    print(name,'BLOCKED:',repr(error),flush=True)
    finally:
        inventory()
