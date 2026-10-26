# Modular Building System: Walter's House Prototype

Version **0.1.0**, pack ID `willow-modular-building-001`. This bounded prototype
contains 16 new original building modules, a 6 x 8 m Walter house and a 6 x 4 m
alternative assembled from the same inventory. The alternative changes the
entrance, porch, window layout and configured colours without introducing a new
module mesh. All dimensions below are metres.

The branch starts from main commit
`8fd7379a6ce1023cf8fd7a690bad0f5ac5bed33f`. Geometry and materials are authored
with deterministic Blender Python, with no manual mesh edits, purchased assets,
external meshes, textures, HDRIs or generation services. Keep future changes in
the scripts and versioned [configuration](../../configs/modular-building.json).

## Inventory and connection contract

This is a **proposed building-specific contract**. It preserves authored grid
anchors rather than applying the generic bottom-centre prop pivot rule. The
provisional [art contract](../ART_CONTRACT.md) is unchanged; game acceptance of
these building anchors and import behaviour remains open.

Source axes are X right, Z up, exterior front -Y. GLB axes are X right, Y up,
front +Z: source `(x, y, z)` becomes GLB `(x, z, -y)`. Configuration bounds and
`dimensionsMeters` are **exported GLB X/Y/Z**, whereas collision boxes and
explicit `SourceXYZ` metadata use Blender source coordinates. Root transforms
are identity, scale 1; placements belong to instances. Unity must apply its
normal glTF handedness conversion, without an extra art-side reflection.

| Asset ID | Connection anchor and purpose |
| --- | --- |
| `bld_wall_solid_200_001` | Bay bottom centre; 2 m span, 2.8 m wall height |
| `bld_wall_window_200_001` | Same bay; genuine 1.10 x 1.25 opening, sill 0.85 above floor |
| `bld_wall_door_200_001` | Same bay; genuine 1.10 x 2.20 opening from floor |
| `bld_corner_trim_001` | Wall intersection at bottom; rotate in 90-degree increments |
| `bld_floor_200_001` | Tile bottom centre; 2 x 2 plan, 0.18 thick |
| `bld_foundation_200_001` | Strip bottom centre; 2 m span, 0.42 high |
| `bld_porch_200_001` | Bay bottom centre; 2 x 2 nominal plan, deck at 0.60 |
| `bld_porch_steps_001` | Back-edge centre at ground; three 0.20 risers, extends toward -Y |
| `bld_porch_post_001` | Foot centre on porch; 2 m tall, includes broad knee braces |
| `bld_roof_half_200_001` | Ridge baseline at bay centre; 2 m longitudinal span, positive-X half |
| `bld_roof_ridge_200_001` | Same ridge baseline; independent 2 m cap |
| `bld_gable_end_600_001` | Wall-top centre; 6 m structural span, separate wall infill |
| `bld_gable_trim_600_001` | Same gable baseline; open-centred roof edge, no wall fill |
| `bld_porch_canopy_200_001` | Rear wall/top datum; 2 m X bay, extends toward -Y |
| `bld_window_110_001` | Opening-bottom centre; frame/sill extends to Z=-0.07 |
| `bld_door_100_001` | Opening-bottom centre; identity root with separate frame and leaf |

Exact per-module bounds, seeds, triangle limits, material colours and collision
proposals are in the configuration. Structural walls are 0.18 thick; clapboard
projects beyond that thickness. The 2 m grid uses touching module ends without
negative scale. The roof is deliberately limited to a **6 m house span** and
1.8 m rise; its overhang is 0.35 at each eave. Rotate the second roof half 180
degrees around source Z rather than mirroring its scale.

The walkable floor is source/world Z=0.60: foundation height 0.42 plus floor
thickness 0.18. Walls start at 0.60 and end at 3.40. Main roof and gable anchors
start at 3.40. The canopy rear datum is 3.10; porch deck and stair top are 0.60.
The upper silhouette suggests an attic; **no upper floor is delivered**.

## Windows, entry and door hierarchy

Window inserts are placed 0.85 above the wall bay root. Four panes are opaque
muted-blue PBR geometry; no transparency or interior lighting is required. The
window root deliberately sits above its sill's lowest geometry. Frame bounds
in source are X +/-0.62, Y -0.16..0.051, Z -0.07..1.32.

