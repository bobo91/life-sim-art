# B04 — local elbow topology recovery

**NO-GO for gameplay integration. One candidate was made and rejected at the Blender visual gate. Work stops here.** No B04 GLB, Unity import, PlayMode run or video was produced; these were conditional on both elbows clearly improving without new defects.

## Actual visual evidence

[Run, both elbows and both angles](../../../evidence/male-neutral-b04/previews/run25-both-elbows.png) · [Left/front](../../../evidence/male-neutral-b04/previews/all-poses-L-front.png) · [Left/outer](../../../evidence/male-neutral-b04/previews/all-poses-L-outer.png) · [Right/front](../../../evidence/male-neutral-b04/previews/all-poses-R-front.png) · [Right/outer](../../../evidence/male-neutral-b04/previews/all-poses-R-outer.png) · [50°/16 m comparison](../../../evidence/male-neutral-b04/previews/game16m-comparison.png).

All 75 native PNGs ship in the review archive at `evidence/male-neutral-b04/previews/native/`: 3 versions × (6 poses × 2 elbows × 2 views + one game-camera view). Git retains six comparison sheets and all image fingerprints. These are actual Blender 4.5.14 CPU Cycles renders, 12 samples, identical A03 lighting/materials and shared B02-derived camera targets and bone matrices. Sheets only resize and label the original images. Both the primary review and an independent read-only review reached the same NO-GO.

| Pose | Observed B04 result against B02/B03 |
| --- | --- |
| Idle / walk | New pale facets and step-like ridges at the hinge, particularly left/front and right/outer. |
| Exact run25% | Rounder outer silhouette on both sides, but new abrupt inner shelves/notches. Not a consistent improvement. |
| Physical 45° | New weight-transition ridge appears before a deep bend. |
| Physical 90° | Outer contour improves; inner bend remains pinched and abrupt. |
| Physical 120° | Left inner bend pinches; right/outer shows a conspicuous dark slit. |
| 50° pitch, 16 m | Elbow differences are too small to judge reliably at native 1280×720. This does not invalidate the close-up failures. |

The dark slit is a **visible folding defect**, not proof of a newly opened topological hole. No new boundary edge or non-manifold edge was found; exhaustive posed self-intersection testing was not performed.

The run reference is source frame **5.5**, normalized 0.25, exactly as in B02/B03. Actual idle frame13 is about **26.40°** physical elbow flex, walk frame7 about **26.34°/26.46°**, run about **72.21°/72.69°**. Idle was not silently straightened. The 45°/90°/120° diagnostic poses hold the run upper arm and actual hinge plane fixed; achieved angles differ by less than 0.00003°. B03's original angle activation is evaluated for these same poses. No base animation was edited to obtain a better comparison.

The game-camera image is an **art-side proxy**, not Neighborhood or a Unity screenshot: 16 m Euclidean camera-to-target distance, 50° pitch, 35° azimuth, 40° vertical FOV. The game issue supplies pitch/distance; the remaining settings are documented assumptions.

## What changed

Only `M01_body` near the two elbows was modified. The preserved A03 high body supplies local longitudinal vertex-density quantiles. Seven transverse cuts per side divide existing neutral triangles; a local three-joint weight field blends the existing upper arm, half-angle elbow support and forearm. Original weights outside the small elbow band are retained.

This **adds longitudinal sampling; it does not transplant A03 high's original connectivity or reconstruct its full circumferential topology**. The existing sparse circumference and the piecewise weight field still produce abrupt inner folds. More triangles alone did not establish a usable bend. No second topology or weight recipe was attempted after review.

| Geometry | B02/B03 | B04 | Change |
| --- | ---: | ---: | ---: |
| Body vertices | 2,748 | 3,126 | **+378** (193 L / 185 R) |
| Body triangles | 5,460 | 6,216 | **+756** |
| Whole character triangles | 29,367 | 30,123 | **+756** |
| Bones | 58 | 58 | 0 |

Geometry/UV checks: all original neutral positions are exact; new points are within **0.000000125 m** of the old neutral surface. **5,242 outside triangles** remain; 58 old vertices receive local weight changes. UV interpolation error is at most **0.000000121 UV units**, with zero wrong new loops. Boundary edges remain32 and edges with more than two incident faces remain0; no zero-area face was accepted by the recipe.

