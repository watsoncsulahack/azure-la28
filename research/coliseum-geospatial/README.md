# Coliseum geospatial evidence pack

**Current status: 2026-11-27 (Los Angeles).** The [executed evidence iteration](evidence/README.md) has acquired and inspected 8,111,630 EPT points, 145 county polygon features and a USGS 1 m terrain tile/crop. It records source checksums, mixed feature vintages, conditional residuals and acquisition exceptions. The [native follow-up](evidence/NATIVE_LAZ_FOLLOWUP.md) also acquired both original LAZ tiles and confirmed their embedded EPSG:6340 / EPSG:5703 CRS. The model is still physically unverified. The original proposal and historical acquisition report below describe the earlier PR workflow; their failed downloads are superseded by the separate executed inventory, not retroactively claimed as successful.

The principal priority is geometric and topological accuracy, **not appearance**. Continue to use [the existing Coliseum dimensions register](../coliseum-dimensions/README.md) for sourced field/street heights and architectural documentation. A draft venue technical guide and older design sheets do not certify a modern as-built survey.

## Sources and their roles

| Source | Geometry | Acquisition vintage | Principal use | Limits |
| --- | --- | --- | --- | --- |
| USGS 3DEP `CA_LosAngeles_1_B23` | Classified LAZ/EPT LiDAR | 2023–24 | Post-2019 exterior/bowl/terrain scan candidate | Stadium-area coverage/density need verification; occlusion and classification error |
| USGS `USGS_LPC_CA_LosAngeles_2016_LAS_2018` | LAZ/EPT LiDAR | 2015–16 | Pre-renovation comparison/change detection | Cannot stand in for 2019 tower geometry |
| USGS/NOAA Los Angeles 0.5 m DEM | Bare-earth raster | 2023–24 | Ground elevation/terrain profile | Removes buildings and cannot represent seats |
| LARIAC6 Countywide Building Outlines | Footprint polygons, possible attributes | 2020 | Coarse perimeter/neighboring massing | Roof outlines are not wall footprints; HEIGHT/ELEV definitions need verification |
| Existing Coliseum dimension register | Plans, sections, dimensions | Mixed | Metric constraints, datum reasoning and geometry holdout tests | Historic / draft / modern values must remain separate |
| Existing project accessibility data | Curb ramps, street segments, barrier points | Mixed | Supplemental routing context | Not a verified accessible pathway survey |

Source URLs and known limitations are in [source_catalog.csv](source_catalog.csv). Check the underlying county distribution terms, USGS metadata, and each individual acquisition's native CRS and vertical datum. A high numerical precision in the stored point coordinates does **not** imply high measurement accuracy.

## Quick start

Run from repository root with Python 3.10 or newer:

```sh
# Inspect the 2020 county spatial request before downloading
python research/coliseum-geospatial/fetch.py fetch-buildings --dry-run

# Download only polygons intersecting the approximate study AOI
python research/coliseum-geospatial/fetch.py fetch-buildings

# Generate LiDAR extraction pipeline descriptions
python research/coliseum-geospatial/fetch.py prepare-lidar

# Requires separately installed PDAL with readers.ept and LAZ support
pdal pipeline research/coliseum-geospatial/pdal_2023.json
pdal pipeline research/coliseum-geospatial/pdal_2016.json

# Inspect coordinate system, classes, bounds and point counts
pdal info research/coliseum-geospatial/derived/usgs_3dep_2023_aoi.laz --summary
```

The `aoi.geojson` polygon is a **working study rectangle**, not a surveyed property or operational security boundary. The extractor requests source polygons intersecting it and retains the complete features; it does **not** geometrically clip partial polygons to its edges. Its GeoJSON download is transformed to EPSG:4326. LiDAR pipelines use EPSG:4326 query bounds; **preserve the true point-cloud spatial reference and vertical reference when integrating with the game engine**. Verify the PDAL version and source EPT service before executing.

Do not commit gigabyte-scale raw clouds, duplicate public datasets, temporary raster products, or generated `derived/` outputs. Archive large source files externally using stable identifiers and record sha256, acquisition timestamps and transformations. Share only resources licensed for redistribution. LA County eGIS terms: https://egis-lacounty.hub.arcgis.com/pages/terms-of-use.

## Source hierarchy for an accurate simulation

1. **Geodetic control:** independently verified points in a consistent horizontal CRS and vertical datum, including uncertainty and survey date.
2. **Terrain:** bare-earth DEM to establish topography and major surface gradients, but not small curbs or stair treads.
3. **Surface geometry:** current classified LiDAR and independently usable photogrammetry for visible exposed surfaces.
4. **Architecture:** official plans and measured sections to resolve occluded geometry; document revisions and assumptions.
5. **Topology/semantics:** entrances, passage edges, elevators, stair flights, slopes, surface materials, crowd capacities, and barriers are separate attributes and cannot be deduced reliably from external LiDAR alone.
6. **Validation:** independent holdout dimensions, registered point-to-mesh residuals, coverage masks, source provenance, and unverified feature flags.

**Model a navigable route only when the actual physical connection is verified.** A geometrically attractive route graph or polygon footprint cannot prove wheelchair access or ADA compliance.

## Model validation deliverables

For each source or derived feature, record `source_id`, `capture_date`, `processing_version`, `horizontal_crs`, `vertical_datum`, `source_accuracy`, `validation_method`, `holdout_residual_m`, `confidence_class`, and `geometry_epoch`. Keep unverified guessed features separated from observations. Do not combine the 2016 and 2023–24 geometry without registration and a temporal-change layer.

Offline tests: `python -m unittest discover research/coliseum-geospatial/tests`.
