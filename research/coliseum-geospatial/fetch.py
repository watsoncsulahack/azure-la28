#!/usr/bin/env python3
"""Build a reproducible Coliseum spatial subset without hardcoded GIS measurements.

Python 3.10+ standard library. Downloading requires Internet access. PDAL is
needed only to execute the generated lidar pipelines.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "derived"
SERVICE = ("https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/"
           "Countywide_Building_Outlines_%282020%29/FeatureServer/0/query")
EPT = {
    "2023": "https://s3-us-west-2.amazonaws.com/usgs-lidar-public/CA_LosAngeles_1_B23/ept.json",
    "2016": "https://s3-us-west-2.amazonaws.com/usgs-lidar-public/USGS_LPC_CA_LosAngeles_2016_LAS_2018/ept.json",
}

def bbox():
    fc = json.loads((ROOT / "aoi.geojson").read_text())
    west, south, east, north = [float(v) for v in fc["bbox"]]
    if not (west < east and south < north):
        raise ValueError("Invalid bbox")
    return [west, south, east, north]

def ids_url():
    west, south, east, north = bbox()
    params = {
        "f": "json", "where": "1=1",
        "geometry": f"{west},{south},{east},{north}",
        "geometryType": "esriGeometryEnvelope", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "returnIdsOnly": "true"
    }
    return SERVICE + "?" + urlencode(params)

def features_url(ids):
    params = {"f": "geojson", "where": "1=1", "objectIds": ",".join(map(str, ids)),
              "outFields": "*", "outSR": 4326, "returnGeometry": "true"}
    return SERVICE + "?" + urlencode(params)

def read_json(url):
    req = Request(url, headers={"User-Agent": "IS699-Coliseum-Geodata/0.1"})
    with urlopen(req, timeout=60) as response:
        data = json.load(response)
    if not isinstance(data, dict) or data.get("error"):
        raise RuntimeError(f"GIS server error: {data}")
    return data

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def collect_buildings(dry_run=False):
    if dry_run:
        print(ids_url())
        print("Then query returned object IDs in batches of 250 as GeoJSON.")
        return
    ids_data = read_json(ids_url())
    ids = sorted(set(int(x) for x in ids_data.get("objectIds", [])))
    if not ids:
        raise RuntimeError("No 2020 building polygons found for study AOI.")
    features = []
    for offset in range(0, len(ids), 250):
        batch = ids[offset:offset + 250]
        data = read_json(features_url(batch))
        feats = data.get("features")
        if not isinstance(feats, list):
            raise RuntimeError(f"Invalid feature response at {offset}")
        features.extend(feats)
        print(f"Fetched {min(offset+250, len(ids))}/{len(ids)} IDs", file=sys.stderr)
    features_by_id = {}
    for feature in features:
        oid = feature.get("properties", {}).get("OBJECTID")
        if oid is None:
            raise RuntimeError("Feature missing OBJECTID")
        features_by_id[int(oid)] = feature
    if set(features_by_id) != set(ids):
        raise RuntimeError("Some features missing; not writing incomplete extract.")
    path = OUT / "lariac6_buildings_2020_aoi.geojson"
    write_json(path, {"type": "FeatureCollection", "bbox": bbox(),
                      "features": [features_by_id[x] for x in ids]})
    write_json(OUT / "lariac6_buildings_2020_aoi.manifest.json", {
        "source_url": SERVICE, "source_id": "LARIAC6_2020_BUILDINGS",
        "query_url": ids_url(), "bbox_epsg4326": bbox(),
        "output_crs": "EPSG:4326", "count": len(ids),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "downloaded_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "height_units": "UNVERIFIED; SOURCE VALUES RETAINED",
        "license_review": "Review LA County eGIS terms before redistribution",
    })
    print(f"Saved {len(ids)} polygons to {path}")

def prepare_lidar():
    OUT.mkdir(parents=True, exist_ok=True)
    w,s,e,n = bbox()
    for year, url in EPT.items():
        pipeline = [
            {"type": "readers.ept", "filename": url,
             "bounds": {"minx": w, "miny": s, "maxx": e, "maxy": n, "crs": "EPSG:4326"}},
            {"type": "writers.las", "filename": str((OUT / f"usgs_3dep_{year}_aoi.laz").resolve()),
             "compression": True, "scale_x": 0.001, "scale_y": 0.001, "scale_z": 0.001,
             "offset_x": "auto", "offset_y": "auto", "offset_z": "auto"}
        ]
        filename = ROOT / f"pdal_{year}.json"
        write_json(filename, pipeline)
        print(f"Prepared: {filename}; run: pdal pipeline {filename}")
    print("After download inspect source horizontal/vertical CRS with pdal info.")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["fetch-buildings", "prepare-lidar"])
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if args.command == "fetch-buildings":
        collect_buildings(args.dry_run)
    else:
        prepare_lidar()

if __name__ == "__main__":
    main()
