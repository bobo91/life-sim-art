# Cafe Environment Pack v0.1.0

Six original props for Willow Creek's First Playable Day. The approved mailbox
and cafe table provide the visual reference: warm timber, quiet sage metal,
cream and restrained terracotta, softened edges and broad readable silhouettes.
No purchased meshes, external services, manual modeling or borrowed graphics.

The owner's latest instruction explicitly authorizes independent art production
while Claude lacks credits and supersedes the earlier hold on these props.
Missing import/gameplay decisions are documented assumptions; they do not block
asset authoring. This pack belongs in its own review PR. No game-repository
changes or automatic merge. Ava and draft PR33 remain paused.

## Asset contract

Dimensions are exported Unity XYZ: width / height / depth, in meters. All roots
use scale1 and bottom-center pivots. Blender authoring is +Z up / -Y front;
GLB delivery is +Y up / +Z front. Four opaque PBR materials maximum per asset;
no texture dependencies. Material values are versioned in each linked config.

| Asset-ID / config | XYZ meters | Preflight triangles | Materials | Readable design |
| --- | --- | ---: | ---: | --- |
| [prop_cafe_counter_001](../../configs/prop_cafe_counter_001.json) | 1.60 / 1.02 / .65 | 1,732 | 4 | Rounded timber top, sage customer panels, open rear shelves |
| [prop_cafe_chair_001](../../configs/prop_cafe_chair_001.json) | .46 / .86 / .51 | 1,256 | 4 | Rounded timber seat, bowed back and tapered sage frame |
| [prop_tin_001](../../configs/prop_tin_001.json) | .14 / .19 / .11 | 904 | 4 | Cream tin, terracotta band, sage fixed lid and original leaf seal |
| [prop_cafe_cup_001](../../configs/prop_cafe_cup_001.json) | .158 / .105 / .158 | 1,844 | 3 | Hollow ceramic profile and handle, saucer and static coffee |
| [prop_cafe_tablecloth_001](../../configs/prop_cafe_tablecloth_001.json) | .94 / .172 / .94 | 2,048 | 2 | Cream linen with broad draped corners and terracotta hem |
| [prop_cafe_parasol_001](../../configs/prop_cafe_parasol_001.json) | 1.80 / 2.25 / 1.80 | 1,676 | 4 | Soft octagonal cream/terracotta canopy, timber pole, weighted sage base |

The furniture generators create closed construction components that deliberately
meet/overlap at joints. They are not welded into one boolean solid. No exhaustive
inter-component intersection proof is claimed.

### Candidate collisions

These are proposals only, not exported gameplay colliders or confirmed Unity
prefabs. Centers and sizes use Unity XYZ meters.

| Asset | Candidate |
| --- | --- |
| Counter | Box center(0,.51,0), size(1.60,1.02,.65); full footprint, service aisle at rear |
| Chair | Box center(0,.43,0), size(.46,.86,.51); full footprint; seating system decides any disabling |
| Tin | Optional box center(0,.095,0), size(.14,.19,.11); no small-item physics assumed |
| Cup+saucer | Optional box center(0,.0525,0), size(.158,.105,.158); no drinking or pickup physics assumed |
| Tablecloth | None; visual dressing uses the shared table's eventual gameplay collider |
| Parasol | Base box center(0,.043,0), size(.44,.086,.44); pole +Y capsule center(0,1.12,0), height2.24, radius.028; canopy has no collider by default |

The chair's46cm seat and proposed seat center(0,.46,.035) are art placement aids,
not an animation/seating contract. Walking routes, head clearance, seating
approach and final cafe placement remain game-owned decisions.

## Two states, one approved table

[Pack config](../../configs/cafe-environment-pack.json) defines declarative
composition recipes. Both `assembly_cafe_table_bare_001` and
`assembly_cafe_table_set_001` reference the same `prop_cafe_table_001` v0.1.0.
The approved GLB SHA256 is
`6e122d9a172952fe237e9b24fe9c94b4eff70151e346f3ead95803a86a71ee54`.
The build rejects a changed table export. No second table mesh is authored.

- **Bare:** shared table and two opposing chairs; no dressing.
- **Set:** same table and chair assets, one fitted cloth, two instances of the
  same cup+saucer asset, and a freestanding parasol beside the table. The stand
  provides partial overhang; there is no hole in the approved tabletop.

Cloth is a static shell fitted to this specific .78m table, not simulated cloth
or a universal table-size modifier. Its bottom-center origin must be raised
to.571m: underside.741m and top.743m leave1mm clearance above the.740m tabletop.
Cups sit on the cloth surface with a further small clearance. Do not place the
cloth root directly on the tabletop. All offsets are proposed display assembly
values; generated `arrangements.json` records the actual rendered transforms.
Neither composition implements a runtime state transition or seating behavior.

## What has actually been verified

The first isolated Blender4.5.14 preflight built/exported all six assets.
Actual measured bounds match the configured dimensions; the triangle counts
above come from that run. All six reported zero non-manifold edges, loose
vertices, degenerate faces, duplicate faces and non-finite vertices, with
positive total signed volume. This is geometry evidence, not visual approval.

