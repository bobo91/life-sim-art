# Art direction v0.2 - ART-002 proposal

This is the proposed visual bible for an original stylized low-poly adult life
simulator set in a contemporary fictional American small town. The working
preference is **civic_sage**. Neither palette nor the production direction has
human visual approval yet. ART-002 establishes a reviewable benchmark; it does
not approve the lamp for ART-003 or authorize mass production.

## Visual intent and shape language

Build a town that feels inhabited, warm and practical: quiet painted surfaces,
weathered warm neutrals, restrained vegetation, and small amber accents. Adult
characters and recognizable construction dimensions anchor the scale. Readable
silhouettes, broad material groups and a few deliberate edge breaks carry detail
at a high-angle gameplay camera.

Use broad planes with visible lighting response, tapered supports, controlled
roof overhangs, and trim that explains construction. Keep geometry concentrated
on silhouette, contact with the ground, and features visible at gameplay distance.
Flat face normals are appropriate on faceted surfaces; a smooth surface requires
an intentional normal treatment and a comparison render. Use irregularity in
small, seeded amounts without moving modular attachment points.

Avoid photorealistic noise, inflated toy proportions, featureless unshaded
primitives, dense surface greebles, extreme bevels, and an unrelated palette for
each object. Do not reproduce the recognizable construction or composition of
commercial asset packs. All production meshes and materials originate in our
procedural scripts; no premade meshes, purchased packs, imported texture sets,
HDRIs, or manual modeling enter the workflow.

## Palette and material library

Hex colors below are **sRGB authoring values**. The generator converts them to
linear RGB for Blender's Principled BSDF. AgX changes the rendered appearance;
a screenshot is not a source color sample. Material roles express presentation,
not gameplay state or persistent asset identity.

The machine-readable benchmark library is [materials/library.json](../materials/library.json).
Its four roles map to the lamp generator's fixed material slots. Both proposed
variants use identical geometry, seed 1701, dimensions 0.64 x 3.20 x 0.64 meters,
roughness, metallic values, camera and lighting. Only palette color and variant
asset identity differ. The unchanged amber and fastener colors provide common
anchors for comparison.

| Semantic role / generator slot | civic_sage | harbor_slate | Roughness | Metallic | Purpose |
|---|---|---|---:|---:|---|
| `surface.civic.metal` / `metal` | `#344A48` | `#394B5A` | 0.64 | 0.45 | Painted civic metal; main quiet silhouette |
| `surface.civic.edge` / `edge` | `#70827A` | `#82939C` | 0.57 | 0.35 | Restrained construction trim and service plate |
| `surface.lantern.amber` / `glass` | `#EFC88A` | `#EFC88A` | 0.32 | 0.00 | Warm pane color visible at distance |
| `surface.hardware.warm` / `fastener` | `#A9A08B` | `#A9A08B` | 0.48 | 0.60 | Small hardware accents |

`civic_sage` is provisionally preferred because the muted green relates readily
to planting and warm siding while the amber remains the focal accent.
`harbor_slate` tests a cooler, slightly more formal municipal character. The
preference is a proposal, not a claim that a reviewer has accepted the renders.
A choice should be made from the actual comparison sheet and small-size view.

The following original town roles are **proposed authoring extensions**, not
materials already implemented or assets already delivered. Validate each role
on the first relevant ART-003 model before freezing the library.

| Proposed role | sRGB | Roughness | Metallic | Intended use |
|---|---|---:|---:|---|
| `surface.building.siding` | `#D8CBB2` | 0.78 | 0.00 | Warm neutral siding and broad wall planes |
| `surface.building.trim` | `#E5DDCC` | 0.68 | 0.00 | Window/door trim; avoid pure white |
| `surface.building.roof` | `#6B554D` | 0.86 | 0.00 | Muted brown roof masses |
| `surface.foundation.stone` | `#9D9C8D` | 0.88 | 0.00 | Foundations and plain masonry |
| `surface.paving` | `#909690` | 0.92 | 0.00 | Neutral path/paving masses |
| `surface.wood` | `#8B634B` | 0.82 | 0.00 | Broad timber surfaces |
| `surface.tree.bark` | `#755443` | 0.92 | 0.00 | Readable warm trunk |
| `surface.tree.foliage` | `#7B8A5C` | 0.90 | 0.00 | Main canopy planes |
| `surface.tree.foliage_light` | `#A7B476` | 0.90 | 0.00 | Sparse lighter canopy groups |
| `surface.tree.foliage_shadow` | `#4E6651` | 0.92 | 0.00 | Limited inner canopy groups |

Use approximately 70 percent quiet base surfaces, 25 percent supporting material
variation and at most 5 percent strong accents as a composition guide, not a
pixel-count gate. Adjacent functional pieces need a value or silhouette change;
color alone must not carry an interaction cue. Do not bake key-light highlights
or contact shadows into base colors.

