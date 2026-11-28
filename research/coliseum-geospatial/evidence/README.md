# Acquired Coliseum geospatial evidence

Acquired 2026-11-27 Los Angeles time (some UTC timestamps fall on November 28). See [engineering assessment](../../../analysis/coliseum-model/evidence-iteration/README.md) for model implications.

## Inventory and storage

[source-inventory.json](source-inventory.json) records each cached upstream object: exact request URL, acquisition timestamp (or explicitly labeled file-mtime proxy for initial exploratory downloads), byte size and SHA-256. HTTP ETag/Last-Modified/Date are retained where recorded. Initial retrievals made before the recorder have null unavailable headers/timestamps; they are not fabricated. [Product manifest](products-manifest.json) records derived file hashes, transformations and tool versions.

| Source | Actual result | CRS/units and limitations | Rights |
| --- | --- | --- | --- |
| USGS `CA_LosAngeles_1_B23` EPT | 283 LAZ nodes, all intersecting hierarchy branches at all depths; 8,111,630 cropped points | EPT EPSG:3857, metre X/Y; Z metres with no vertical CRS in EPT. Original project EPSG:6340, NAVD88/GEOID18. No vertical conversion performed. | US federal public-domain elevation data; retain USGS credit/metadata |
| Native current LAZ tiles | Two located by TNM; no complete native file acquired | Full transfer incomplete; header probe HTTP 429. Native vertical-CRS confirmation remains blocked. | USGS |
| County 2020 building distribution | 145 complete intersecting features, 143 Building + 2 Courtyard | REST source EPSG:3857; server exports EPSG:4326. Mixed 2008/2014/2017/2020 feature dates; roof-line outlines. HEIGHT/ELEV units not verified or used as control. | LARIAC / County of Los Angeles / Pictometry / EagleView; [county terms](https://egis-lacounty.hub.arcgis.com/pages/terms-of-use) and item license retained locally; no engineering/survey suitability warranty |
| USGS B23 1 m DEM | Complete 351,851,429-byte tile and 784 × 686 crop | Header EPSG:26911, metres, nodata −999999; project NAVD88/GEOID18. Same survey as point cloud. Large localized field disagreement; no field datum control. | USGS |
| NOAA 0.5 m DEM | Metadata downloaded only | No 0.5 m raster acquired; do not confuse with actual 1 m tile | Source-specific terms need checking on acquisition |
| Official Draft 2024 Guide and NPS 1984 nomination | Actual PDFs downloaded; hashes match prior source catalog | Draft operational dimensions vs historic approximate measurements, not independent modern survey control | Publisher rights retained; research cache only |

`raw/` is an immutable local source cache, currently approximately 974 MiB including a 570 MB work-unit report with extensive appendices. It is deliberately excluded from Git. Do not overwrite cached raw files or commit bulk point clouds/PDFs. `derived/` contains cropped points, terrain, county polygons and coverage/residual arrays, also excluded from Git. These files remain in the task workspace. Small reports and source/product checksum manifests are versioned. Reacquisition with the recorded URLs is required on a fresh checkout; verify hashes before using changed upstream objects. This is a reproducible catalog, not a promise that upstream services will remain byte-identical.

The study rectangle is EPSG:4326 **[−118.2923, 34.0109, −118.2839, 34.0170]**, a spatial filter rather than a surveyed property boundary. County features are retained in full if they intersect it. EPT XY cropping transforms that rectangle to EPSG:3857. Native/terrain metadata and processing reports preserve the coordinate distinctions. PROJ's nominal operation accuracy does not establish site accuracy.

## Reproduce

From repository root, use a local environment (Node 20+ for existing model checks):

```sh
python -m venv --system-site-packages .venv
.venv/bin/pip install -r research/coliseum-geospatial/evidence/requirements.txt
.venv/bin/python research/coliseum-geospatial/evidence/acquire.py metadata
.venv/bin/python research/coliseum-geospatial/evidence/acquire.py buildings
.venv/bin/python research/coliseum-geospatial/evidence/acquire.py lidar
.venv/bin/python research/coliseum-geospatial/evidence/acquire.py dem
.venv/bin/python research/coliseum-geospatial/evidence/analyze.py
.venv/bin/python research/coliseum-geospatial/evidence/acquire.py inventory
.venv/bin/python -m unittest discover research/coliseum-geospatial/tests
python analysis/coliseum-model/evidence-iteration/build_traceability.py
npm --prefix apps/coliseum-mvp run check
npm --prefix apps/coliseum-mvp run check:evidence
.venv/bin/python research/coliseum-geospatial/evidence/finalize.py
```

`native` is an optional additional stage after the host stops throttling. Do not repeatedly retry a 429 response. `all` runs every stage, records failures and continues with unaffected datasets. Downloads have bounded body-read time, atomic completion and explicit failed receipts; missing/duplicate county IDs prevent writing a successful extract. Cached sources are reused. Raw points keep classifications, return numbers and withheld/ClassFlags; unclassified points are not converted into verified ground/walkable surfaces.

`analyze.py` generates the candidate transform, first-return raster, unobserved-cell mask, conditional residuals, county chronology assessment, terrain comparison and figure. Its 1 m observation cells require three first returns; there is no interpolation of holes for validation. The candidate transform is unapproved and is not applied to the game/CAD. Both the fit and all metrics must be rerun if control changes. Column names, masks and sidecar metadata are preserved with the generated arrays.

## Primary metadata

- [USGS original work-unit report](https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/metadata/CA_LosAngeles_B23/CA_LosAngeles_1_B23/reports/LA_County_Report_WU300609.pdf): original datums, acquisition 2023-01-08 through 2024-01-07, classification scheme and project processing/accuracy statements. Project-wide performance is not a Coliseum checkpoint result.
- [USGS acceptance summary](https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/metadata/CA_LosAngeles_B23/CA_LosAngeles_1_B23/reports/USGS_CA_LosAngeles_1_B23_Summary_Report.pdf): QL1, original EPSG:6340/5703, GEOID18 and review limitations.
- [Live EPT metadata](https://s3-us-west-2.amazonaws.com/usgs-lidar-public/CA_LosAngeles_1_B23/ept.json): actual online encoding/CRS, distinct from native delivery metadata.
- [County item](https://www.arcgis.com/home/item.html?id=e6a1e375e12a4fe6849d896a26ec028a): stereo roof-line interpretation, chronology, attribution and license notice.
- [USGS terrain tile catalog](https://www.sciencebase.gov/catalog/item/689bf41fd4be0276bfcb20af): current 1 m tile. Its bytes/header were inspected, not merely discovered.

No dataset here proves pedestrian connectivity, ramp compliance, doorway clearance or present-day event access.
