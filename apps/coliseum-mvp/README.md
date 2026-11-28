# Coliseum MVP 0.3.0 — Evidence-integrated exploration

The interactive Coliseum viewer has been advanced to **0.3.0** with actual GIS centerlines and curb-ramp inventory markers. The structure and terrain of the stadium **remain the 0.2.0 procedural approximation**: no independent LiDAR-derived mesh reconstruction was possible from the committed source metadata alone.

- **10 LA28-area street centerline features** from the repository's extracted GIS dataset.
- **20 historic curb-ramp inventory points** in the study area (2017 record creation). A point's `HASRAMP=Yes` is not a field survey or an accessible path certification.
- GIS overlays are positioned using the **provisional 2008 courtyard-based candidate registration** and a local linearization into EPSG:6340. The annotation Y coordinate is a nominal display elevation, not a physical elevation measurement.
- Toggle **GIS ON/OFF** in the viewer. GIS lines and points are **not part of the collision or navigation model**.
- New versioned `dist/data/geospatial-evidence.json` includes source object IDs, reference blob SHAs, candidate registration parameters, original coordinate values and known limitations.

## Reproduction

```sh
python -m http.server 3000 --directory apps/coliseum-mvp/dist
npm --prefix apps/coliseum-mvp run check
npm --prefix apps/coliseum-mvp run check:v03
```

The native USGS 2023–24 LAZ point clouds (29.1 million full-tile points, approximately 8.11 million in the study area) were acquired in the earlier processing workspace and deliberately excluded from GitHub because of their size. Their summary metrics and provenance were saved, but **the individual points required to reconstruct a new bowl/tower surface are unavailable to this revision**. Do not interpret the displayed GIS evidence as a fitted model. The 0.2.0 GLB remains the base-geometry export; no falsely named 0.3 GLB is supplied.

Suggested next geometry iteration: recover the acquired LAZ files or regenerate a compact, documented bowl/tower surface sample from the recorded acquisition pipeline; inspect raw class-1 first returns; resolve field/bowl boundaries and survey control; then fit and verify a new component-level mesh using withheld data. Do not change the bowl based solely on the conditional 7.25 m vertical RMSE statistic.

---

## Prior implementation — 0.2.0

# Coliseum 3D MVP 0.2

A dimension-anchored Three.js model of the Los Angeles Memorial Coliseum with touch-first exploration. Three.js 0.170.0 is vendored locally. No installation or bundling is required.

## Explore

- **First-person:** use the analog joystick to move and independently swipe the scene to look. Movement is 8 m/s in Explore and 16 m/s in Fast. Desktop supports WASD, drag-to-look, arrow keys and Shift.
- **Overhead map:** north-up orthographic camera. One-finger pan, two-finger pinch/pan, zoom buttons, venue/grounds fit. Tap a named place to jump directly, or tap a walking surface and choose Explore here.
- **Places:** field, lower/upper north bowl, west bowl, peristyle, exterior grounds and seven tower terrace previews. There is no visitor avatar.
- **Connections:** modeled bowl aisle steps; schematic east field-to-plaza stairs; three schematic exterior-to-rim stairs. These support continuous exploration between the field, stands and surrounding grounds. Tower floors use direct location jumps; detailed interior circulation is not modeled.

## Run and reproduce

Serve `dist/` over HTTP. On your own computer:

```sh
python -m http.server 3000 --directory dist
```

Open `http://localhost:3000`. Direct file opening does not support the module/data loading used here.

With Node 20+:

```sh
node scripts/check-model.mjs
node scripts/check-navigation.mjs
node scripts/export-model.mjs
node scripts/check-export.mjs
node scripts/package.mjs
```

Edit `dist/data/venue.json`, increment its revision and update generation code as necessary. The viewer and export use the same inputs and generator. The checks write `dist/data/validation.json`; packaging synchronizes the evidence manifest and source ZIP. `dist/coliseum-0.2.0.glb` is the current binary asset. Seating uses `EXT_mesh_gpu_instancing`; consuming applications must support this standard extension.

## Architecture