### Surface and texture strategy

For the benchmark, use core glTF opaque metallic/roughness materials, authored
normals and no textures. The role named `glass` is deliberately opaque amber:
there is no transmission, emission or nighttime illumination test. It is a
readability proposal rather than a physically accurate lantern pane.

Prefer a small shared role palette over a unique material per part. Initial
material-slot targets are four for a civic prop, six for a house, and four for a
tree. Reuse role values across assets; a new slot needs a visible purpose. Keep
collision proxies, runtime light behavior and interaction markers separate from
visual materials and outside this benchmark.

Textures are deferred until they solve a demonstrated readability problem. A
future self-generated texture workflow should target 128 texels per meter for
large surfaces, a 512-square shared atlas for small props, and at most a
1024-square atlas for a first house. These are proposed caps, not a claim that
textures/UVs or texture validation exist in ART-001. Do not add photographic
textures or downloaded atlases to fill this gap.

## Scale, proportions and modular sizes

Delivery uses meters and exported X width, Y height, Z depth. Buildings and props
use a bottom-center pivot. Blender source is Z-up/-Y-forward; export produces
+Y-up/+Z-forward glTF. The asymmetric service plate marks the benchmark's front.
Unity importer handedness conversion remains a game-repository integration test.
See [ART_CONTRACT.md](ART_CONTRACT.md) before changing the contract.

These dimensions are proposed art authoring targets. Gameplay collision sizes,
navmesh clearance and interaction ranges remain game-owned. Confirm them with
the game repository before an asset request becomes production work.

| Element | Proposed reference |
|---|---|
| Adult reference | 1.75 m height; ordinary adult range 1.55-1.95 m; about 7-7.5 heads tall |
| Character shape | Clear shoulders/hips and grounded feet; expressive head/hands without childlike head-to-body proportions |
| Main building grid | 0.25 m; place structural connections on grid |
| Trim/detail increment | 0.05 m; never shift structural connectors to add variation |
| Story height | 3.00 m floor to floor; about 2.60 m interior clear height |
| Exterior door reference | 0.90 m clear width x 2.10 m clear height |
| Window module reference | 1.00 m width x 1.20 m height; 0.90 m sill height |
| First house envelope | 8.00 x 6.00 x 5.00 m in exported X,Y,Z; 8 x 5 m footprint and 6 m total height |
| House construction | 0.30 m roof overhang; 0.20 m visible foundation reference |
| Benchmark streetlamp | 0.64 x 3.20 x 0.64 m exported bounds; explicit 3.20 m height |
| First tree target | About 5.00 m height, 3.00 m canopy diameter; trunk width 0.25-0.40 m |

The house envelope preserves the canonical contract example's array [8,6,5]
in explicit exported X,Y,Z order. The canonical example does not label each
component, so confirm this interpretation across repositories before production.
It is not a generated house.
Do not round a contractual requested dimension to a prettier proportion; update
and reconcile the request if a different size is needed.

## Geometry and LOD budgets

Budgets count **exported triangles**, including trim and hardware. They are
initial per-asset authoring caps, not proof of game performance. Record actual
triangles, exported bounds, material slots and file bytes in the manifest.
A silhouette or shadow improvement can justify spending triangles; invisible
microdetail cannot. Keep closed components where useful, disclose intersections,
and avoid duplicate/degenerate faces, loose vertices and inverted normals.

| Asset class | Proposed LOD0 cap | Future LOD1 cap | Future LOD2 cap | Material-slot target |
|---|---:|---:|---:|---:|
| Small civic prop / streetlamp | 2,400 | 1,200 | 400 | 4 |
| First detached house | 12,000 | 6,000 | 2,000 | 6 |
| First medium tree | 2,000 | 1,000 | 350 | 4 |
| Adult feasibility prototype | 16,000 | 8,000 | 3,000 | 6 |

Only the streetlamp's LOD0 budget is exercised by the current generator. No LOD
meshes or runtime LOD switching are delivered by ART-001/002. Adult topology,
skinning, rig hierarchy and animation need the separate ART-004 humanoid contract.
Future LOD generation must preserve pivot, bounds and silhouette and use measured
screen coverage rather than an arbitrary universal world-distance switch.

## Controlled render benchmark

Use the verified ART-001 pipeline and [scripts/render_benchmark.py](../scripts/render_benchmark.py).
A render compares variants only if geometry/source digest, dimensions, seed,
Blender build and all scene/render settings match. Asset IDs may differ to keep
variant bundles distinct. Check actual metrics in each manifest; do not infer
equal geometry merely from equal triangle counts.

