# Coliseum model requirements and scope

Revision date: 2026-11-27. Captures the user feedback and authorized scope from the model/CAD discussion. These are product hypotheses; implementation checks do not establish user acceptance or physical venue accuracy.

MVP: touch-first exploration, with no photo collection. Third-person means overhead orthographic map, with no avatar. Geometry inputs use meters. Native engineering reference files prioritize DXF; STEP is explicitly excluded.

Retired IDs: UR-3D-02, UR-3D-03, UR-3D-04, SR-3D-05, SR-3D-08, SR-3D-09. Public measurement, source inspection and cutaway tooling are not required; engineering provenance remains internal.

## User requirements

| ID | Req. | Reason | Date | Status |
| --- | --- | --- | --- | --- |
| UR-3D-01 | Users should be able to explore in first-person and in a third-person overhead orthographic view. | Support venue exploration and spatial orientation. | 2026-11-27 | Implemented in MVP 0.2; physical-phone testing pending |
| UR-3D-05 | Users should eventually be able to contribute phone photographs that help correct inaccurate areas. | Improve the venue model with new observations. | 2026-11-27 | Deferred beyond MVP |
| UR-3D-06 | Developers should be able to reuse the spatial model for additional applications. | Provide a common foundation for future features. | 2026-11-27 | GLB, source and metadata delivered; integration-specific checks remain |
| UR-3D-07 | Users should experience recognizable layout and structural proportions corresponding to the physical venue. | Make exploration useful for understanding the real venue. | 2026-11-27 | Prototype feedback supports scale; physical accuracy unverified |

## System requirements

| ID | Req. | Reason | Date | Status |
| --- | --- | --- | --- | --- |
| SR-3D-01 | Each revision shall identify its represented configuration, references, coverage and omissions. | Keep source evidence and model scope traceable. | 2026-11-27 | Implemented in model metadata and CAD R001 |
| SR-3D-02 | Use metre-based project inputs and document units, origin, axis directions and import/export transforms. | Keep model placement and file exchange consistent. | 2026-11-27 | Implemented; FCStd internal mm and IFC/GLB transforms checked |
| SR-3D-03 | Give each modeled component a stable ID linked to dimensions, evidence or assumptions. | Support correction and reuse of individual components. | 2026-11-27 | Implemented in app groups and CAD/IFC/GLB properties |
| SR-3D-04 | Store dimension and placement inputs separately from viewer code. | Permit geometry corrections without rewriting navigation. | 2026-11-27 | Implemented in JSON inputs and generation scripts |
| SR-3D-06 | Provide first-person joystick/swipe exploration and an overhead orthographic map with pan, zoom and reset. | Support touch-first use and desktop fallback. | 2026-11-27 | Implemented in MVP 0.2; input/math tests passed, phone runtime unverified |
| SR-3D-07 | Provide controls for relevant scene-layer visibility. | Allow users to simplify their view. | 2026-11-27 | Implemented for seating and map labels |
| SR-3D-10 | Target physical positional error within 0.30 m for agreed features and record unverified coverage and exceptions. | Make the desired reconstruction accuracy explicit. | 2026-11-27 | Unverified; current checks establish source consistency only |
| SR-3D-11 | Record versioned inputs, generation instructions, generator version and changes to reproduce geometry. | Support repeatable engineering revisions. | 2026-11-27 | Implemented for viewer and CAD reference; binary timestamps may differ |
| SR-3D-12 | Release reusable GLB geometry and metadata and verify units and ID mapping across export/import. | Support application reuse. | 2026-11-27 | Implemented and checked for viewer export and CAD-derived GLB |
| SR-3D-13 | Constrain walking to modeled traversable surfaces and supported solid barriers. | Make movement coherent with represented geometry. | 2026-11-27 | Implemented with simplified collision; decorative seats/trees are not barriers |
| SR-3D-14 | Accept phone photographs associated with a venue and identified or estimated model location. | Connect future observations with affected geometry. | 2026-11-27 | Deferred beyond MVP |
| SR-3D-15 | Generate candidate photo corrections and validate evidence before a versioned geometry update. | Avoid geometry changes from insufficient evidence. | 2026-11-27 | Deferred beyond MVP |
| SR-3D-16 | Eventually accept standardized component definitions, dimensions, placements, relationships and metadata for multiple venues. | Generalize the model-generation engine. | 2026-11-27 | Deferred; current generators are Coliseum-specific |
| SR-3D-17 | Deliver meter-based native-dimension DXF drawings and IFC/FCStd reference files, with a CAD-derived GLB. | Enable engineering inspection and future reference work. | 2026-11-27 | Implemented in reference package R001; STEP excluded by user request |
| SR-3D-18 | Distinguish source evidence, reconstruction accuracy targets and construction tolerances in engineering files. | Prevent approximate reconstruction geometry from becoming a construction specification. | 2026-11-27 | Implemented in drawing notes, control register and standards guide |

Engineering files: [CAD R001](../../research/coliseum-cad/README.md). Application source: [MVP 0.2](../../apps/coliseum-mvp/README.md). Earlier wayfinding requirements remain separate in [their original register](../coliseum-wayfinding/requirements-analysis.md).