The door module has exactly two mesh children: `__frame` and `__leaf`. Frame
bounds are source X +/-0.62, Y -0.13..0.08, Z 0..2.30. Excluding the leaf leaves
a physical passage **0.99 wide x 2.135 high**, above a **0.015 threshold**:
source X -0.495..0.495, Z 0.015..2.15. The frame has no opaque backing across
this passage. The wall aperture is larger than the finished clear passage.

The leaf origin is the lower hinge, source `(-0.48, 0, 0.015)` relative to the
door module. Its rotation axis is source +Z / exported +Y. Its body is 0.96 wide,
2.12 high and 0.045 thick; panels, hinges and brass handle extend beyond the
body. Its local body bounds are X 0..0.96, Y -0.05..-0.005, Z 0..2.12. Root and
child extras record the clear bounds, component identity and hinge. The closed
pose is static: no door animation, rig, interaction or controller is provided.

Proposed source/world entry anchors are `(0, -0.5, 0.6)` for Walter and
`(2, -0.5, 0.6)` for the alternative, exported as `(0, 0.6, 0.5)` and
`(2, 0.6, 0.5)`. These presentation markers require game-owned portal alignment.

## Assemblies, hiding and collision

Assembly instances retain `moduleId` and `hideGroup` extras. `roof` includes
roof halves, caps, bargeboards and porch canopies. `wall.south`, `wall.north`,
`wall.east` and `wall.west` include their matching openings/inserts; gable wall
infill belongs to its end wall. Corner trims have separate `corner.*` groups.
Floors, foundation and porch remain independent. The cutaway previews hide
matching corner trims with selected walls. This is hierarchy/metadata for a
future importer, **not a runtime camera or visibility implementation**.

Collision definitions are proposals, not authored Unity components. Wall
`compound-boxes` contain separate piers, lintels and window sill regions, with
no box crossing an opening. Use floor-tile boxes and separate step boxes;
evaluate a navigation ramp in the game if desired. The door leaf needs its own
future collider and state handling; optional roof collision stays separate.
Never apply a house-wide solid BoxCollider that blocks the interior or doorway.
Decorative trim, glazing, braces and plants need no walking collision.

Suggested source-space envelopes for the other walking surfaces are floor
2 x 2 x 0.18, porch 2 x 2 x 0.60, foundation 2 x 0.32 x 0.42, and three
separate stair boxes 1.40 wide x 0.30 deep with 0.20/0.40/0.60 heights.
Use only the 0.13 x 0.13 x 2.00 post shaft for optional post collision;
braces stay decorative. Window and corner trim need no extra walking collider.
The hinge-local door body box is X 0..0.96, Y -0.05..-0.005, Z 0..2.12.

## Existing prop provenance and pins

The 16 building modules are new work from main. Presentation props are existing
project-owned assets regenerated from **unchanged source snapshots at their
canonical paths**, not remodelled variants. All required snapshots are included
in this PR, so a build has **no dependency on checking out an unmerged branch**.
PR #34 and PR #36 retain their own approval/merge decisions.

