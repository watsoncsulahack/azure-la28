# Coliseum evidence milestone — 2026-11-27 (Los Angeles)

**Readiness: suitable as an exploration prototype and research baseline; not validated for physical, accessibility or crowd simulations.** The 0.30 m target is provisional. No complete physical feature has been accepted against it.

**Native acquisition follow-up:** both original LAZ tiles are now fully downloaded and decoded (29,118,711 points), and their embedded EPSG:6340 / EPSG:5703 NAVD88-Geoid18 CRS is verified. See the [follow-up record](../../../research/coliseum-geospatial/evidence/NATIVE_LAZ_FOLLOWUP.md). The initial milestone findings below remain a historical snapshot; native acquisition/CRS confirmation is resolved, while model registration and physical acceptance remain open.

This iteration starts from `main` **a56ec755e188494fd935c0ac62bf9f817aedc9cd**, integrates the reviewed contents of PRs [#1](https://github.com/watsoncsulahack/azure-la28/pull/1) and [#2](https://github.com/watsoncsulahack/azure-la28/pull/2) on the engineering branch, and executes acquisition and analysis. The original PRs are not remotely merged by this work. Their old acquisition/audit reports remain historical records.

| Deliverable | Result |
| --- | --- |
| A — downloaded source inventory | [Inventory and reproduction](../../../research/coliseum-geospatial/evidence/README.md), with exact requests and SHA-256 for every cached upstream file |
| B — traceability | [35 parameter/level rows](parameter-traceability.csv), [640 actual meshes](component-traceability.csv), and [generator literal review](generator-constants.csv) |
| C — discrepancies | [Register](discrepancy-register.csv), including unresolved field/bowl boundaries, estimated circulation and new DEM/classification findings |
| D — validation | [Engineering assessment](geometry-validation.md), [13/13 transcription checks](transcription-validation.json), [actual model diagnostics](model-diagnostics.json), existing and rebuilt CAD validation |
| E — model updates | Validation output now exposes unresolved boundaries and provisional acceptance policy. Geometry inputs and all GLB/CAD shapes are preserved. Source package regenerated. No unsupported dimension correction or geographic placement is adopted. |
| F — next iteration | Priorities below and [pending requirement change](SR-3D-10-change-proposal.md) |

## Acquired and inspected

- **USGS 2023–24 EPT:** all 283 intersecting octree nodes at all depths; **8,111,630 points** in the study rectangle. Raw LAZ nodes, metadata and hierarchy pages are cached. Native full-tile LAZ transfer did not complete; a header probe returned **HTTP 429**, so that attempt stopped. EPT extraction succeeded independently.
- **County 2020 distribution:** **145 intersecting features** (143 buildings, two courtyards). Feature vintages: 101 from 2008, five from 2014, six from 2017, 33 from 2020. The principal stadium polygon and courtyard are **2008 / LARIAC2 / Unchanged** records. They are not post-renovation tower controls.
- **USGS B23 1 m DEM:** complete **351,851,429-byte** source tile, plus a **784 × 686** cell crop. The 0.5 m NOAA source remains a metadata lead; it was not downloaded.
- Official Draft 2024 Guide and NPS nomination were downloaded again. Both SHA-256 hashes exactly match the existing source register. The original source controls remain distinguishable from observations and design inferences.

The EPT declares **EPSG:3857** horizontally; original work-unit documentation declares **EPSG:6340**, **NAVD88 / GEOID18**. The terrain tile declares **EPSG:26911**. These are recorded separately. EPT vertical CRS is absent. Native vertical-CRS confirmation and accepted site control remain outstanding.

## Most consequential findings

1. The elliptical field mesh has **10,213.40 m²** of triangulated top surface (analytic ellipse: **10,215.22 m²**), compared with the guide's **12,619.67 m²** playing-field area. The old county courtyard is **12,472.43 m²**, but its boundary and vintage differ. These are three distinct boundaries; there is no justified area-forcing correction.
2. A candidate pose derived from the old county courtyard permits diagnostic comparisons. Across **28,558 observed 1 m bowl cells**, observed-minus-generated terrace height has median **−6.61 m**, RMSE **7.25 m**, and P95 absolute **10.93 m**. This flags the uniform profile for investigation. It is **not** an accepted 3D positional error: pose is provisional, returns include seats/fixtures, and the metric is vertical height difference.
3. A west field-interior patch fits the vertical translation; the disjoint east patch has **12,716 withheld returns**, RMSE **0.027 m**, P95 absolute **0.050 m**, maximum absolute **0.100 m**. This supports exposed interior flatness only. It does not validate absolute field elevation, edges, geographic pose, or the whole field.
4. The DEM is about **11.25 m above** those field observations. Exterior class-2 points have median absolute DEM difference **0.0085 m** and P95 **0.0438 m**. Local interpolation across the excavated field is a plausible explanation; a global datum correction is not justified. **Do not use this DEM to set field elevation.**
5. Only classes 1, 2, 7 and 18 occur in the extracted cloud. The sampled field is class 1. There is no building/seat/walking-surface semantic inventory here. Occupied 2D cells do not observe hidden circulation or certify access.

## Next work, in order

1. Obtain current horizontal control with recognizable field/perimeter endpoints and a NAVD88 benchmark. Retain independent holdouts. Confirm native LAZ CRS after server throttling clears. PROJ currently reports nominal **2 m** accuracy for WGS84/EPT-to-NAD83(2011) operations; this is not adequate evidence for a 0.30 m acceptance claim.
2. Resolve the field boundary using the official dimension lines/current field plan, matching county/scan endpoints explicitly. Reconcile the historic overall shell with the partial modeled bowl and current roof line. Do not scale either to force a match.
3. Extract multiple observed bowl sections and a tower roof/footprint from the point cloud in the accepted frame. Separate seat tops from walking surfaces, mask occlusions, and fit profiles with spatial holdouts. The multi-meter conditional bowl differences make this more consequential than façade work.
4. Review bare-earth classification locally and acquire the 0.5 m DEM if useful for exterior terrain. Retain field observations separately; finer raster cells alone will not fix a ground-class exclusion.
5. Acquire current as-built tower sections and a pedestrian survey of entrances, landings, ramp slopes/cross-slopes, clear widths, stair flights, doors and lift endpoints. Under-stand geometry remains unobserved. Keep all present routes and A009 connectors marked as schematic.
6. Approve feature/use-specific tolerances and a coverage/exception policy through the requirement change record before any physical acceptance. Permanent infrastructure and temporary event overlays must remain separate.

Reproduce the parameter/model audit with `python analysis/coliseum-model/evidence-iteration/build_traceability.py` and `npm --prefix apps/coliseum-mvp run check:evidence`. Acquisition and point-cloud analysis commands are in the linked source inventory guide. Nothing in these reports establishes an accessible route or a calibrated crowd-flow domain.
