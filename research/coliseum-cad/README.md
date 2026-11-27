# Coliseum engineering reference — R001

Reference issue dated **2026-11-27**. Priority deliverable: editable, meter-based **DXF drawings with native dimension entities**. Additional deliverables are a native **FreeCAD FCStd**, an **IFC4** building reference, and a **GLB derived from the reopened FreeCAD geometry**. No STEP files are generated. No DWG file is claimed.

This is an independent reference reconstruction from public research, with explicit estimates. It is not a venue survey, an as-built record, a structural design, or a construction issue. The **±0.30 m physical accuracy target remains unverified**.

## Open the files

| File | Purpose / software |
| --- | --- |
| [Complete reference ZIP](coliseum-engineering-reference-R001.zip) | Drawings, models, inputs, scripts and verification records |
| [Four-sheet PDF](drawings/coliseum-reference-drawings-R001.pdf) | G-001 notes, A-101 plan, A-201 longitudinal section, A-202 transverse section |
| [A-101 plan DXF](drawings/A-101.dxf) | Open in LibreCAD, QCAD Community Edition, FreeCAD or other DXF-capable CAD software |
| [A-201 section DXF](drawings/A-201.dxf) | East–west section through the field/peristyle |
| [A-202 section DXF](drawings/A-202.dxf) | North–south section through the field/tower |
| [FreeCAD model](models/coliseum-reference-R001.FCStd) | Open directly in FreeCAD |
| [IFC4 reference](models/coliseum-reference-R001.ifc) | Open in Bonsai for Blender or an IFC-capable FreeCAD BIM workflow |
| [CAD-derived GLB](models/coliseum-reference-R001.glb) | Lightweight 3D reference view; generated from this FCStd, not the earlier browser mesh |
| [Validation report](reports/validation.json) | DXF dimensions, native shapes, IFC rules/positions, GLB axes/units and PDF checks |
| [Drawing conventions and standards guide](drawing-standards.md) | Relationship to mechanical GD&T and architectural documentation |

GitHub may require **Download raw file** for CAD and binary files. The PNGs in [reports](reports/) preview the rendered DXF layouts. PDF pages are A2 landscape; plot at actual size for the stated scales.

DXF was chosen for portable editable exchange. A verified DWG writer/converter was not available here. DXF files have not been renamed to `.dwg`; a genuine DWG can be produced later in a compatible CAD application.

## Units and coordinates

- DXF model space: **one drawing unit = one metre**, `$INSUNITS=6`. Geometry is at full size; A2 paper layouts provide the stated plot scales.
- CAD and IFC: **X east, Y north, Z up**. The chosen field-centre reference is `(0,0,0)`. Directions are schematic plan alignment, not surveyed geographic bearings.
- FreeCAD stores lengths internally in millimetres; the generator explicitly multiplies metre inputs by 1000. Display-unit preferences may show mm or m.
- GLB: metres, **X east, Y up, Z south**. The explicit transform from CAD is `[x,y,z] -> [x,z,-y]`.
- Street reference is `Z=12.4206 m`, last-row reference `Z=35.2552 m`, tower overall top `Z=45.7454 m`, and cauldron top reference `Z=50.0634 m`. Street is a generic source reference, not a surveyed benchmark or a claim that all exterior ground is level.

## What is controlled and what is estimated

The [source research](../coliseum-dimensions/README.md) and [control register](inputs/control-register.csv) retain measurement IDs and source URLs. S01 is the **Draft Technical Guide 2024**; S04 is the historic NPS nomination. The snapshot [inputs/venue.json](inputs/venue.json) preserves the starting data and assumptions used by the viewer.

Source controls include the field and football extents, field/street/last-row relationships, tower and cauldron overall height references, and fifteen peristyle arches. The approximate historic **316.3824 × 224.9424 m** envelope is a construction-reference ellipse in FCStd and DXF, not a measured current perimeter. That wire is intentionally omitted from IFC/GLB render geometry.

Estimated geometry includes the field outline between known extents, bowl profiles, 80 visual bands, inner seating boundary, tower footprint and individual floor elevations, and peristyle arch/pedestal dimensions. These are assumptions A001–A008. Model bands are not a seat-row inventory. The older undatumed design elevations M170–M175 are not used as field-relative as-built elevations.

The engineering model contains **111 rendered reference components plus one CAD construction-reference wire**. It omits individual seats, landscaping, detailed interiors, display supports, and the MVP's visitor-only exterior paths/stair connectors. The app's later A009 navigation additions are not promoted into engineering evidence. The [MVP 0.2 viewer](../../apps/coliseum-mvp/README.md) remains a separate application snapshot.

## Editability and building semantics

The FCStd is a real native document containing valid Open CASCADE BRep shapes, a parameter register, and per-object source/evidence properties. Tower plate sizes/placements and roof elevation include native expressions. Bowl/peristyle shapes are generated BReps: changing their input parameters requires rerunning the supplied generator; they are not a fully constrained interactive feature-history model.

The IFC uses `IfcProject`, `IfcSite`, `IfcBuilding` and seven `IfcBuildingStorey` identities. Reference components are generic `IfcBuildingElementProxy` objects with custom `Coliseum_Reference` properties. This avoids asserting unknown structural assemblies. Its geometry is tessellated from the reopened FCStd at nominal **0.05 m deflection**. IFC validity does not certify physical venue accuracy.

The GLB is built from that same native CAD tessellation, with stable object IDs, provenance and the CAD-file hash. This demonstrates a working FCStd-to-GLB pipeline without STEP. FreeCAD also documents [glTF/GLB export support](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/GlTF.md); exact GUI availability depends on the FreeCAD build.

## Reproduce

The reference was produced with FreeCAD 1.0.0, ezdxf 1.4.5 and IfcOpenShell 0.9.0.post1. Install FreeCAD separately and install the Python requirements in a virtual environment:

```sh
python -m venv .venv
.venv/bin/pip install -r research/coliseum-cad/requirements.txt
.venv/bin/python research/coliseum-cad/scripts/build_all.py \
  --freecad-python /usr/bin/python3 \
  --freecad-lib /usr/lib/freecad-python3/lib
```

Use the Python interpreter/library paths that match your FreeCAD installation. On this Linux image, importing FreeCAD from its matching system Python worked; the `freecadcmd --version` launcher crashed. The generator does not require the launcher or a graphical desktop. Scratch tessellation and caches go under ignored repository `work/`, not into the committed package.

The build creates native CAD, reopens it, exports IFC/GLB, builds and renders the three DXFs, validates the outputs, and writes the manifest/ZIP. Native CAD dimensions are measured with `optimalBoundingBox(False, False)` so a cached display mesh cannot replace analytic curve bounds. IFC/GLB geometry is checked separately with its mesh tolerance. Generation reproduces geometry and references; file timestamps and generated IFC relation IDs can differ.

## Verification scope

The package checks all eleven native DXF dimensions against the measurement catalog, valid/reopened native CAD shapes, seven selected native geometric dimensions, IFC4 schema/EXPRESS rules, all 111 IFC world-coordinate bounds, all GLB component coordinates/identities/axis mappings, and four A2 PDF pages. Rendered drawing previews were visually inspected.

These checks establish internal/source consistency. There are **zero independent site measurements** in this package. Screen dimensions and room areas not represented here remain in the broader research catalog. No fabrication, construction, code-compliance or real-world access certification is implied.
