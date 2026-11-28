import * as THREE from './vendor/three.module.js';

export const EVIDENCE_LAYER_VERSION = '0.3.0';

/**
 * Evidence visualization in the CURRENT provisional candidate frame.
 * Road centerlines are not sidewalks; points marked HASRAMP do not establish usable routes.
 * The horizontal positions have not been approved against independent survey control.
 * Absolute elevations of street or ramp GIS features are UNKNOWN: nominal streetHeight is
 * a DISPLAY offset only and MUST NOT become a walkable surface or collision constraint.
 */
export function buildEvidenceOverlay(spec, evidence) {
  if (evidence?.schemaVersion !== EVIDENCE_LAYER_VERSION) throw Error('Unsupported GIS evidence version');
  const parent = new THREE.Group();
  parent.name = 'geospatial-evidence';
  parent.userData = {componentId: 'geospatial-evidence', version: EVIDENCE_LAYER_VERSION,
    status: 'PROVISIONAL_DIAGNOSTIC_ONLY', navigable: false, surveyGeometry: false,
    caution: 'Horizontal candidate alignment only; all marker elevations are visualization offsets.'};
  const roadMaterial = new THREE.LineDashedMaterial({color: '#198cb5', dashSize: 5, gapSize: 3,
    transparent: true, opacity: .95, depthTest: true});
  const rampMaterial = new THREE.MeshBasicMaterial({color: '#e4ab40', depthTest: true});
  const markerGeo = new THREE.SphereGeometry(1.5, 8, 6);
  const streetY = spec.parameters.streetHeight + 1.2;
  let lines = 0;
  for (const f of evidence.streetSegments || []) {
    for (const path of f.localPaths || []) {
      if (path.length < 2) continue;
      const xyz = path.map(([x,z]) => new THREE.Vector3(x, streetY, z));
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(xyz), roadMaterial);
      line.name = `street-centerline-${f.sourceId}`;
      line.userData = {sourceId: f.sourceId, sourceType: 'centerline', streetName: f.name,
        passable: false, physicalZKnown: false, sourceClass: 'administrative GIS record'};
      line.computeLineDistances();
      parent.add(line);
      lines++;
    }
  }
  // LARIAC2/2008 envelope is a bounding rectangle, NOT a building footprint.
  if (evidence.referenceFootprintBounds?.localCorners?.length === 4) {
    const corners = evidence.referenceFootprintBounds.localCorners;
    const outline = corners.concat([corners[0]]).map(([x,z])=>new THREE.Vector3(x,streetY+.25,z));
    const boundary = new THREE.Line(new THREE.BufferGeometry().setFromPoints(outline),
      new THREE.LineDashedMaterial({color:'#d25b83',dashSize:8,gapSize:4}));
    boundary.name='historic-2008-stadium-polygon-bounding-rectangle';
    boundary.userData={sourceType:'2008 building polygon AABB (not footprint)',sourceId:evidence.referenceFootprintBounds.sourceObjectId,
      navigable:false,approvedForGeometry:false};
    boundary.computeLineDistances();
    parent.add(boundary);
  }
  let points = 0;
  for (const f of evidence.curbRamps || []) {
    const [x,z] = f.localXZ;
    if (!Number.isFinite(x) || !Number.isFinite(z)) continue;
    const marker = new THREE.Mesh(markerGeo, rampMaterial);
    marker.position.set(x, streetY + 1.5, z);
    marker.name = `curb-ramp-inventory-${f.sourceId}`;
    marker.userData = {sourceId: f.sourceId, sourceType: 'curb-ramp-inventory',
      recordedHasRamp: f.hasRamp, captureYear: f.createdYear, passable: false,
      conditionVerified: false, physicalZKnown: false};
    parent.add(marker);
    points++;
  }
  return {group: parent, streets: lines, curbRamps: points, navMeshesAdded: 0};
}