Reference: Blender 4.5.14 LTS, CPU Cycles, one render thread, 640 x 640 pixels,
64 samples, seed 1701, denoising off, AgX, exposure 0, gamma 1, opaque background.
ART-001's original pipeline evidence uses 32 samples; both ART-002 candidates use
the higher 64-sample setting together.
Other color management settings use the pinned factory-startup defaults. These
images evaluate material response; they are not a Unity render or an approved
in-game lighting setup. Comparison across operating systems/builds has no
byte-identical pixel guarantee.

For asset height `h`, target `(0, 0, 0.49*h)` in Blender source coordinates:

- Front: camera `(0, -2.5*h, 0.49*h)`, looking toward the target.
- True isometric: target plus `(2*h, -2*h, 2*h)`, giving 45 degrees azimuth
  from the front and 35.264 degrees elevation.
- Orthographic scale: `1.25*h`, square frame; retain full silhouette and ground
  contact without cropping.

Three disk area lights aim at `(0, 0, h/2)`. At reference height 3.20 m, use:

| Light | Blender position in meters | Power | Diameter | Linear RGB |
|---|---|---:|---:|---|
| Key | `(-3, -4, 6)` | 650 W | 4 m | `(1.00, 0.89, 0.74)` |
| Fill | `(4, -1, 4)` | 350 W | 5 m | `(0.75, 0.85, 1.00)` |
| Rim | `(1, 4, 5)` | 500 W | 3 m | `(1.00, 0.95, 0.84)` |

For other heights, multiply positions and light diameters by `h/3.2` and power by
`(h/3.2)^2`. World background is linear RGBA `(0.32, 0.36, 0.40, 1)` at strength
0.45. The floor is `#D6D1C3`, roughness 0.9, metallic 0, at source Z = -0.005 m.
The floor/lights/camera are preview-only and must not enter the exported asset.

Keep the front and isometric images as the canonical pair. Also inspect a
160 x 160 pixel display of the same full frame to approximate distant readability
without changing the lighting; label that view as a display-size check, not a
measured game-camera distance. The lantern/base/post should remain distinct;
small fasteners may disappear. A future game-camera review must record its own
projection, zoom, viewport and actual on-screen asset height.

### Actual comparison renders

The following images come from the procedural pipeline; execution results,
checksums and any observed limitations belong in [the benchmark evidence](../evidence/art-002/README.md).
The existence of an image does not constitute visual approval.

| Candidate | Front | True isometric |
|---|---|---|
| civic_sage, preferred proposal | [front](../evidence/art-002/civic_sage/front.png) | [isometric](../evidence/art-002/civic_sage/isometric.png) |
| harbor_slate, alternate proposal | [front](../evidence/art-002/harbor_slate/front.png) | [isometric](../evidence/art-002/harbor_slate/isometric.png) |

Do not describe an unrendered candidate as tested. Preserve the reference
material parameters and render settings when comparing these proposals; a new
lighting look requires its own labeled comparison.

## Review rubric and approval checkpoint

Technical validation and aesthetic judgment are separate gates. Automated passes
establish bundle integrity, not production quality. Record **pass**, **revise** or
**not evaluated** for each item with a specific observation and image reference.
Do not average failures into a score or use a generated aesthetic score as human
approval.

| Review area | Acceptance observation |
|---|---|
| Provenance | Original generator/config/seed/command, source identity and hashes are recorded; no external asset content |
| Technical integrity | GLB/bundle validators pass; dimensions, origin, axes, normals, materials and triangle cap match the request |
| Silhouette | Lamp reads as base, shaft and lantern in both views and at the 160-pixel frame size |
| Material response | Broad planes respond to key/fill; metal, pane and hardware are distinguishable without a texture |
| Value hierarchy | Amber is a controlled focal accent; trim does not turn into a bright outline or hide the main shape |
| Town coherence | Palette belongs with the proposed warm architecture and vegetation; neither candidate reads as a separate visual universe |
| Adult-scale plausibility | Dimensions make sense beside the 1.75 m reference; trim and hardware do not imply toy scale |
| Surface quality | No visible holes, inverted faces, floating trim, objectionable intersections, or unintentionally faceted shading |
| Comparative fairness | Same seeded geometry, renderer, camera and lighting; differences are attributable to palette |
| Integration boundary | Unity import and game-camera performance are explicitly recorded as unverified until tested in the game repository |

**Human visual approval is pending.** Before scaling ART-003 production, a human
reviewer must record the selected palette (or requested revision), observations
for the rubric, the exact evidence/config revision reviewed, and permission to
apply that direction to the first house/tree/lamp set. Also reconcile the art and
game delivery contracts before any production release. Neither pipeline success,
this provisional preference, nor creation/merge of an ART-002 PR supplies that
approval.

Until that checkpoint, keep the comparative lamps labeled benchmarks. Their
remaining limits include opaque non-emissive panes, intersecting closed
construction components, no collision/LODs, no character-scale scene, and no
verified Unity import. These are explicit next review inputs, not claims of
completed production assets.
