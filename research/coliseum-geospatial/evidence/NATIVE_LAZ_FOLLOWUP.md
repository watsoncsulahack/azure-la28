# Native LAZ acquisition follow-up

Recorded UTC: 2026-11-28T01:09:38.706471+00:00

**Completed native tiles: 2/2. Status: ACQUIRED_AND_INSPECTED.**

| Tile | Expected bytes | Completed bytes | Retained partial bytes |
| --- | ---: | ---: | ---: |
| USGS_LPC_CA_LosAngeles_B23_11SLT038000376400.laz | 64,160,267 | 64,160,267 | 4,194,304 |
| USGS_LPC_CA_LosAngeles_B23_11SLT038100376400.laz | 63,589,240 | 63,589,240 | 0 |

Final attempt: `{'status': 'COMPLETE', 'completed_utc': '2026-11-28T01:07:22.811860+00:00', 'tiles': 2, 'bytes': 127749507, 'fully_decoded_points': 29118711, 'aoi_points': 8111643, 'inspection': 'Both source files completely decoded and CRS read from embedded EVLRs. A local len(chunk.points) API error was corrected to len(chunk); complete data were preserved and checks rerun.'}`.

The first retry received a 4 MiB prefix. A resume request returned HTTP 429, and the prefix request still returned 429 after a five-minute backoff. A final full-file attempt was scheduled after a further ten-minute cooldown with a 30-minute body-transfer allowance. Existing prefix bytes were preserved separately. The final result above controls the current acquisition status.

The downloader now preserves interrupted payloads, checks resume prefixes and HTTP ranges, pins source validators, checks catalog byte sizes and LAS magic, and excludes partials from completed-source counts. Error-page ETags are never reused as dataset validators. Throttled responses are recorded without automatic repeated retries.

Both per-tile USGS XML records were acquired and checksummed. They report NAD83(2011) / UTM zone 11N, NAVD88 elevations in metres, acquisition 2023-01-08 through 2024-01-07, and publication 2025-06-13. Their vertical accuracy field is N/A and altitude resolution is 1.0 m; the partial LAS header coordinate scale is 0.01 m. Neither numeric field establishes physical accuracy. Binary extended-metadata inspection still requires complete data unless separately documented.

NOAA points to the same USGS binary host. Its checked S3 native mirror prefix was empty. Both ScienceBase tile JSON endpoints returned 403. The authoritative per-tile XML endpoints did succeed.

The initial prefix identifies LAS 1.4, point format 6, 14,070,854 declared points and one extended metadata record starting at byte 64,159,304. These are partial-header observations, not a claim that the whole file has been downloaded or decoded.

A local point-count check initially used the wrong laspy attribute. It was corrected to `len(chunk)` for ScaleAwarePointRecord objects; both complete files were then decoded and their counts checked. Raw source files were preserved throughout.

Validation: 13 geospatial tests passed, including resumable-transfer safeguards and exclusion of partial files from the source inventory. No model geometry or original accuracy requirement changed. Existing EPT extraction remains available.

Exact source URLs, hashes, partial locations and outcomes: [machine-readable status](reports/native-retry-status.json). Source inventory and product manifests are regenerated separately with `finalize.py`.

**Native inspection:** all 29,118,711 points decoded successfully; the study-area crop contains 8,111,643 points. Both files are LAS 1.4 / point format 6, with EPSG:6340 horizontally and EPSG:5703 vertically. The embedded vertical CRS name explicitly identifies NAVD88 height / Geoid18 in metres. Coordinate scales are 0.01 m, which does not establish physical accuracy.

**Native/EPT consistency:** 50,000 sampled points have maximum 3D nearest-coordinate difference 0.005838 m, with identical classifications for the associated points and numerically unchanged elevations. This is expected encoding quantization between two distributions of the same acquisition, not independent physical validation. The native crop has 13 more points; boundary associations account for the net difference (59 native-only vs 46 EPT-only points near the crop edges). Exact source point IDs were not compared.

The native coordinate frame can now be used directly for subsequent analysis. The model-to-world transformation remains provisional and no SR-3D-10 physical acceptance is claimed.
