# LA28 Paralympics planning dataset

Structured snapshot of [LA28 Planning Hub — Paralympics](https://la28-planning-hub.lovable.app/paralympics), an independent educational student project, not an official LA28 publication.

## Data

All files are in [`data/paralympics/`](data/paralympics/).

| File | Records | Contents |
| --- | ---: | --- |
| `venue_curb_ramps.csv` | 9 | Venue, street miles, corners with/missing ramps, share missing, coverage note |
| `access_barriers.csv` | 19 | Location, category, council district, logged date, explicitly noted ramp/request counts |
| `summary_metrics.csv` | 4 | Published page totals |
| `resources.csv` | 20 | Resource titles, publishers, descriptions, URLs, review dates, AI-fetched labels |
| `organizer_technologies.csv` | 4 | Organizer technology teaching examples and citations |
| `planning_notes.csv` | 27 | Planning statements, fieldwork questions, research questions |
| `links.csv` | 31 | Every link in the main page, retaining repeated appearances |
| `dataset.json` | — | All tables, 10 complete section texts, source metadata and caveats |
| `page_text.txt` | — | Main page text in reading order |
| `source.html` | — | Exact retrieved HTML snapshot |

CSV uses UTF-8, a header row, and decimal numbers without thousands separators. JSON contains typed numbers, booleans, and nulls. Missing optional counts are null in JSON and blank in CSV; they do **not** mean zero. Dates use ISO 8601; `retrieved_at_utc` is the scrape time. `source_snapshot_date` (2026-11-23) and `streetsla_updated_date` (2025-02-05) are dates stated on the webpage, not the scrape date. No coordinates were provided or inferred.

Every table row has `source_url` and `retrieved_at_utc`. Metadata includes the SHA-256 of the original HTML. Resource `reviewed_date` and `ai_fetched` values are the website's labels, not independent verification by this scraper. The scrape covers this single page; it does not download linked articles or municipal GIS layers.

## Interpretation

- City of Los Angeles streets only: coverage for other host cities is limited or absent.
- Ramp presence does not establish ADA compliance, usable slope, condition, or an accessible route.
- The page says ramp points derive from a 2017 inventory traced from 2014 aerial photos.
- The venue list is the city's unofficial, subject-to-change list rather than the current official Games Plan.
- The page says a newer LiDAR sidewalk assessment is not yet public.
- Published venue street miles are rounded. Their sum is 126.1 miles. Published corner totals are 3,555 with a ramp, 149 missing, and 3,704 overall.

Statements and source limitations are preserved as published. This is a scrape, not an independent audit. Source content remains subject to its owners' rights; no new license is asserted over third-party content.

## Refresh

Requires Python 3.10+.

```sh
python -m pip install -r requirements.txt
python scripts/scrape_paralympics.py
```

To reproduce the extraction from the committed HTML without a network request:

```sh
python scripts/scrape_paralympics.py --html data/paralympics/source.html --output work/reparsed
```

With `--html`, the input file's modification time supplies the retrieval timestamp; the original committed scrape timestamp remains in `dataset.json`. Parser checks verify nonempty tables, matching corner totals, rounded percentages, and unique barrier locations. Review outputs when the source layout changes; this script deliberately fails if expected sections disappear.
