#!/usr/bin/env python3
"""Extract the public Paralympics page into JSON and CSV snapshots."""
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin

from bs4 import BeautifulSoup

SOURCE = 'https://la28-planning-hub.lovable.app/paralympics'


def text(node):
    return node.get_text(' ', strip=True) if node else ''


def extract(html, retrieved_at):
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('main')
    if not main:
        raise ValueError('Source main element is missing')
    sections = {text(s.h2): s for s in main.find_all('section') if s.h2}
    street = sections['Street access near venues']
    date_note = next(text(p) for p in street.find_all('p') if 'Snapshot from' in text(p))
    snapshot, updated = re.findall(r'\d{4}-\d{2}-\d{2}', date_note)
    provenance = dict(source_url=SOURCE, retrieved_at_utc=retrieved_at)
    venues = []
    for row in street.select('tbody tr'):
        header = row.find('th')
        cells = row.find_all('td')
        name = ''.join(str(t) for t in header.find_all(string=True, recursive=False)).strip()
        venues.append(dict(venue=name, street_miles=float(text(cells[0])),
                           corners_with_ramp=int(text(cells[1]).replace(',', '')),
                           corners_missing_ramp=int(text(cells[2]).replace(',', '')),
                           share_missing_percent=float(text(cells[3]).replace('%', '').replace(' ', '')),
                           coverage_note=text(header.find('span')),
                           source_snapshot_date=snapshot, streetsla_updated_date=updated,
                           **provenance))
    metrics = [dict(metric=text(d.dt), value=float(text(d.dd).replace(',', '')),
                    source_snapshot_date=snapshot, **provenance) for d in street.select('dl > div')]
    barriers = []
    for li in sections['Access barriers the city tagged for LA28'].select('li'):
        spans = li.find_all('span', recursive=False)
        detail = text(spans[1])
        council, logged = re.search(r'Council District (\d+) · logged (\d{4}-\d{2}-\d{2})', detail).groups()
        ramp = re.search(r'(\d+) curb ramp', detail)
        requests = re.search(r'(\d+) requests', detail)
        barriers.append(dict(category=text(li.find_previous('h3')), location=text(spans[0]),
                             council_district=int(council), logged_date=logged,
                             curb_ramps_noted=int(ramp[1]) if ramp else None,
                             requests_noted=int(requests[1]) if requests else None,
                             details=detail, **provenance))
    resources = []
    for heading in ['Previous Games resources', 'LA28 & local resources']:
        for a in sections[heading].select('a'):
            spans = a.find_all('span', recursive=False)
            review = re.search(r'Reviewed\s+(\d{4}-\d{2}-\d{2})', text(a))
            resources.append(dict(category=heading, publisher=text(a.select_one('div span')),
                                  title=text(spans[0]), description=text(spans[1]),
                                  url=urljoin(SOURCE, a['href']), reviewed_date=review[1] if review else None,
                                  ai_fetched='AI fetched' in text(a), **provenance))
    technologies = []
    for li in sections['Organizer technology map'].select('ol > li'):
        ps = li.find_all('p', recursive=False)
        technologies.append(dict(step=int(text(ps[0])), purpose=text(ps[1]), title=text(li.h3),
                                 description=text(ps[2]), publisher=text(li.a), url=li.a['href'], **provenance))
    notes = []
    for heading in ['Venue conversion', 'Accessibility across the Games', 'Security & workforce',
                    'Fieldwork questions', 'Research questions for LA28']:
        for i, li in enumerate(sections[heading].select('li'), 1):
            value = text(li)
            if heading in ['Venue conversion', 'Accessibility across the Games', 'Security & workforce']:
                value = re.sub(r'^\d{2}\s+', '', value)
            notes.append(dict(section=heading, sequence=i, text=value, **provenance))
    links = []
    for a in main.select('a[href]'):
        previous = a.find_previous('h2')
        links.append(dict(section=text(previous), label=text(a), url=urljoin(SOURCE, a['href']), **provenance))
    section_text = [dict(heading=heading, text=text(sec), **provenance) for heading, sec in sections.items()]
    caveats = [text(li) for li in street.select('ul.list-disc li')]
    data = dict(metadata=dict(**provenance, title=text(soup.title),
                             source_html_sha256=hashlib.sha256(html).hexdigest(),
                             source_snapshot_date=snapshot, streetsla_updated_date=updated,
                             scope='Single-page snapshot; linked datasets and articles were not crawled.',
                             caveats=caveats),
                venue_curb_ramps=venues, summary_metrics=metrics, access_barriers=barriers,
                resources=resources, organizer_technologies=technologies,
                planning_notes=notes, links=links, sections=section_text)
    validate(data)
    return data, main.get_text('\n', strip=True)


def validate(data):
    venues = data['venue_curb_ramps']
    if not venues or not data['access_barriers']:
        raise ValueError('Expected venue and barrier data is missing')
    metrics = {r['metric']: r['value'] for r in data['summary_metrics']}
    assert sum(r['corners_with_ramp'] for r in venues) == metrics['Corners with a curb ramp']
    assert sum(r['corners_missing_ramp'] for r in venues) == metrics['Corners without a ramp']
    assert sum(r['corners_with_ramp'] + r['corners_missing_ramp'] for r in venues) == metrics['Corners in the city inventory']
    for row in venues:
        assert row['share_missing_percent'] == round(100 * row['corners_missing_ramp'] / (row['corners_with_ramp'] + row['corners_missing_ramp']), 1)
    assert len({r['location'] for r in data['access_barriers']}) == len(data['access_barriers'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/paralympics'))
    parser.add_argument('--html', type=Path, help='Parse an existing HTML snapshot instead of fetching')
    args = parser.parse_args()
    retrieved_at = datetime.now(timezone.utc).isoformat()
    if args.html:
        html = args.html.read_bytes()
        retrieved_at = datetime.fromtimestamp(args.html.stat().st_mtime, timezone.utc).isoformat()
    else:
        with urlopen(Request(SOURCE, headers={'User-Agent': 'LA28ParalympicsDataset/1.0'}), timeout=60) as response:
            html = response.read()
    data, page_text = extract(html, retrieved_at)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'dataset.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for key, rows in data.items():
        if key in ['metadata', 'sections']:
            continue
        with (args.output / f'{key}.csv').open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (args.output / 'page_text.txt').write_text(page_text + '\n', encoding='utf-8')
    # Publish content only; page scripts and framework metadata can contain tokens.
    snapshot = BeautifulSoup(html, 'html.parser')
    content = snapshot.find('main')
    for tag in content.select('script, style, svg'):
        tag.decompose()
    for tag in [content, *content.find_all(True)]:
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in {'href', 'id', 'scope', 'colspan', 'rowspan', 'class'}}
    (args.output / 'source.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>'
        + data['metadata']['title'] + '</title></head><body>' + str(content)
        + '</body></html>\n', encoding='utf-8')
    print(json.dumps({k: len(v) for k, v in data.items() if isinstance(v, list)}, indent=2))


if __name__ == '__main__':
    main()