The ten porch/garden props come from [PR #36](https://github.com/bobo91/life-sim-art/pull/36),
source commit `b290bcf5702344d1a911cd31f793f77d8cafcbaf`:
`prop_porch_bench_001`, `prop_flower_pot_001`, `prop_flower_pot_002`,
`prop_welcome_mat_001`, `prop_porch_lantern_001`, `prop_wooden_fence_001`,
`prop_fence_post_001`, `prop_old_watering_can_001`, `prop_wooden_crate_001` and
`prop_porch_rocking_chair_001`. They use `scripts/props_walter.py`,
`scripts/walter_common.py` and their corresponding `configs/<assetId>.json`.
The script snapshot SHA256 pins are:

```text
props_walter.py  2fc086ba351d9efdfb141a1847a988583f547622e29dcb977702a45563660146
walter_common.py 0f3a1d5b844c7034e012b50a58804f681dbfcaa70fc01dce3590321ba04e7417
```

The mailbox is the approved `prop_mailbox_001` from
[PR #34](https://github.com/bobo91/life-sim-art/pull/34), source commit
`96eb13ada9bab56a3c8cfa5de307a16753025f65`, with these existing pins:

```text
Approved GLB                  b243a55a5d92da3cd3a51c3957d0b1e1f1b9737ad8f6ed988121bae69e654698
walter_mailbox_reference.py    b76d773d1cdd9e5d0470d9a5f0d2784b5be92ef608e0a55f20873521f272f63c
walter-mailbox-reference.json  3f2ba255a195e4271c2d775f66eaa10c34179927d3e9018f89e1afc451d52af7
```

The new build records source/config hashes and each delivered GLB/Blend hash in
its own manifests; a regenerated container's hash must be measured rather than
assumed to equal an earlier exporter build. Content provenance is original
project geometry/materials with no third-party asset licence dependency. No
broader public asset licence is granted by this technical document.

## Reproduction and review artifacts

Use **Blender 4.5.14**, Python 3.11+ and Pillow 12.3.0. Run from the repository
root, with `BLENDER_BIN` set to the pinned Blender executable. The worker uses
offline mode, factory startup, disabled autoexec and CPU Cycles with four
threads. No GPU or paid service is required. Each output directory must be new;
prior evidence is preserved.

```text
python -m unittest discover -s tests -v
python scripts/run_modular_building.py --blender <Blender4.5.14> --output build/modular-building/review-001
python scripts/compose_modular_building.py --input build/modular-building/review-001 --output build/modular-building/review-001/review
python scripts/package_modular_building.py --input build/modular-building/review-001 --output build/artifacts/modular-building-v0.1.0-review.1.zip
```

The [Linux workflow](../../.github/workflows/modular-building.yml) installs the
official checksum-pinned Blender distribution and runs the same sequence.
Platform-specific floating-point pixels and container bytes may differ; use
the recorded tool versions, source hashes and validation outcomes to assess a
reproduction. Configured bounds are checked independently to 1 mm without
rewriting delivered module coordinates.

The bundle contains separate module GLBs and editable Blends; front/isometric
module previews; assembled house GLBs/Blends; reused prop sources; manifests;
geometry, persistence and roundtrip reports; six house views; and the module
contact sheet. `walter-house.blend` contains the architecture; the additional
`walter-presentation.blend` opens the full prop presentation and lighting.
The six views are three-quarter, 16 m game-perspective proxy, 6 m entry,
roof hidden, selected walls hidden, and alternative house. The contact sheet
uses the actual module renders. The game camera reference is perspective,
vertical FOV 40 degrees, pitch 50 degrees and yaw 180 degrees; the hero view is
a separately framed three-quarter composition. The 16 m distance is measured
to the explicit building review anchor `(0, 0.7, 3.35)`, recentered to fit the
whole house and yard props. It is not a screenshot of Unity's player-follow
camera. The 6 m entry inspection uses pitch 15 / yaw 168 so the canopy does not
hide the door. Every camera and view hash is recorded in `presentation.json`.
Each assembly shares nine opaque PBR palette roles through object material
overrides, preserving the same module mesh data for the alternative palette.

Packaging requires successful validation, verifies recorded input and asset
SHA256 hashes, and reads the ZIP back to verify every archived file. A SHA256
sidecar and file index accompany the versioned artifact. Large GLBs/Blends stay
in the downloadable artifact rather than ordinary Git blobs. Current measured
outcomes, image paths and the final artifact link belong in the
[quality report](../../reports/modular-building-v0.1.0/quality-report.md); this
document describes the reproducible contract, not an unrecorded test claim.

## Deliberate limits and game handoff

This proves two layouts at one width and roof pitch, not a general building
generator. There is no furnished interior, staircase/upper floor, transparent
window view, lighting bake, LOD system, weathering texture or complete doorway
gameplay. Parts are closed procedural solids; intentional construction joints
and overlaps are not a Boolean-unioned watertight house shell.

**Unity import, URP appearance, navigation, collision layers, runtime hiding,
door operation and game camera behaviour are not verified by Blender renders
or GLB roundtrips.** Importer/version selection and those integration decisions
remain game-owned and are recorded as open decisions. No game repository code
is changed. This PR requires visual review; no automatic merge is authorised.
The existing style stays warm and restrained, with broad siding, cream trim,
muted roof colours and details sized to read at approximately 16 m.
