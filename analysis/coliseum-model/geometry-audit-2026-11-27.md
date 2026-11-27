# Coliseum 3D MVP 0.2 — initial geometry audit

**Audit:** 2026-11-27 · **Model:** `0.2.0` · **Baseline:** `main` commit `a56ec755e`

**Decision:** **Source-parameter consistency passes; physical accuracy is unverified.** Do not claim compliance with SR-3D-10 (≤0.30 m positional error) yet.

## What was actually tested

1. Inspected live GitHub `requirements.csv`, `venue.json`, `model.js` and `validation.json`, with blob SHAs recorded in [the machine-readable audit](geometry-audit-2026-11-27.json).
2. Independently converted the original values in the cited primary documents from feet/inches to meters and compared **13 source-related parameter inputs**; **13/13 numeric matches**, to 0.005 m. Historic approximate references count as **transcription matches only**, not modern physical-survey passes.
3. Inspected the current generator's field shape, 80-band seating interpolation, schematic exterior stairs and explicit exclusion of the historic-length check.
4. Reviewed the checked-in `validation.json`: **12/12 reported model-generator checks passing**. These are the project's existing test results; **the complete binary GLB was not retrieved here and these specific mesh tests were not independently re-executed**.
5. Independently computed the field plan-area and bowl-span diagnostics below. Small calculation tests were executed separately.

## Measurements that match the published specification numerically

| Published constraint | Model input | Evidence/status |
| --- | ---: | --- |
| Field east-west 560 ft | **170.6880 m** | MATCH input; model-generated X extent reports a match |
| Field max north-south 250 ft | **76.2000 m** | MATCH maximum; guide also reports **222 ft** minimum at unspecified location |
| Football 360 × 160 ft | **109.728 × 48.768 m** | MATCH inputs and existing source-consistency checks |
| Field → street 40 ft 9 in | **12.4206 m** | MATCH relative height |
| Field → last row 115 ft 8 in | **35.2552 m** | MATCH relative height |
| Street → last row 74 ft 11 in | **22.8346 m** | MATCH derived relative height |
| Street → Scholarship Tower top 109 ft 4 in | **33.3248 m** | MATCH relative height; exact top endpoint ambiguous |
| Street → cauldron top 123 ft 6 in | **37.6428 m** | MATCH relative height; endpoint ambiguous |
| West screen face 150 ft 3 in × 39 ft 11 in | **45.7962 × 12.1666 m** | MATCH dimensions; placement remains estimated |
| Historic bowl 1,038 × 738 ft | **316.3824 × 224.9424 m** | MATCH *historic approximate input*, not post-2019 measured envelope |

The current guide indicates fifteen peristyle arches; the project's existing validation reports 15. This is a **reported generator check**, not a physically measured profile for each arch.

## Open geometry findings (must not be counted as passed real-world tolerances)

### G-01 — Playing-field plan-area discrepancy (REVIEW)

`model.js` constructs the `field-envelope` as an ellipse with full spans 170.688 × 76.2 m. Thus its plan area is **10215.22 m²**. The official Draft 2024 Technical Guide (printed page 6) lists **135,837 ft² = 12619.67 m²** as *Playing Field* area. The difference is **-2404.45 m² (-19.05%)**.

**Interpretation:** The guide does not establish the exact polygon boundary used for its area label, so this is an **unresolved footprint-definition discrepancy**, not a proven 19% real-world model error. The model's ellipse should not be treated as a surveyed as-built polygon.

### G-02 — Bowl component span and omitted historic check (REVIEW)

The checked-in `validation.json` gives bowl-group X bounds `-158.1912` to `139.5122` m, a modeled group span of **297.703 m**, compared with **316.382 m** nominal historic envelope (about **18.679 m** difference). The source contains a `historic-provisional-envelope-length` test, but explicitly **filters it out** before reporting checks.

**Interpretation:** The bowl group omits part of the east opening and is not necessarily the same boundary as the complete 1984 stadium ellipse. Establish component and survey endpoints before calling this a dimensional failure. The omitted check should remain **not validated**, rather than silently passed.

### G-03 — Uniform simulated seating levels (ESTIMATED)

The source generates **80** uniform terrace bands over 35.2552 m: **0.44069 m** of rise per visual band. These are not independently surveyed row risers and must not be used as physical stair or wheelchair-routing measurements.

### G-04 — Schematic exterior stair connections (ESTIMATED)

The source places exterior-to-rim stair connectors over **37.2 m horizontal run** and **22.8346 m elevation change**. The geometry generator creates **109** steps (about **0.209 m** rise per step) without independently verified location, landings, or route connectivity. Appropriate only as exploration scenery for now.

### G-05 — Physical tolerance: SR-3D-10 (NOT VERIFIED)

The model's local frame is **not georeferenced** and the reported independent physical checks count is **0**. No independent LiDAR/survey residual measurements, confidence intervals, coverage masks or holdout control points exist in the current validation. Therefore **≤0.30 m cannot be certified**.

## Recommended correction order

**P0:** Reconcile the real field boundary and published area; establish independent geographic coordinates and vertical datum; acquire post-2019 LiDAR and report point-to-surface residuals.

**P1:** Validate the outer bowl and tower footprint to current physical observations; replace estimated row/riser shapes and connecting stairs only where surveyed; keep inaccessible/unknown regions explicitly marked.

**P2:** Add mesh coverage, collision and route-connectivity checks once the independent geometry layer exists.

## Requirements mapping

- **SR-3D-01/02/03/04/11/12/17/18:** Baseline supports these via provenance, meter-based inputs, stable component IDs and exported references, subject to individual tests.
- **SR-3D-10:** **NOT VERIFIED.** Requires an independently measured current geographic reference; cannot be passed by source-to-source conversions.
- **SR-3D-13:** Simplified traversal is implemented, but physically correct stairs, obstructions and real-world accessibility are not demonstrated.
- **UR-3D-07:** Recognizable prototype proportions are not evidence of real-world accuracy.

## Authoritative sources and scope

- Coliseum [Draft 2024 Technical Guide](https://www.lacoliseum.com/wp-content/uploads/2024/12/Coliseum_Technical_Guide_Draft2024.pdf) — printed pages 6, 19 and 41 (area, dimensions, displays).
- [1984 National Historic Landmark nomination](https://npgallery.nps.gov/NRHP/GetAsset/NHLS/84003866_text) — PDF page 2 (historic *approximate* bowl geometry and arches).
- [Model input](../../apps/coliseum-mvp/dist/data/venue.json) · [Generator](../../apps/coliseum-mvp/dist/model.js) · [Existing generated validation](../../apps/coliseum-mvp/dist/data/validation.json) · [Current requirements](requirements.csv).

**Scope limitation:** The GitHub connection returned source files but not readable binary `.glb` content. The report uses inspected generator code, project-reported component bounding boxes and independently recalculated constraints; it does not claim full independent binary mesh, device, photogrammetric or physical-site validation.