The first full run produced12 individual front/isometric images, then stopped
on composition-camera framing. Inspection found pointed sage slivers where the
chair's rear stiles crossed the visible timber-back face. A targeted correction
bends the upper stiles rearward before the lower rail begins, preserving outer
dimensions, seat and palette. Run002 was then deliberately stopped for a visible
counter correction: coincident carcass/side surfaces caused black vertical
bands. Side returns now tuck10mm behind and6mm in from the front carcass,
removing both exposed coplanar overlaps while keeping overall dimensions.
Final run003 completed successfully in256.452s. All17 actual images were
rendered, all six assets passed save/reopen and static GLB reimport with exact
positions at five decimals and triangle counts, and independent GLB validation
passed. Each final GLB is byte-identical to the corrected geometry-only
preflight003. Five targeted surface-intersection checks (cloth/table, two
cups/cloth, two chairs/table) report zero intersecting triangles. These checks
do not prove absence of all solid intersections within construction parts.

Both displayed table instances share the same mesh datablock; the shared
table export remains byte-identical to the approved GLB. Default16m camera
framing includes every displayed asset. The existing52-test suite passed.
Root and an independent reviewer inspected the actual final overview, contact
sheet and game views. No further aesthetic iteration is proposed before owner
review. Neither interrupted earlier run is counted as a complete pass.

The bounded build uses these existing/pack scripts:

```powershell
<Blender-4.5.14> --background --factory-startup --offline-mode --disable-autoexec --threads 4 --python-exit-code 1 --python scripts/build_cafe_environment.py -- --output build/cafe-environment/preflight-new --geometry-only
python scripts/run_cafe_environment.py --blender "<Blender-4.5.14>" --output build/cafe-environment/run-new --preflight build/cafe-environment/preflight-new
python scripts/compose_cafe_environment.py --input build/cafe-environment/run-new --output build/cafe-environment/sheets-new --font default
python scripts/package_cafe_environment.py --input build/cafe-environment/run-new --sheets build/cafe-environment/sheets-new --output build/artifacts/cafe-environment-pack-v0.1.0-review-new.zip
```

The deterministic command requires a fresh output directory. Versioned inputs
include six configs, pack config and the immutable approved-table source/config.
The runner records exact source/config SHA256 values, seeds, original-content
provenance, geometry reports, export hashes and preview hashes. Editable
`.blend` sources and GLBs belong in a versioned review artifact, not normal Git
blobs. Generator scripts, manifests, reports and small preview PNGs are reviewed
in the art PR.

The intended full-run evidence is front/isometric previews for every asset,
one joint cafe scene, matched bare/set table views and perspective game-camera
views at6m and normal16m distance (FOV40, pitch50, yaw180,1280x720). These are
Blender Cycles CPU renders with reconstructed game-camera parameters; they are
not Unity screenshots or proof of final scene placement. Quality is judged
from actual images, including native game-distance pixel coverage.

## Limits and remaining integration decisions

- Cup and saucer are one static asset. Default coffee is a fixed surface,
  not fluid; there is no empty/drinking/fill-state implementation.
- Tin has a fixed lid. Inventory, opening, story-clue markings and interactions
  remain unspecified; the graphic seal does not implement game issue56.
- Parasol is one static canopy/post/base assembly, without wind, folding or rig.
  Its1.91m minimum valance height and partial table coverage need route/head-
  clearance review. It is deliberately freestanding to preserve the table.
- Furniture has no doors, cash register, seating animation, attachment API,
  runtime collider or interaction logic. Microdetails invisible at16m are omitted.
- PR34's proposed glTFast6.20.0 / Unity6000.5.8f1 / URP17.5.0 import path remains
  an open contract decision. Its successful two-prop test does not establish
  a completed Unity test for these six new assets. Opaque PBR GLB delivery is
  retained; importer choice, material acceptance, navigation and small-item
  physics remain explicit assumptions until game review.

The cafe pack requires owner quality review before expansion. Walter's House
Pack and Small Town Props Pack are queued after this review; no assets for
those packs have been started. They will each receive a separate thematic PR.

## Review evidence and recommendation

[Contact sheet](../../evidence/cafe-environment/contact-sheet.png) ·
[Joint scene](../../evidence/cafe-environment/cafe_scene.png) ·
[Bare/set comparison](../../evidence/cafe-environment/table-states.png) ·
[Normal16m view](../../evidence/cafe-environment/cafe_game_16m.png) ·
[Actual validation](../../evidence/cafe-environment/validation.json).

At16m, the main furniture silhouette and cloth/parasol state remain readable;
cups/tin and fine trim are small. No extra microdetail is proposed. The parasol
partly obscures the counter in the studio overview; the default game view
separates the main silhouettes. Final placement and canopy occlusion in Unity
remain game-owned decisions. Studio light is not the game's actual URP light.

Recommendation: **GO for owner visual review; HOLD game integration/merge.**
This PR is stacked on PR34's branch solely to reuse the exact approved table
and verified pipeline sources; no merge of either PR is automatic. Large GLB
and editable .blend files are delivered as a separately hashed versioned CI
review artifact. Small previews, source/configs and reports are versioned in
Git. Private host logs and system identifiers remain local.