- `dist/data/venue.json`: meter-based dimensions, coordinate frame, stable component/level IDs, references, estimates and navigation configuration.
- `dist/model.js`: procedural geometry, walking surfaces, simplified architectural collision boxes and dimension checks. Navigation surface descriptions are created alongside the same mesh dimensions.
- `dist/navigation.js`: lightweight surface sampling, swept collision steps and normalized movement. It avoids repeatedly raycasting the detailed stadium while walking. Raycasting remains available for arbitrary map point selection and fallback models.
- `dist/joystick.js`, `dist/touch-look.js`: independent pointer controllers, release/cancel/reset behavior and analog joystick math.
- `dist/cameras.js`: orthographic north-up map camera and portrait/landscape framing.
- `dist/app.js`: view modes, touch gestures, location jumps, controls and scene rendering. Static shadows are computed on demand instead of redrawing the shadow scene every frame.
- `dist/data/manifest.json`: evidence, assumptions, configuration and omissions for engineering use.
- `dist/data/validation.json`: geometry, touch-controller, traversal, camera and export/import results with verification limits.
- `dist/data/*.csv`: source research catalog snapshots.

Stable top-level component IDs: `field`, `bowl`, `seats`, `circulation`, `tower`, `peristyle`, `context`, `displays`. Seven tower levels have their own IDs. Seat instance count is a rendering choice, not capacity.

## Sources and accuracy

Research: https://github.com/watsoncsulahack/azure-la28/tree/main/research/coliseum-dimensions

The Draft Technical Guide 2024 (S01) supplies field/street/last-row height relationships, tower and cauldron height references, field/football dimensions, arch count and display sizes. The National Park Service historic record (S04) supplies a provisional approximate outer ellipse. S01 PDF p.5 was visually inspected for context; it has not been registered or traced as a survey.

Local coordinates use meters: X schematically east, Y up, Z schematically south, field reference Y=0. This is right-handed and not georeferenced. The 0.30 m physical accuracy target remains unverified. Numeric checks establish source consistency for selected generated dimensions; no independent physical venue checks have been performed.

Bowl profiles, inner outline, rows and seat spacing, tower footprint and floor heights, peristyle details and landscape remain estimates. MVP 0.2 adds explicitly schematic approach paths, drives, plazas and stair locations (A009). These give exterior navigation context without claiming an as-built representation of neighboring streets/buildings or real pedestrian routes. The permanent football configuration is used; temporary LA28 installations are not modeled.

## Validation limits

The [executed evidence audit](../../analysis/coliseum-model/evidence-iteration/README.md) adds acquired LiDAR/county/DEM diagnostics and per-mesh traceability. `npm run check:evidence` rebuilds the mesh/literal inventory. Validation now explicitly lists the unresolved historic bowl span (M158) and variable field-width control (M019); neither is passed or silently omitted. The candidate geographic transform remains outside the app. Source geometry and original requirements are preserved.

Node checks exercise actual pointer event controllers with simultaneous independent touches, joystick release/cancel, speed/diagonal normalization, fast collision sweeps, navigation surface agreement with meshes, continuous stair/bowl traversal at both speeds and orthographic camera math at portrait/landscape viewport sizes. GLB is reimported to check component identities, seating instances and meter scale.

Browser rendering and physical phone gestures have not been directly tested in this chat: its managed browser-control tool is unavailable. No mobile frame-rate claim is made. Collision volumes are simplified, seats and trees are decorative, under-stand interiors are incomplete, and this model does not establish a real-world accessible route.

## Revisions

- **0.2.0:** analog joystick and independent swipe look; faster movement; avatar removed; orthographic map with pan/pinch/zoom and tap-to-explore; compact touch controls; expanded place jumps; surrounding path/plaza context and stair connections; lightweight walking surface sampling, swept collision and static-shadow optimization.
- **0.1.0:** initial reference-based model, viewer, evidence manifest, numeric checks and reusable GLB.

The generator is currently Coliseum-specific. The separate inputs and stable identities support future reuse; general multi-venue generation and photo-driven updates are not implemented.

Three.js and its examples are MIT licensed; see `dist/vendor/LICENSE`. Research documents retain their publishers' rights. This is an independent prototype, not an official LA28 or Coliseum publication.
