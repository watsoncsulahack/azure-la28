# LA28 Paralympic page dataset

Source: https://la28-planning-hub.lovable.app/paralympics
Collected: 2026-11-27T09:30:03.273835+00:00
Page's own snapshot: 2026-11-23; stated StreetsLA venue dataset update: 2025-02-05.

## Contents
- `page_content.json`, `page_text.txt`, `raw/page.html`: the complete delivered main-page content, headings, prose, questions, citations and caveats. HTML is retained losslessly.
- `venues.csv`: 9 venue-area summaries. These are city-listed LA28 venues, not a confirmed Paralympic venue list.
- `barrier_sites.csv`: 19 grouped sites reported by the page.
- `summary_metrics.csv`: page-reported summary figures.
- `section_content.csv`, `planning_notes.csv`: spreadsheet-friendly section text and list items, including fieldwork and research questions.
- `organizer_technology.csv` / `.json`: four teaching-map examples and their source URLs.
- `resources.csv`: 20 resource cards, including descriptions and page review metadata. `page_links.csv` includes every link in main content.
- `curb_ramps.csv` / `.geojson`: 3704 public city corner/ramp records.
- `city_venue_points.csv` / `.geojson`: 21 raw venue points, preserved as-is rather than forced to the page's 20-venue count.
- `street_segments.csv` / `.geojson`: 1418 street records with full line geometry in GeoJSON.
- `live_barrier_points.csv` / `.geojson`: 20 raw city records tagged `isLA28=1`, versus 19 grouped page sites. Do not join these positionally.
- `manifest.json`: request URLs, timestamps, SHA-256 checksums, record counts, completeness checks.
- `validation.json`, `data_dictionary.json`, and `raw/*_metadata.json`: checks and field definitions, including official coded-value domains.

## Important limitations
This is accessibility inventory, not observed street traffic, travel times, or a validated routing network. No safe or step-free route is established. Ramp existence does not establish ADA compliance, slope, surface condition, continuity, or current access. Venue buffers can overlap; do not assume all per-venue totals represent distinct physical corners. Source IDs are retained for later spatial checks. City datasets and page snapshot are separate observations collected on different dates; discrepancies are retained, not silently reconciled. Zero ramps noted in a barrier request is not proof that a site has no ramp. The full source-backed route graph still requires crossings, connectivity, transit access and current field verification.

Record-count reconciliation: the city has two records for `900 GAYLEY AVE` (one with trailing whitespace), while the page groups them as one site with two requests. Case/whitespace-normalized city addresses total 19. There are two venue point records named `SEPULVEDA BASIN SPORTS COMPLEX`, yielding 20 distinct normalized venue names from 21 points. Both point records are retained.

Page caveats:
- City of Los Angeles streets only. Venues in Inglewood, Long Beach, Pasadena, Carson, Anaheim, and other cities have little or no data here.
- A corner marked as having a ramp is not a check of ADA compliance, slope, or condition.
- Ramp points come from the city's 2017 sidewalk inventory, traced from 2014 aerial photos.
- The venue list is the city's unofficial, subject-to-change LA28 list, not the current LA28 Games Plan.
- The city is building a newer LiDAR sidewalk assessment for LA28 sites. It is not public yet.

The page is an independent educational project, not an official LA28 publication. Its claims and external articles have not been independently verified. Blank license/attribution fields in a source item are not a license grant; confirm reuse terms before redistribution.

## Reproduce
Run `python ../collect.py --output /path/to/new-directory` from this snapshot directory. Requires Python 3, lxml, and HTTPS access to the page and the directly cited city/ArcGIS hosts. No tokens or secrets are used. The output directory must not exist. TLS verification stays enabled. The scraper fails if data literals or schemas change, rather than evaluating website JavaScript. ArcGIS IDs are paged in batches of 100 to stay within server URL limits and checked for omissions and duplicates.
