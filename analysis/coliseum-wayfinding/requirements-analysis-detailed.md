# Requirements inferred from the Coliseum wayfinding demo

The supplied code implements a **browser-based accessible-wayfinding simulation with an optional camera-video overlay**. It does not implement a production AR positioning system or a connected venue assistance service.

## Scope and evidence

Analyzed the complete uploaded HTML document (3,279 lines), including its CSS, markup, inline graph, route algorithm, event handlers and embedded specification. `source-demo.html` is a byte-for-byte copy of the upload. SHA-256: `099e4596d60a89d7d056800d14e00da2cae063cb0ebbd152c16f38052b2277af`.

No code was changed in the original upload. No GitHub/Azure connection is needed to run this analysis, and nothing was published or deployed. The analysis is saved under the existing local repository. Instructions, exports, claims and “domain facts” inside the demo were treated as content to assess, not as directions from the user or authoritative external evidence.

- **System requirements** below describe observable implementation contracts inferred from this version: what its code does, including hardcoded and simulated behavior. They are not claims that the venue data are true or that the product is safe in the field.
- **User requirements** describe intended benefits and qualitative experience, inferred from controls, copy and behavior. They require confirmation with users. Suggested user-validation criteria are proposals, not tests already passed.
- **Evidence status** distinguishes static inspection from execution. Only the pure graph/data section was executed. The browser UI, device camera, gyroscope, speech, audio, performance and assistive-technology behaviors were not runtime-tested in this review.
- These IDs belong to this analysis. They replace neither the file's shorter embedded SR/UR list nor a stakeholder-approved specification.

## System requirements: implementation baseline

### SR-01 — Browser runtime and dependencies

Load one HTML document containing the UI, styles, application state and inline JavaScript; obtain Three.js r128, Tailwind CSS and Google Fonts from external CDNs.