The original generation report retains an obsolete UV diagnostic value0.0996. That diagnostic assumed the wrong source loop ordering and one arbitrary UV chart at seams. The read-only corrected check uses actual `loop_triangles.loops` and all geometrically valid source charts. Its result is in [technical-validation.json](../../../evidence/male-neutral-b04/technical-validation.json). Only the diagnostic code changed; the reviewed candidate was frozen throughout.

## Preservation and actual verification

[Saved-file preservation results](../../../evidence/male-neutral-b04/preservation.json) · [Frozen topology report](../../../evidence/male-neutral-b04/topology.json) · [Pose/camera/source metadata](../../../evidence/male-neutral-b04/render-metadata.json).

The focused verifier reopened the preserved B02 and B04 files and **passed**: the other nine meshes (geometry, normals, UVs, weights and material bindings), nine materials/thirteen packed textures, 58 rest bones, object/data names/hierarchy and all four original action curves/keyframes are exact. All original body neutral vertex positions are exact. Local retriangulation can change interpolated normals, and visible local shading/contour defects remain.

Across idle/walk/run/turn at24/96fps, **1,559,910 evaluated shoe-vertex samples per version are exactly equal, maximum displacement0 m**. B02 turn stance speed is retained: maximum0.000000682 m/s at24fps,0.00851136 m/s at96fps. These are maximum sampled sole-centre speeds under the same3mm contact rule, not averages or controller-grounding guarantees. Known walk/run contact limitations are also retained. This is new Blender preservation evidence, **not new Unity validation**.

[In-memory recipe replay](../../../evidence/male-neutral-b04/replay.json) reproduces the frozen B04 body exactly, including index order, weights, UVs and normals, without saving another model or changing the recipe. B02/B04/A03high file SHA256 values are unchanged before/after. The source fix to UV diagnostics therefore did not mask a different candidate.

A03's accepted face, hair, eyes, palette, clothes and proportions were not redesigned. A01/A02/A03/B01/B02/B03 sources and releases are preserved. B04 adds no new morph, bone, animation, external asset or generic framework.

## Integration answers and blockers

[Q1–Q11 response for art #40](B04_INTEGRATION_Q1_Q11.md) includes the B02 GLB hashes, full 58-joint hierarchy, all material slots and colour spaces, proposed import `.meta`, ready CC BY notice, and explicit unknowns. **There is no integration-approved B04 GLB.**

Independent of elbows, the original gait recipe implies approximately0.552 m/s walk and1.533 m/s run. Actual root travel is0 because the clips are in place. Matching the game's fixed4 m/s by playback alone would require7.25×/2.61×, which is not visually validated and implies implausible cadence. Cached glTFast6.20 loops every Mecanim clip, including demonstration turn; omit turn for gameplay. Dense baseline sampling finds up to5.87 mm run sole penetration. Direct run→idle stopping and gameplay performance remain unverified. No B04 animation edits were authorized to address these findings.

## At most two alternatives — not implemented

1. **Pragmatic First Playable option:** retain approved A03 identity with the B02 asset, accept its documented elbow limitation specifically at the fixed distant camera through an explicit owner waiver, and separately authorize a small locomotion-fit task for the real4 m/s controller. This is a quality tradeoff, not a GO delivered by B04; close-up bending remains unsuitable.
2. **If clean close-up bends are mandatory:** authorize one artist-directed local patch that restores actual high-mesh connectivity and solves its binding in posed space, instead of more automatic cross-section cuts or parameter tuning. Keep the existing character and rig. This requires a new bounded scope and has no guaranteed outcome; no purchase, external artist or work is approved here.

Recommendation: **stop elbow experimentation now** and choose the intended close-up quality requirement before authorizing anything else. No automatic B05, game integration, merge or Phase C.

[Reproduction commands](B04_REPRODUCE.md) · [Review-only artifact record](../../../evidence/male-neutral-b04/artifact.json).

Snow Rig (CC) Blender Foundation | studio.blender.org. Modified [Snow v4](https://studio.blender.org/characters/snow/v4/) under [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). No CloudRig/UI code is included or executed. No life-sim-game changes.
