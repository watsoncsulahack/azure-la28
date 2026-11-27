#!/usr/bin/env python3
"""Collect the public Paralympic page and its directly cited city GIS layers.

Requires Python 3 and lxml. Does not use credentials or modify remote services.
Usage: python collect.py --output /path/to/new-snapshot-directory
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from lxml import html

PAGE = 'https://la28-planning-hub.lovable.app/paralympics'
ITEM = 'https://www.arcgis.com/sharing/rest/content/items/9973563018bf4dc08517a09f2f7a56c5'
BARRIERS = 'https://maps.lacity.org/arcgis/rest/services/External/SRP_LA28/MapServer/23'


def literal(text, start):
    """Parse data-only JS literals; reject expressions and template interpolation."""
    decoder = re.compile(r'\s*(?:(`(?:\\.|[^`\\])*`)|(-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)|([A-Za-z_$][\w$]*)|([{}\[\],:]))')
    tokens, depth, pos = [], 0, start
    while pos < len(text):
        match = decoder.match(text, pos)
        if not match:
            raise ValueError('Unsupported JS data literal near offset ' + str(pos))
        string, number, word, punctuation = match.groups()
        pos = match.end()
        if string:
            value = string[1:-1]
            if '${' in value or '\\' in value:
                raise ValueError('Unsupported string expression')
            tokens.append(json.dumps(value))
        elif number:
            tokens.append(json.dumps(float(number) if '.' in number or 'e' in number.lower() else int(number)))
        elif word:
            tokens.append(word if word in ('true', 'false', 'null') else json.dumps(word))
        else:
            tokens.append(punctuation)
            depth += int(punctuation in '[{') - int(punctuation in ']}')
            if depth == 0:
                return json.loads(''.join(tokens))
    raise ValueError('Unterminated data literal')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'raw').mkdir()
    collected = dt.datetime.now(dt.timezone.utc).isoformat()
    requests = []

    def write_json(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

    def fetch(url, filename):
        req = Request(url, headers={'User-Agent': 'LA28-classroom-dataset/1.0 (public-data research)'})
        with urlopen(req, timeout=60) as response:
            body = response.read()
            record = {'url': url, 'final_url': response.url, 'status': response.status,
                      'content_type': response.headers.get('Content-Type'),
                      'collected_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                      'file': filename, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
        (out / filename).write_bytes(body)
        requests.append(record)
        return body

    def get_json(url, filename, **params):
        value = json.loads(fetch(url + '?' + urlencode(params or {'f': 'json'}), filename))
        if 'error' in value:
            raise RuntimeError(str(value['error']))
        return value

    def csv_file(name, rows):
        if not rows:
            return
        fields = list(dict.fromkeys(key for row in rows for key in row))
        with (out / name).open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    body = fetch(PAGE, 'raw/page.html')
    doc = html.fromstring(body)
    main_element = doc.xpath('//main')[0]
    for element in main_element.xpath('.//script|.//style|.//*[local-name()="svg"]'):
        element.drop_tree()

    def text(element):
        return ' '.join(element.text_content().split())

    sections = []
    for section in main_element.xpath('.//section[.//h2]'):
        sections.append({'title': text(section.xpath('.//h2')[0]), 'text': text(section),
                         'paragraphs': [text(p) for p in section.xpath('.//p')],
                         'list_items': [text(li) for li in section.xpath('.//li')],
                         'links': [{'label': text(a), 'url': urljoin(PAGE, a.get('href'))}
                                   for a in section.xpath('.//a[@href]')]})
    links = [{'label': text(a), 'url': urljoin(PAGE, a.get('href'))}
             for a in main_element.xpath('.//a[@href]')]
    page_data = {'title': text(doc.xpath('//title')[0]), 'source_url': PAGE,
                 'collected_at_utc': collected, 'full_text': text(main_element), 'sections': sections, 'links': links}
    write_json('page_content.json', page_data)
    (out / 'page_text.txt').write_text(page_data['title'] + '\n\n' + page_data['full_text'] + '\n')
    csv_file('page_links.csv', links)
    csv_file('section_content.csv', [{'section': s['title'], 'text': s['text'], 'source_url': PAGE,
                                     'collected_at_utc': collected} for s in sections])
    csv_file('planning_notes.csv', [{'section': s['title'], 'item_index': i + 1, 'text': item,
                                    'source_url': PAGE, 'collected_at_utc': collected}
                                   for s in sections for i, item in enumerate(s['list_items'])])

    asset = next(urljoin(PAGE, e.get('href')) for e in doc.xpath('//link[@href]')
                 if '/paralympics-' in e.get('href', '') and e.get('href').endswith('.js'))
    js = fetch(asset, 'raw/paralympics.js').decode()
    match = re.search(r'\b\w+=(\{fetchedAt:)', js)
    if not match:
        raise ValueError('Page data structure changed; update extractor')
    snapshot = literal(js, match.start(1))
    match = re.search(r'\b\w+=(\[\{step:)', js)
    technology = literal(js, match.start(1))
    write_json('page_accessibility_data.json', snapshot)
    write_json('organizer_technology.json', technology)
    context = {'page_url': PAGE, 'collected_at_utc': collected, 'page_snapshot_date': snapshot['fetchedAt'],
               'page_dataset_updated_date': snapshot['datasetUpdated'], 'verification': 'reported_by_page'}
    csv_file('venues.csv', [dict(v, **context) for v in snapshot['venues']])
    csv_file('barrier_sites.csv', [dict(v, **context) for v in snapshot['barriers']])
    csv_file('summary_metrics.csv', [dict(metric=k, value=v, **context) for k, v in snapshot['summary'].items()])
    csv_file('organizer_technology.csv', [dict(v, **context) for v in technology])
    resources = []
    for a in main_element.xpath('.//a[@href][contains(@class,"group")]'):
        spans = a.xpath('./span')
        if len(spans) >= 2:
            resources.append({'title': text(spans[0]), 'description': text(spans[1]),
                              'url': urljoin(PAGE, a.get('href')), 'card_text': text(a), **context})
    csv_file('resources.csv', resources)

    item = get_json(ITEM, 'raw/arcgis_item.json', f='json')
    root = item['url']

    def layer(name, url, fields, where='1=1'):
        metadata = get_json(url, 'raw/' + name + '_metadata.json', f='json')
        oid = metadata.get('objectIdField') or metadata.get('objectIdFieldName') or next(
            f['name'] for f in metadata['fields'] if f['type'] == 'esriFieldTypeOID')
        ids = get_json(url + '/query', 'raw/' + name + '_ids.json', f='json', where=where, returnIdsOnly='true')
        expected = sorted(ids.get('objectIds') or [])
        features = []
        for start in range(0, len(expected), 100):
            data = get_json(url + '/query', f'raw/{name}_batch_{start // 100}.geojson', f='geojson',
                            objectIds=','.join(map(str, expected[start:start + 100])),
                            outFields=fields, returnGeometry='true', outSR=4326)
            if data.get('exceededTransferLimit'):
                raise ValueError('Transfer limit exceeded: ' + name)
            features.extend(data['features'])
        actual = [f['properties'][oid] for f in features]
        if len(actual) != len(set(actual)) or sorted(actual) != expected:
            raise ValueError('Missing or duplicate records: ' + name)
        write_json(name + '.geojson', {'type': 'FeatureCollection', 'features': features})
        rows = []
        for feature in features:
            row = dict(feature['properties'])
            geometry = feature.get('geometry')
            if geometry and geometry['type'] == 'Point':
                row.update(longitude=geometry['coordinates'][0], latitude=geometry['coordinates'][1])
            row.update(source_layer_url=url, source_filter=where, collected_at_utc=collected)
            rows.append(row)
        csv_file(name + '.csv', rows)
        return {'count': len(features), 'url': url, 'filter': where, 'complete_id_check': True,
                'spatial_reference': 'WGS84 / EPSG:4326'}, features

    layers = {}
    layers['curb_ramps'], ramps = layer('curb_ramps', root + '/0', 'OBJECTID,CURBRAMP_ID,ASSETID,PIND,HASRAMP,CRTN_DT,LST_MODF_DT')
    layers['city_venue_points'], venues = layer('city_venue_points', root + '/1', '*')
    layers['street_segments'], streets = layer('street_segments', root + '/2', '*')
    layers['live_barrier_points'], barriers = layer('live_barrier_points', BARRIERS,
        'OBJECTID,Site_No,Address,Date_Logged,Council_District,Number_CurbRamps,Subtype,isLA28', 'isLA28=1')

    summary = snapshot['summary']
    checks = {
        'venue_row_count': len(snapshot['venues']),
        'barrier_site_count': len(snapshot['barriers']),
        'resource_count': len(resources),
        'page_venue_totals_consistent': all(v['hasRamps'] + v['missingRamps'] == v['totalRamps'] for v in snapshot['venues']),
        'page_missing_percentages_consistent': all(abs(round(v['missingRamps'] / v['totalRamps'] * 100, 1) - v['missingPct']) < 0.01 for v in snapshot['venues']),
        'page_summary_matches_venue_totals': {
            'with_ramp': sum(v['hasRamps'] for v in snapshot['venues']) == summary['cornersWithRamp'],
            'missing_ramp': sum(v['missingRamps'] for v in snapshot['venues']) == summary['cornersMissingRamp'],
            'total': sum(v['totalRamps'] for v in snapshot['venues']) == summary['cornersTotal']},
        'page_street_miles_sum': round(sum(v['centerlineMiles'] for v in snapshot['venues']), 1),
        'page_street_miles_summary': summary['streetMilesCovered'],
        'live_ramp_values': dict(collections.Counter(str(f['properties']['HASRAMP']) for f in ramps)),
        'live_barrier_raw_records': len(barriers),
        'live_barrier_unique_addresses': len(set(f['properties']['Address'] for f in barriers)),
        'live_barrier_unique_normalized_addresses': len(set(' '.join(f['properties']['Address'].upper().split()) for f in barriers)),
        'live_barrier_repeated_normalized_addresses': {k: v for k, v in collections.Counter(
            ' '.join(f['properties']['Address'].upper().split()) for f in barriers).items() if v > 1},
        'live_venue_point_records': len(venues),
        'live_venue_unique_normalized_names': len(set(' '.join(f['properties']['Venues_ProperNames'].upper().split()) for f in venues)),
        'live_street_segment_records': len(streets),
        'all_layer_id_sets_complete': all(v['complete_id_check'] for v in layers.values()),
        'external_articles_independently_verified': False,
        'route_safety_or_ADA_compliance_verified': False,
    }
    write_json('validation.json', checks)
    write_json('manifest.json', {'source_page': PAGE, 'collected_at_utc': collected,
        'page_snapshot_date': snapshot['fetchedAt'], 'layers': layers, 'requests': requests,
        'scope': 'Complete delivered page content and embedded data; four directly cited public GIS layers. External articles, PDFs, and other site pages are catalogued, not crawled.'})
    write_json('data_dictionary.json', {
        'venues.csv': {'name': 'City unofficial venue name, not a verified Paralympic competition site',
            'centerlineMiles': 'Street centerline miles; already rounded by page', 'streetSegments': 'Page-reported street segments',
            'hasRamps': 'Corners classified as ramp present', 'missingRamps': 'Corners classified as missing ramp',
            'totalRamps': 'Corners inventoried, including missing ramps; not installed-ramp count',
            'missingPct': 'Percentage of inventoried corners missing a ramp'},
        'barrier_sites.csv': {'curbRampsNoted': 'Raw page value; zero means none noted, not proof of no ramp',
            'requests': 'Page-grouped request count', 'loggedOn': 'Page-reported date, not repair completion date',
            'subtype': 'City category', 'kind': 'Page grouping: la28-site or access-request'},
        'GIS': {'geometry': 'GeoJSON longitude/latitude WGS84; no geocoding or routing inferred',
            'dates': 'ArcGIS date attributes remain Unix epoch milliseconds, null remains null',
            'domains': 'Coded field meanings retained in raw/*_metadata.json',
            'street_segments.csv': 'Attributes only; full lines in street_segments.geojson',
            'live_barrier_points': 'Raw source records, not merged; can exceed page grouped-site count'},
        'provenance': {'page_snapshot_date': 'Date claimed by page, not collection date',
            'page_dataset_updated_date': 'StreetsLA venue dataset date claimed by page, not all-layer freshness',
            'collected_at_utc': 'Collector execution timestamp', 'verification': 'Page claims remain unverified unless noted'},
    })
    readme = f'''# LA28 Paralympic page dataset

Source: {PAGE}
Collected: {collected}
Page's own snapshot: {snapshot['fetchedAt']}; stated StreetsLA venue dataset update: {snapshot['datasetUpdated']}.

## Contents
- `page_content.json`, `page_text.txt`, `raw/page.html`: the complete delivered main-page content, headings, prose, questions, citations and caveats. HTML is retained losslessly.
- `venues.csv`: {len(snapshot['venues'])} venue-area summaries. These are city-listed LA28 venues, not a confirmed Paralympic venue list.
- `barrier_sites.csv`: {len(snapshot['barriers'])} grouped sites reported by the page.
- `summary_metrics.csv`: page-reported summary figures.
- `section_content.csv`, `planning_notes.csv`: spreadsheet-friendly section text and list items, including fieldwork and research questions.
- `organizer_technology.csv` / `.json`: four teaching-map examples and their source URLs.
- `resources.csv`: {len(resources)} resource cards, including descriptions and page review metadata. `page_links.csv` includes every link in main content.
- `curb_ramps.csv` / `.geojson`: {len(ramps)} public city corner/ramp records.
- `city_venue_points.csv` / `.geojson`: {len(venues)} raw venue points, preserved as-is rather than forced to the page's 20-venue count.
- `street_segments.csv` / `.geojson`: {len(streets)} street records with full line geometry in GeoJSON.
- `live_barrier_points.csv` / `.geojson`: {len(barriers)} raw city records tagged `isLA28=1`, versus {len(snapshot['barriers'])} grouped page sites. Do not join these positionally.
- `manifest.json`: request URLs, timestamps, SHA-256 checksums, record counts, completeness checks.
- `validation.json`, `data_dictionary.json`, and `raw/*_metadata.json`: checks and field definitions, including official coded-value domains.

## Important limitations
This is accessibility inventory, not observed street traffic, travel times, or a validated routing network. No safe or step-free route is established. Ramp existence does not establish ADA compliance, slope, surface condition, continuity, or current access. Venue buffers can overlap; do not assume all per-venue totals represent distinct physical corners. Source IDs are retained for later spatial checks. City datasets and page snapshot are separate observations collected on different dates; discrepancies are retained, not silently reconciled. Zero ramps noted in a barrier request is not proof that a site has no ramp. The full source-backed route graph still requires crossings, connectivity, transit access and current field verification.

Record-count reconciliation: the city has two records for `900 GAYLEY AVE` (one with trailing whitespace), while the page groups them as one site with two requests. Case/whitespace-normalized city addresses total 19. There are two venue point records named `SEPULVEDA BASIN SPORTS COMPLEX`, yielding 20 distinct normalized venue names from 21 points. Both point records are retained.

Page caveats:
''' + '\n'.join('- ' + c for c in snapshot['caveats']) + '''

The page is an independent educational project, not an official LA28 publication. Its claims and external articles have not been independently verified. Blank license/attribution fields in a source item are not a license grant; confirm reuse terms before redistribution.

## Reproduce
Run `python ../collect.py --output /path/to/new-directory` from this snapshot directory. Requires Python 3, lxml, and HTTPS access to the page and the directly cited city/ArcGIS hosts. No tokens or secrets are used. The output directory must not exist. TLS verification stays enabled. The scraper fails if data literals or schemas change, rather than evaluating website JavaScript. ArcGIS IDs are paged in batches of 100 to stay within server URL limits and checked for omissions and duplicates.
'''
    (out / 'README.md').write_text(readme)
    print(json.dumps({'output': str(out), 'layers': layers, 'validation': checks}, indent=2))


if __name__ == '__main__':
    main()
