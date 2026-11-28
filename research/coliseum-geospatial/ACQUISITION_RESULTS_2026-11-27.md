# Coliseum geospatial acquisition and relevance assessment

Verified November 27, 2026 against the repository's original raw ArcGIS GeoJSON batches. This report distinguishes **actually extracted data** from **sources only identified for future downloading**.

## Actual extraction completed

Approximate study rectangle (EPSG:4326): longitude -118.2923 to -118.2839, latitude 34.0109 to 34.0170. This rectangle is a working spatial filter, not a surveyed Coliseum site boundary.

| Dataset | Original committed records examined | AOI records saved | New output |
| --- | ---: | ---: | --- |
| Curb-ramp inventory | 3,704 point features across 38 source batches | **20** | [curb_ramps_aoi.geojson](data/curb_ramps_aoi.geojson) |
| Olympic-area street segments | 1,418 line features across 15 source batches | **10** | [street_segments_aoi.geojson](data/street_segments_aoi.geojson) |

The 20 curb-ramp source attributes have `HASRAMP = Yes` and `CRTN_DT` dates in **2017**. This does **not** establish current physical condition, ADA compliance, or that there are no missing ramps elsewhere. In particular, source points are drawn from the original inventoried layer and a filtered source population, not a fresh street inspection. The values preserve the source point coordinates and attribute data in EPSG:4326.

The 10 selected road-centerline segments all have `VENUE_NAME = LA MEMORIAL COLISEUM`. Street-name counts: **Martin Luther King Jr. Boulevard = 3**, **Hoover Street = 1**, **Vermont Avenue = 6**. Source-reported `ST_Width` values are 56, 72 and 74 (source units/meaning should be verified from layer metadata). Not all source street widths define walkable pavement. The ten are **centerline-based street records, not detailed sidewalks**, and the selection rule includes any line that intersects the study rectangle, even if its endpoints are outside.

Original upstream repository data:
- [Raw GIS batch directory](../../datasets/paralympics/2026-11-27/raw)
- [Dataset manifest](../../datasets/paralympics/2026-11-27/manifest.json)
- [Requirements](../../analysis/coliseum-wayfinding/requirements-analysis.md)

## Engineering relevance to existing wayfinding requirements

| Requirement | Extract contribution | Verification still required |
| --- | --- | --- |
| UR-02 / SR-05 — route suited for mobility devices / step-free path exclusion | Ramp-location *candidates* for fieldwork and spatial registration | Actual ramp location, current condition, gradient, landing, clear width, cross-slope, connectivity and surrounding obstacles |
| SR-06 — route metrics including grade and distance | Street centerlines provide rough exterior context | Verified pedestrian alignment, distance in local projected CRS, and actual 3D grade |
| SR-09 — first-person 3D arrows | Exterior GIS may anchor reference landmarks after survey registration | Camera/world alignment, obstacle geometry, current entrances, interior topology |
| UR-04 — quieter or shadier route | None: records have no validated noise/shade measurements | Time-varying shade model and independently sampled acoustics |

**Do not promote these 20 ramp records into an automatically certified accessible pedestrian graph.** The existing Three.js route graph is procedural/demo geometry, not survey-grade Coliseum data.

## Highest priority yet to acquire

1. **USGS 2023–24 QL1 airborne LiDAR, CA_LosAngeles_1_B23:** candidate survey for post-renovation surface geometry. EPT URL in [source_catalog.csv](source_catalog.csv). **Not downloaded or spatially inspected** here due to network/DNS restrictions.
2. **USGS/NOAA post-renovation 0.5m bare-earth DEM:** candidate local ground reference. **Not downloaded**.
3. **LARIAC6 2020 county building polygons:** candidate footprint and coarse surrounding massing. **Not downloaded** because the live ArcGIS service could not be reached from this execution environment.
4. **2015–16 LiDAR:** pre-renovation historical comparator, not a present-day source of tower and seating geometry. **Not downloaded**.

No new LAZ, GeoTIFF, or building polygons should be claimed as incorporated until actual files have been retrieved, inspected, spatially bounded to the Coliseum, checked for coordinate/vertical reference systems, and independently tested against architectural measurements.

## Priorities for a simulation-grade model

**P0: Survey-grade control and current surface geometry.** USGS point clouds + vertical datum reconciliation + current tower and field elevations; retain measurable error and missing-surface masks.

**P1: Physical traversability.** Audited pedestrian centerlines, actual clear widths, stair runs, slopes, curb ramps, doors, landing surfaces, connected concourses and lift endpoints. These are more important to accessibility routing than façade textures.

**P2: Event-time operational overlays.** Temporary fences/closures, queuing, one-way entry, congestion, elevator outages and event route plans. Keep separate from permanent infrastructure.

For each geometry element keep `source_id`, `capture_date`, `horizontal_crs`, `vertical_datum`, `observation_or_inference`, `accuracy_or_uncertainty`, `geometry_epoch` and a pass/fail validation status. Use separate temporal layers rather than merging the 2016 and 2023 point clouds as though they represent the same building.
