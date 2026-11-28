# CR-3D-001 — feature-specific physical accuracy and coverage

**Status: proposed, awaiting project approval.** The original SR-3D-10 remains unchanged in `requirements.csv` and `requirements.md`:

> Target physical positional error within 0.30 m for agreed features and record unverified coverage and exceptions.

The handoff authorizes treating 0.30 m as a provisional engineering target. This proposal does not change that requirement, assert approval, or assign a passing feature tolerance.

## Recommended replacement wording

For each agreed component and intended use, define the represented physical boundary, configuration epoch, horizontal and vertical reference frames, authoritative evidence, source precision/uncertainty, and an approved feature-specific tolerance before physical acceptance. Validate against independent observations or withheld controls, reporting signed deviations, RMSE, median absolute deviation, P95 absolute deviation, maximum deviation, observed coverage and excluded/unobserved geometry. Distinguish registration error from shape error where evidence allows. Retain 0.30 m as a provisional positional objective for suitable features pending source- and use-specific justification. Transcription and generator consistency alone shall not establish physical acceptance. Unobserved geometry shall remain unverified.

## Why a change is warranted

- The NPS dimensions are historical and approximate; converting them to four decimal places does not establish that precision.
- The official guide reports relative heights but supplies no surveyed street benchmark or consistently identified endpoints.
- Source EPT and county geographic coordinates require datum operations whose reported nominal accuracy is already coarser than 0.30 m in this workflow. Current survey control is missing.
- The terrain raster bridges the sampled field by about 11.25 m relative to laser observations. Metadata resolution alone cannot define acceptable field-elevation accuracy.
- Bowl silhouette, walking-plane height, ramp gradient, doorway clearance and step geometry have different observability and consequences. Positional tolerance alone cannot certify accessible routing.

## Proposed acceptance record (no numerical tolerances approved yet)

| Feature/use | Evidence needed | Acceptance basis to approve |
| --- | --- | --- |
| Historic shell context | Historic text plus matched current observed endpoints | Historical reference uncertainty and present-day boundary definition; no millimeter claim |
| Current shell/tower geometry | Registered current scan plus independent controls/as-built sections | Separate horizontal/vertical residuals, density and occlusion masks |
| Field surface and edge | Current line endpoints and field survey/scan | Absolute elevation control, fitted-plane holdouts, edge correspondence and playing/event configuration |
| Accessible circulation | Current walking-surface/door/ramp/stair survey and verified topology | Feature-specific positional, width, grade, cross-slope and clearance tolerances approved for intended use |
| Hidden interiors | Current as-built documentation plus field checks | Remain unverified until observable or documented; do not fill validation gaps |

Project approval must record the decision, approver, date, revised requirement revision and scope. Only then update the original register. This iteration leaves the original wording and 0.30 m value intact and reports physical acceptance as not validated.
