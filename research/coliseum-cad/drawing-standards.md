# Architectural drawings, dimensions and tolerances

## How this relates to GD&T

A venue drawing set usually communicates its layout with plans, elevations, sections, grids, levels, dimensions, schedules and specifications. There is no single universal replacement for every function of mechanical GD&T. Fabricated building components can still need detailed shop drawings and GD&T; building layout and construction accuracy also rely on discipline-specific standards and contract specifications.

Three separate questions matter:

1. **Presentation:** how the drawing, layers, dimensions and references are organized.
2. **Construction requirements:** what deviation is permitted when work is fabricated or built.
3. **Reconstruction accuracy:** how closely our model represents the existing venue.

Our ±0.30 m target belongs to the third question. It is not a general allowance for doors, stairs, steelwork, concrete or other construction.

## Useful standards families

| Reference | Main role | Relevance here |
| --- | --- | --- |
| [United States National CAD Standard / CSI](https://www.csiresources.org/standards/ncs) | Drawing organization, AIA CAD layer guidelines, Uniform Drawing System, plotting and BIM conventions | Useful organizing framework for a US architectural drawing set |
| [ISO 129-1:2018](https://www.iso.org/standard/64007.html) | General presentation of dimensions and associated tolerances | How dimensional information is communicated across technical disciplines |
| [ISO 7519 — construction drawing presentation](https://www.iso.org/obp/ui/#iso:std:iso:7519:ed-3:v1:en) | General arrangement and assembly drawing presentation for construction documentation | Plans, sections, levels and related construction representations |
| [ISO 6284:2023](https://www.iso.org/standard/82512.html) | Indication of limit deviations in construction documents | Explicitly stating permitted deviations when a construction requirement is actually intended |
| [ACI tolerances committee / ACI 117 family](https://www.concrete.org/getinvolved/committees/directoryofcommittees/acommitteehome/committee_code/c0011700.aspx) | Concrete construction and material tolerances | Material-specific requirements; not replaced by our modelling target |
| [ANSI/AISC 303](https://www.aisc.org/aisc/publications/current-standards/) | Standard practice including structural-steel fabrication/erection provisions | Discipline-specific construction tolerances and coordination |

These links identify the standards and their scopes. The package does not reproduce licensed standards, specify their construction tolerances, or claim a full conformance audit. R001 uses a documented project convention inspired by architectural drawing practice.

## Conventions used in R001

- G-001 provides purpose, units, evidence limits, scales and the issue status.
- A-101 is the general arrangement plan, A-201 the east–west section A-A, and A-202 the north–south section B-B.
- DXF model geometry is full size in metres. Paper layouts are A2 in millimetres with scale handled by viewports.
- The local field-centre coordinate frame is fixed and distinguishes plan north from a verified survey orientation.
- Source-reported, historic-approximate and estimated geometry are identified separately in the geometry layers, notes, native CAD properties and source register.
- Native `DIMENSION` entities retain geometry-driven values (`<>`), source IDs in XDATA and rendered dimension blocks. Values are not a detached list of manually typed measurements.
- Layers include `A-REFR-SRCE`, `A-REFR-ESTM`, `A-AREA-HIST`, `A-SEAT-ESTM`, `A-ANNO-DIMS`, `A-ANNO-NOTE`, and `A-ANNO-DATM`. These are project layer names, not a claim that every code is a prescribed NCS layer.
- Decimal precision follows readable metric conversions. Extra decimal places do not mean the physical feature was surveyed to that precision.
- The historic ellipse is explicitly approximate; the inferred field outline and bowl profiles are not promoted to measured facts.
- Revision R001 is a reference-only issue. Future changes should record which source or assumption changed and regenerate all derived files.

## IFC and GLB in this workflow

[IFC](https://www.buildingsmart.org/standards/bsi-standards/industry-foundation-classes/) carries building objects, geometry, properties and spatial relationships. [Bonsai for Blender](https://bonsaibim.org/studio.html) is open-source native IFC authoring software; [FreeCAD](https://www.freecad.org/) also provides IFC-capable BIM workflows. IFC can contain tessellated or parametric geometry. R001 deliberately labels its tessellated reference proxies and preserves source metadata.

The native FreeCAD file retains analytic CAD geometry. The supplied GLB is exported by tessellating that reopened file, converting internal millimetres to metres, and rotating Z-up CAD coordinates into the Three.js Y-up frame. A rendering mesh can represent dimensions accurately within its tessellation settings, while physical accuracy still depends on the underlying evidence.

The editable DXF files provide the requested drawing reference. Genuine DWG conversion requires a compatible writer; this package supplies DXF without disguising it as DWG.
