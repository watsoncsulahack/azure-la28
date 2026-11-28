# Geometry and evidence release assessment — MVP 0.3.0

Date: 2026-11-27 (Los Angeles). **Preview implementation on branch** `feature/coliseum-mvp-0.3.0-evidence-overlay`.

## Implemented

| Area | 0.2.0 | 0.3.0 | Evidence category |
|---|---|---|---|
| Stadium shell, field, bowl, tower | Procedural, dimensions from guide, many estimated | **Same underlying geometry** | No new physical mesh acceptance |
| External road context | Schematic non-geographic roads | **10 authentic municipal street centerlines**, visual-only | GIS records, local transform candidate |
| Curb ramps | No surveyed overlay | **20 inventoried ramp points**, creation year 2017 | Historic administrative inventory, not accessibility inspection |
| Stadium perimeter comparison | Historic approximate ellipsoid | **Additional 2008 county polygon bounding rectangle** | Legacy geospatial bounding box, not current 2026 perimeter |
| Coordinate frame | No geographic references | **Provisional registration metadata**, human-inspectable | Unapproved 2008 courtyard-based fit |
| Source provenance | Architectural dimensions | Existing source reference IDs + GIS feature IDs, SHA source identifiers | Documentary |
| Physical accuracy | Not verified | **Still not verified** | No new physical validation test |

**Validation conclusion: 0.3.0 is geographically better-informed, but it is not demonstrated to be geometrically more accurate.** The source-derived 2023–24 survey includes more than 8.1 million study-area point observations; however, only their reports and provenance survive in this GitHub checkout. Those aggregate statistics are insufficient to regenerate the detailed seating-bowl mesh or a terrain surface. The raw files were not committed by Codex and were unavailable to this iteration.

## Implementation checks

The evidence overlay has been executed in a mocked Three.js scene using the actual new GIS JSON: 10 line objects, 20 point objects and one historic rectangle; all flagged as non-traversable. JavaScript syntax was checked independently. **Full browser rendering, node package integration tests and native GLB export were not executed in this session**. Do not mistake source integration for production device acceptance.

## Geometry next steps

1. Restore the exact cached USGS source LAZ/derived NPZ files using `research/coliseum-geospatial/evidence/README.md` or export compact accepted surface samples to version control with hashes and clear licensing.
2. Fit horizontal/vertical registration against *current identifiable* surveyed control points; verify the candidate pose before promoting legacy county geometry.
3. Extract measured cross sections of bowl terraces and tower/peristyle from observed current LiDAR; classify actual seat tops and walking surfaces separately; retain an occlusion mask.
4. Derive a new constrained bowl profile only from station-specific samples, using geographically withheld test sections. Rebuild GLB and CAD when acceptable source geometry exists.
5. Treat pedestrian paths, curb ramps, interior floors and temporary LA28 features as unverified until a separate access/topology survey is available.

The earlier conditional vertical bowl RMSE of **7.25 m** is a diagnostic under a provisional pose, not a reliable physical error measurement and not a correction offset.

## Release/asset limitations

`dist/coliseum-0.2.0.glb` is **intentionally retained as a base geometry asset**. The interactive 0.3.0 scene dynamically composes the base procedural geometry with source-derived GIS overlays. There is **no falsely named 0.3.0 binary GLB** and no raw LiDAR mesh in this branch.

Change review is required before merging. Source attribution and existing license conditions remain unchanged.