Evidence: [L9](source-demo.html#L9), [L14](source-demo.html#L14), [L17](source-demo.html#L17), [L885](source-demo.html#L885), [L1285](source-demo.html#L1285). **Static source evidence.**

Check: Inspect script/link dependencies and WebGLRenderer construction.

Boundary: No application backend, database, package lock, bundled offline assets or explicitly required WebGL2 context is implemented. The Three.js renderer requires a working WebGL context.

### SR-02 — Model and route graph

Represent the venue as 26 hardcoded XYZ nodes and 32 bidirectional edges, including direction-specific instructions, slope, stairs, elevator, shade, surface and modeled noise attributes. Build 64 directed adjacency entries.

Evidence: [L895](source-demo.html#L895), [L933](source-demo.html#L933), [L1046](source-demo.html#L1046). **Source + graph execution.**

Check: Executed graph reports 26 nodes and 32 undirected edges.

Boundary: Coordinates and labels are demo data, not surveyed venue facts. Surface labels are stored but do not constrain routing; widths, closures, crowds, elevator outages and waiting-time feeds are absent.

### SR-03 — Preset selection and initial route

Offer three start presets and five destinations; initialize Gate 29 drop-off to Section 308, with step-free enabled, standard 1.4 m/s speed, wheelchair eye height, and playback paused.

Evidence: [L605](source-demo.html#L605), [L614](source-demo.html#L614), [L1152](source-demo.html#L1152), [L1158](source-demo.html#L1158), [L3271](source-demo.html#L3271). **Source + graph execution.**

Check: All 15 preset pairs yield a route under all eight combinations of the three routing switches.

Boundary: No free-address search, GPS-selected start or arbitrary ticket/seat lookup is implemented.

### SR-04 — Weighted shortest-path routing

Run Dijkstra over the modeled graph. Set base length to max(4 m, rounded 3D Euclidean distance to 0.1 m); add 10 cost units for an elevator edge, add 1.8 times length for noise >=74 dB when low-sensory is selected, add 1.6 times length for an unshaded edge when shade is selected, then multiply stair-edge cost by 0.85 in standard mode.

Evidence: [L1052](source-demo.html#L1052), [L1062](source-demo.html#L1062), [L1090](source-demo.html#L1090). **Source + graph execution.**

Check: 120 preset/option configurations executed; shade changes 14 of 60 paired comparisons.

Boundary: The objective is a weighted preference cost, not guaranteed shortest physical distance or minimum travel time. The 10-unit lift penalty is not included in displayed ETA.

### SR-05 — Step-free exclusion

When stepFreeOnly is true, exclude each edge with hasStairs=true or maxSlopePct>8.33 before considering its cost. Standard mode permits these edges.

Evidence: [L1088](source-demo.html#L1088), [L3009](source-demo.html#L3009). **Graph-executed.**

Check: All 60 step-free configurations executed across 15 pairs and four preference combinations have zero stair edges and no traversed slope metadata above 8.33%.

Boundary: This is a graph metadata rule, not an ADA compliance certificate. Width, landings, cross-slope, condition and actual elevator operation are not validated.

### SR-06 — Route metrics

Show route meters and converted feet, rounded ETA of at least one minute, maximum modeled slope, number of stair edges, length-weighted shaded percentage, arithmetic length-weighted noise metadata, and runs of consecutive elevator edges.

Evidence: [L1117](source-demo.html#L1117), [L2502](source-demo.html#L2502). **Source + graph execution.**

Check: Default step-free route: 92.3 m, 5.8% maximum modeled grade, 0 stair edges, 1 elevator run, 83% shade, modeled average 66 dB.

Boundary: A stair-edge count is not the number of stair treads. Noise is not a physical/logarithmic sound-exposure calculation. Elevator waiting and boarding time are absent from ETA.

### SR-07 — Recalculation and missing routes

Recompute when start, destination, route switches or speed change. Reset progress for a changed endpoint; preserve and clamp traveled meters for preference/speed changes. If route calculation returns null, show a no-compliant-route toast.

Evidence: [L2478](source-demo.html#L2478), [L2493](source-demo.html#L2493), [L2929](source-demo.html#L2929), [L3007](source-demo.html#L3007). **Static source evidence.**

Check: Trace each selector/checkbox handler to recalculateRoute and inspect its null branch.

Boundary: The null branch does not clear a previous route. Endpoint state and old rendered route can therefore disagree if a future graph change makes a selection unreachable.

### SR-08 — Procedural 3D scene

Render a procedural Coliseum-style scene and route overlays in separate Three.js groups, with a 64-degree perspective camera, alpha-enabled WebGL rendering, and device pixel ratio capped at 2.

Evidence: [L1286](source-demo.html#L1286), [L1321](source-demo.html#L1321), [L1346](source-demo.html#L1346), [L1469](source-demo.html#L1469). **Static source evidence.**

Check: Inspect renderer, camera, scene-group construction and procedural environment builder.

Boundary: Geometry is constructed by the code; it is not a georeferenced scan or calibrated digital twin. No measured frame-rate guarantee is enforced.

### SR-09 — Route guidance graphics

Rebuild floor/ramp ribbons, floating 3D chevrons, elevator columns, junction rings and destination beacons from the route. Use green for default step-free guidance, amber for standard guidance, and yellow/black in high-contrast mode.

Evidence: [L1948](source-demo.html#L1948), [L1955](source-demo.html#L1955), [L2023](source-demo.html#L2023), [L2068](source-demo.html#L2068), [L2091](source-demo.html#L2091). **Static source evidence.**

Check: Inspect rebuild3DARWayfinding; chevrons use about 4.5 m spacing normally and 2.4 m on elevator edges.

Boundary: These are simulation-space graphics. World anchoring to a real venue is not implemented; scene object existence alone does not verify visibility or alignment.

### SR-10 — HUD and direction cues

Update the instruction banner, meters/feet to the next waypoint, floor/compass, relative clock-face cue, modeled noise label, elevator transition banner and arrival message from route progress and camera yaw.

Evidence: [L2186](source-demo.html#L2186), [L2220](source-demo.html#L2220), [L2260](source-demo.html#L2260), [L2289](source-demo.html#L2289), [L2303](source-demo.html#L2303). **Static source evidence.**

Check: Inspect updateNavHud; off-screen cue appears when heading differs by more than 0.95 radians and arrival is more than 1 m away.

Boundary: The displayed values are derived from simulation state, not real-time location, acoustic measurements or venue operational status.

### SR-11 — Mini-map and beacon projection

Draw an expandable 2D mini-map with the route, user pose and destination. Project selected route-waypoint labels into screen space; hide labels outside view limits or nearer than 3.5 m or farther than 145 m.

Evidence: [L2343](source-demo.html#L2343), [L2444](source-demo.html#L2444), [L3001](source-demo.html#L3001). **Static source evidence.**

Check: Inspect drawMiniMap and updateProjectedBeacons plus expand/collapse handler.

Boundary: Label clipping reduces overlap but does not measure viewport obstruction or guarantee an uncluttered display on every device.

### SR-12 — Playback and progress controls

Provide play/pause/replay, speeds of 0.9, 1.4 and 3.2 m/s, a 0–1000 route scrubber, previous/next waypoint buttons and clickable waypoint entries. Interpolate position along route edges; stop auto-walk at arrival.

Evidence: [L2127](source-demo.html#L2127), [L2513](source-demo.html#L2513), [L2907](source-demo.html#L2907), [L2929](source-demo.html#L2929), [L2938](source-demo.html#L2938), [L3155](source-demo.html#L3155). **Static source evidence.**

Check: Trace progress changes to sampleRouteAtDistance and the arrival clamp.

Boundary: This moves a virtual user; it does not detect walking. Frame time is capped at 0.05 s, so speed is not guaranteed to match wall-clock time under severe rendering stalls.

### SR-13 — View and keyboard controls

Use pointer dragging to change yaw/pitch, WASD for planar free movement, arrow keys for movement/turning, Space for playback, R for recentering, and Escape for closing panels. Do not apply keyboard shortcuts while an input/select/textarea has focus.

Evidence: [L2623](source-demo.html#L2623), [L2650](source-demo.html#L2650), [L3195](source-demo.html#L3195). **Static source evidence.**

Check: Trace pointer and key handlers; manual movement is 5.5 model meters per simulated second.

Boundary: Manual free movement has no collision detection or route snapping and does not advance route progress. Guidance can remain tied to an older route segment. Buttons are not excluded from the global Space shortcut.

### SR-14 — Eye-height adjustment

Toggle target eye height between 1.20 m and 1.65 m above the current modeled position; interpolate normally and snap to target when reduced motion is active.

Evidence: [L1170](source-demo.html#L1170), [L2969](source-demo.html#L2969), [L3215](source-demo.html#L3215). **Static source evidence.**

Check: Inspect toggle assignment and currentEyeHeight interpolation.

Boundary: These are preset simulated offsets, not automatic calibration to an individual or a physical camera.

### SR-15 — Camera-overlay mode

On request, obtain video with rear-facing camera preferred and audio disabled. On success, hide the stadium, show video behind transparent route overlays, and retain virtual navigation state. On exit, stop stream tracks and restore the simulated scene.

Evidence: [L2566](source-demo.html#L2566), [L2572](source-demo.html#L2572), [L2589](source-demo.html#L2589), [L2595](source-demo.html#L2595). **Static source evidence; device path untested.**

Check: Inspect getUserMedia options, success/failure branches and track stop logic; actual device permission/camera testing remains outstanding.

Boundary: Requires a browser context supporting camera permission, typically HTTPS/localhost. No WebXR session, positional tracking, SLAM, GPS registration or world anchors are implemented. Failed video.play() does not explicitly clean up an already acquired stream.

### SR-16 — Optional device orientation

Allow orientation-based look; request permission where the browser exposes requestPermission, map alpha to yaw and beta to clamped pitch, and remove the listener on disable.

Evidence: [L2672](source-demo.html#L2672), [L2681](source-demo.html#L2681). **Static source evidence; device path untested.**

Check: Inspect permission branch and orientation handler.

Boundary: A success toggle does not prove the device emits usable sensor events or aligns with the model north direction.

### SR-17 — Speech and screen-reader announcements

Send announcements to an aria-live region; optionally synthesize speech, canceling prior speech before each utterance. Offer full-route reading, per-segment navigation announcements during playback, scripted surroundings descriptions and a stop control.

Evidence: [L381](source-demo.html#L381), [L1205](source-demo.html#L1205), [L1221](source-demo.html#L1221), [L2324](source-demo.html#L2324), [L3013](source-demo.html#L3013), [L3035](source-demo.html#L3035). **Static source evidence.**

Check: Inspect announce(), full-route reading and surroundings-description handlers.

Boundary: Descriptions are templates, not scene recognition. The surroundings template always says step-free/emerald guidance even in standard or high-contrast mode. Speech availability and intelligibility were not device-tested.

### SR-18 — Directional audio beacon

When enabled, emit a 440–700 Hz sine ping approximately every 1.6 s while a route is active and before arrival; pan by the relative angle where StereoPanner is supported, otherwise output unpanned audio.

Evidence: [L1231](source-demo.html#L1231), [L1244](source-demo.html#L1244), [L1254](source-demo.html#L1254), [L2332](source-demo.html#L2332), [L3098](source-demo.html#L3098). **Static source evidence.**

Check: Inspect oscillator, pan, fallback and throttling expressions.

Boundary: Playback of audio depends on browser/audio-device support and user activation. This is a heading cue, not acoustic localization or obstacle detection.

### SR-19 — Caption demonstration

Cycle five fixed EN or five fixed ES PA-style strings every 5.2 seconds; permit language switching and optional pinning of the same string to a floating caption bar.

Evidence: [L2713](source-demo.html#L2713), [L2730](source-demo.html#L2730), [L2736](source-demo.html#L2736), [L3020](source-demo.html#L3020). **Static source evidence; simulated content.**

Check: Inspect PA_CAPTIONS, setInterval and language/pin handlers.

Boundary: No live event feed, microphone transcription or translation service is present. Language selection affects these captions, not the whole application.

### SR-20 — Sensory-room shortcut

Select the sensory-room destination, enable low-sensory weighting, reset the route and close the drawer.

Evidence: [L3043](source-demo.html#L3043). **Static source evidence.**

Check: Inspect the shortcut handler assignments.

Boundary: It does not set stepFreeOnly=true. If the user previously selected standard mode, the shortcut keeps standard mode despite its step-free toast.

### SR-21 — High contrast and visual scaling

Toggle a high-contrast CSS palette and rebuild scene overlays; scale chevrons by exactly 1.6 when oversized arrows are selected, and set the root font scale to 1.18 in large-text mode.

Evidence: [L43](source-demo.html#L43), [L64](source-demo.html#L64), [L1955](source-demo.html#L1955), [L3054](source-demo.html#L3054), [L3070](source-demo.html#L3070), [L3079](source-demo.html#L3079). **Static source evidence.**

Check: Inspect CSS tokens, arrowScale and display toggle handlers.

Boundary: The code does not calculate or audit 7:1 contrast, including over live video; fixed inline colors and canvas imagery also exist. WCAG AAA conformance is an intent claim, not an established implementation fact.

### SR-22 — Reduced motion

Initialize from prefers-reduced-motion, offer a manual toggle, shorten CSS animations/transitions, stop decorative arrow/ribbon/ring/torch animation updates, and snap camera height/orientation instead of easing when applicable.

Evidence: [L351](source-demo.html#L351), [L1188](source-demo.html#L1188), [L3086](source-demo.html#L3086), [L3189](source-demo.html#L3189), [L3215](source-demo.html#L3215), [L3229](source-demo.html#L3229). **Static source evidence.**

Check: Inspect the media-query initialization, CSS override and animation guards.

Boundary: The render loop, auto-walk and input-driven camera movement continue. This is reduced decorative motion, not a guarantee of no motion.

### SR-23 — Navigation UI accessibility affordances

Provide a skip link, visible focus styling, labeled controls, pressed/selected/expanded states, drawer tabs and dialog roles; permit Escape to close the drawer and dialogs.

Evidence: [L89](source-demo.html#L89), [L380](source-demo.html#L380), [L400](source-demo.html#L400), [L591](source-demo.html#L591), [L771](source-demo.html#L771), [L813](source-demo.html#L813), [L2650](source-demo.html#L2650), [L2886](source-demo.html#L2886). **Static source evidence.**

Check: Inspect markup and attribute updates.

Boundary: No modal focus trap, focus restoration, inert background or complete ARIA tab keyboard pattern is implemented. Accessible markup alone does not establish usability or conformance.

### SR-24 — Escort request demonstration

Open an assistance dialog with five request categories, a route-segment-start waypoint, fixed coordinate text and active destination. Confirming reveals a fixed ticket/ambassador/three-minute message and announces it.

Evidence: [L789](source-demo.html#L789), [L798](source-demo.html#L798), [L3111](source-demo.html#L3111), [L3123](source-demo.html#L3123). **Static source evidence; simulated service.**

Check: Trace dispatch handler: it only changes a CSS class and announces a string.

Boundary: The assistance dropdown value is never read by dispatch. No ticket is created or transmitted; coordinates are not measured, no ambassador is contacted, and the displayed support contact is unverified.

### SR-25 — Embedded specification and local export

Display the embedded requirements panel, offer re-running six built-in checks, and export a fixed Markdown specification via Blob and an object URL.

Evidence: [L813](source-demo.html#L813), [L2744](source-demo.html#L2744), [L2831](source-demo.html#L2831), [L3129](source-demo.html#L3129). **Static source evidence.**

Check: Inspect the check list, spec-modal handlers and Blob download code.

Boundary: The exported text repeats authored claims; it does not derive a new specification or include the current verification evidence. Built-in tests do not establish real-world accessibility.

### SR-26 — Initialization and responsive rendering

On window load, calculate the default route, run the built-in checks, and start requestAnimationFrame rendering. Resize renderer/camera with the window; adjust mini-map dimensions at the 640 px CSS breakpoint.

Evidence: [L365](source-demo.html#L365), [L3142](source-demo.html#L3142), [L3150](source-demo.html#L3150), [L3271](source-demo.html#L3271). **Static source evidence.**

Check: Inspect initialization order, resize handler and responsive styles.

Boundary: The label “60FPS” is not enforced by a performance check or adaptive quality mechanism.

### SR-27 — Integration and persistence boundary

Keep route settings, current pose and demo interactions in browser memory. This file contains no application API client, login flow, persistent settings storage, Azure service calls, GitHub calls or city-dataset loader.

Evidence: [L9](source-demo.html#L9), [L14](source-demo.html#L14), [L17](source-demo.html#L17), [L1158](source-demo.html#L1158), [L2713](source-demo.html#L2713), [L3111](source-demo.html#L3111). **Whole-file static inspection.**

Check: Reviewed application network/storage/API references: only external static dependencies and device media APIs are present.

Boundary: No connection to the previously collected curb-ramp/traffic datasets is implemented. CDN availability is required unless assets are separately bundled; reloading resets state.

## User requirements: qualitative intent

These statements express intended outcomes. They are not assurances that the current demo delivers those outcomes.

### UR-01 — Understand directions naturally

As a spectator, I want directions in my forward view so I can navigate without mentally rotating a stadium map.

Basis: [L831](source-demo.html#L831), [L844](source-demo.html#L844), [L1948](source-demo.html#L1948), [L2220](source-demo.html#L2220); strong intent evidence. Supports: SR-09,SR-10,SR-11.

Proposed user validation: observe representative users finding a destination using cues; measure wrong turns, assistance needed and reported confidence. Agree targets with users.

Current gap: The existence of arrows does not establish comprehensibility.

### UR-02 — Trust a route suited to mobility needs

As a wheelchair or mobility-device user, I want routes that respect my access needs so I can travel confidently and with dignity.

Basis: [L627](source-demo.html#L627), [L845](source-demo.html#L845), [L1088](source-demo.html#L1088); strong intent evidence. Supports: SR-02,SR-04,SR-05,SR-06.

Proposed user validation: review verified end-to-end paths with mobility-device users, including crossings, widths, landings, entrances, lifts and closures.

Current gap: Only the modeled stairs/slope exclusion is implemented. Trust and physical accessibility remain unvalidated.

### UR-03 — Choose useful destinations

As a spectator, I want to find accessible seating, club access, companion-care facilities and a quiet room from a recognizable entrance.

Basis: [L605](source-demo.html#L605), [L614](source-demo.html#L614), [L895](source-demo.html#L895); inferred from available choices. Supports: SR-02,SR-03.

Proposed user validation: confirm the destination vocabulary and facilities with attendees and venue staff, then test selection tasks.

Current gap: The preset destinations are not a complete or independently verified venue directory.

### UR-04 — Choose sensory and environmental comfort

As someone sensitive to noise or sun exposure, I want quieter or shadier options and a quick way to find a calm space.

Basis: [L635](source-demo.html#L635), [L845](source-demo.html#L845), [L1093](source-demo.html#L1093), [L3043](source-demo.html#L3043); strong intent evidence. Supports: SR-04,SR-06,SR-10,SR-20.

Proposed user validation: compare perceived comfort and acceptable detours using verified shade/noise conditions and participant preferences.

Current gap: Weights use fixed metadata, do not guarantee globally minimum noise or maximum shade, and are not live measurements.

### UR-05 — Receive directions through usable channels

As a blind, low-vision, deaf or hard-of-hearing spectator, I want equivalent directions through visual, spoken and nonvisual cues so I can use the channels available to me.

Basis: [L846](source-demo.html#L846), [L1205](source-demo.html#L1205), [L1231](source-demo.html#L1231), [L2713](source-demo.html#L2713); strong intent evidence. Supports: SR-10,SR-17,SR-18,SR-19,SR-23.

Proposed user validation: test core navigation tasks with screen readers, speech/audio cues and text under representative venue conditions.

Current gap: Caption content is simulated; audio output and screen-reader access have not been user-tested and do not prove equivalent access.

### UR-06 — Adapt visibility and motion

As a user with visual or motion sensitivity needs, I want adjustable contrast, text, arrow size and motion so directions remain legible and comfortable.

Basis: [L726](source-demo.html#L726), [L3054](source-demo.html#L3054), [L3070](source-demo.html#L3070), [L3079](source-demo.html#L3079), [L3086](source-demo.html#L3086); strong intent evidence. Supports: SR-14,SR-21,SR-22.

Proposed user validation: test readability, contrast and motion comfort across device sizes, lighting and simulated/live-camera backgrounds.

Current gap: No fixed contrast-compliance result or usability target is inferred from labels.

### UR-07 — Preview and control the journey

As an attendee preparing for a visit, I want to preview a route at a suitable pace and viewpoint, pause it, inspect surroundings and revisit waypoints.

Basis: [L515](source-demo.html#L515), [L831](source-demo.html#L831), [L847](source-demo.html#L847), [L2907](source-demo.html#L2907), [L2938](source-demo.html#L2938), [L2969](source-demo.html#L2969); strong intent evidence. Supports: SR-03,SR-12,SR-13,SR-14.

Proposed user validation: have users rehearse a trip, change viewpoint/speed and resume without losing orientation.

Current gap: Playback demonstrates the virtual route, not actual travel time or physical positioning.

### UR-08 — Keep guidance while using a camera

As an attendee, I want a familiar transition from preview to camera-based guidance, with a usable fallback when camera access is unavailable.

Basis: [L847](source-demo.html#L847), [L2566](source-demo.html#L2566); strong intent evidence; partially supported. Supports: SR-08,SR-15,SR-16.

Proposed user validation: test permissions, fallback and switching on representative devices; separately verify real-world registration before navigation use.

Current gap: Video overlay exists in source, but physical alignment and positioning are absent. A camera overlay is not a verified on-site AR navigator.

### UR-09 — Keep the display understandable and calm

As a spectator, I want essential instructions to be prominent while optional details can be collapsed so I can see the path and avoid information overload.

Basis: [L848](source-demo.html#L848), [L2444](source-demo.html#L2444), [L2886](source-demo.html#L2886), [L3001](source-demo.html#L3001); strong intent evidence. Supports: SR-09,SR-10,SR-11,SR-23.

Proposed user validation: measure task completion, missed hazards and perceived overload on small/large screens with and without panels open.

Current gap: The stated >75% unobstructed viewport is not measured or enforced and is not adopted as a proven requirement.

### UR-10 — Ask for appropriate human assistance

As a spectator needing help, I want to request the appropriate assistance with location context and receive a trustworthy status update.

Basis: [L789](source-demo.html#L789), [L798](source-demo.html#L798), [L3111](source-demo.html#L3111); strong intent evidence; service mocked. Supports: SR-24.

Proposed user validation: validate dispatch workflows, acknowledgement, failure handling and location accuracy with venue accessibility staff and users.

Current gap: The current confirmation is a UI demonstration, not a completed request or genuine ETA.

## Embedded claims that must not be promoted to implementation facts

| Claim in the demo | What the implementation establishes | Remaining gap |
|---|---|---|
| “Authentic” metric Coliseum, facility locations and operating support contact | Fixed node coordinates, names, scene geometry and text | No survey provenance, authoritative facility verification, date/version control or operational confirmation |
| “ADA compliance”, step-free trust, no narrow bottlenecks | Graph edges with stairs or slope metadata >8.33 are filtered | Width, cross-slope, landings, handrails, current condition, closures and actual facility usability are not modeled; a threshold alone is not full ADA conformance |
| “Live” camera AR wayfinding | Camera video can replace the simulated background | No position tracking, georeferencing, world anchors, SLAM, WebXR registration or obstacle detection |
| “Live” captions and sensory telemetry | Fixed bilingual caption arrays and modeled noise attributes | No live event, microphone or sensor feed |
| Ambassador dispatched, real ETA and ticket | Local confirmation text and a speech announcement | No request transmission, server acknowledgement, queue or assistance-specific behavior |
| WCAG AAA / >=7:1 contrast | Palette toggles, some ARIA metadata, focus styles and display options | No contrast calculation or complete accessibility audit; no modal focus management or user validation |
| >75% unobstructed viewport | Full-window canvas and hideable panels | No viewport-area measurement, acceptance test or all-device guarantee |
| “60FPS” | requestAnimationFrame loop and a capped frame-time integration step | No measured performance target enforcement |
| “Self-contained”, “WebGL2” export | One HTML file with externally loaded assets and Three.js WebGLRenderer | Not a bundled/offline application; code does not explicitly require a WebGL2 context |

## Verification performed and limits of built-in checks

The repeatable check is `node verify-routes.cjs > route-verification.json`. It executes the unchanged graph section in a restricted Node VM without browser/device calls. The script evaluates actual route results and fails on missing routes, wrong endpoints or forbidden step-free edges.

| Check | Result |
|---|---|
| Graph size | 26 nodes, 32 bidirectional edges |
| Three starts × five destinations × two step-free settings × two noise settings × two shade settings | 120 route configurations executed successfully |
| Step-free configurations | 60/60 found routes with no stair edges and no traversed edge slope metadata >8.33% |
| Default Gate 29 → Section 308, step-free | 92.3 m; 0 stair edges; 1 elevator run; modeled max grade 5.8% |
| Same endpoints, standard | 86.2 m; 2 stair edges; 0 elevator runs; modeled max grade 34% |
| Shade option | Changes 14 of 60 paired route comparisons in this graph |
| File's specific low-sensory example | Same path and same modeled average noise with the option on/off: 64 dB in both cases |
| Invalid route endpoint | Returns null |

The file's own six checks are not independent acceptance evidence. This review did not execute its whole browser verification panel. Static inspection of its predicates shows:

- **VC-1:** checks route existence and returned summary stair/grade values for 15 default step-free pairs, not all preferences or real-world conditions. Our route check additionally inspects each traversed edge across all 60 step-free configurations.
- **VC-2:** checks a step-free route has no stair edges, a standard route has some, and a lift exists. Its predicate does not confirm the specifically advertised Tunnel 9 alignment or rendered visual divergence. The graph example does use Tunnel 9.
- **VC-3:** checks array counts (at least six chevrons and one beacon), not actual visible rendering, occlusion, legibility or placement in the physical environment.
- **VC-4:** checks the active target eye-height value, not transition behavior, both switch states or a real person's calibration.
- **VC-5:** checks WebGL alpha capability and the overlay group's scene parent, not camera permissions, camera playback, spatial alignment or real hardware operation.
- **VC-6:** accepts modeled average noise that is less than **or equal to** the baseline, so the unchanged 64 → 64 dB example qualifies. It never enables maxShade or tests shade despite mentioning it in the displayed question.

## Implementation discrepancies worth tracking separately

These are findings from this version, not additional implemented requirements or authorization to fix the demo.

1. **Simulated support is presented as real dispatch.** An operational build needs a genuine service or unmistakable demo labeling; selecting an assistance type currently has no dispatch effect (SR-24).
2. **Sensory shortcut can mislabel standard mode as step-free.** It does not force the step-free switch on (SR-20).
3. **Surroundings description can contradict active mode.** Its fixed template describes emerald step-free guidance even when standard/high-contrast settings differ (SR-17).
4. **No-route branch retains the previous route.** A future unavailable path could leave old instructions visible (SR-07).
5. **Manual exploration is detached from route progress.** Navigation instructions can describe the old segment while the user moves freely; there is no collision or localization engine (SR-13).
6. **Camera playback-failure cleanup is incomplete.** If capture succeeds but video playback fails, the catch branch does not explicitly stop the acquired tracks (SR-15).
7. **Global Space handling can conflict with button activation.** The keyboard shortcut ignores inputs/selects/textareas but not focused buttons (SR-13).
8. **Dialog/tab semantics are incomplete.** Roles and labels exist, but focus trapping/restoration and full tab keyboard interaction are absent (SR-23).

## What is outside this codebase

Azure hosting and identities, GitHub integration, a database, authenticated services, real-time crowds/noise/lift status, validated indoor positioning, traffic feeds, authoritative venue GIS and the previously collected curb-ramp dataset are all absent. They should be proposed as future work only after deciding the class demonstration's goals. The current report does not turn them into user-approved requirements.

## Files

- `requirements.csv` / `requirements.json`: 27 system and 10 user requirements, with stable IDs, evidence line numbers, status, checks, limitations and traceability.
- `source-demo.html`: unmodified evidence copy of the uploaded HTML.
- `verify-routes.cjs` / `route-verification.json`: repeatable pure-graph check and its 120 detailed results.
