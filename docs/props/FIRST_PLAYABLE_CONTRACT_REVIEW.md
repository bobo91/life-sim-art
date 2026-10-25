# First Playable Day: game contract and camera review

Read-only review, 2026-10-24. No game repository edit, issue comment, asset
import, Unity/Blender run or merge was performed. The game working copy was
changed externally while this review ran: it first pointed to
`game-037-camera-occlusion-impl` at `a466f5e73860fa0cecd6fdd4ebf32ad150fa47cb`,
then to `game-038-letter-on-the-porch` at the current remote main revision.
This report pins game source conclusions to **main
`863906b5de720bca72105bfeeb126a5ba7a0af08`**, read with `git show`, rather than
mixing changing working-copy files.

[Machine-readable snapshot](../../evidence/first-playable-props/game-contract-snapshot.json)
records exact file blob IDs/hashes, issue update times and unconfirmed fields.

## What is actually specified

The canonical [game art contract](https://github.com/bobo91/life-sim-game/blob/863906b5de720bca72105bfeeb126a5ba7a0af08/docs/contracts/ART_CONTRACT.md#L1)
is still titled a **proposal**, and the art repo's mirror is provisional too.
Their shared conventions agree:

* Meters; Unity world **+Y up / +Z forward**. The art direction specifies
  Blender **Z up / -Y front**, converted and validated on export.
* Props use a **bottom-center pivot**, unless an individual request overrides it.
* Deliver **GLB**, manifest and front/isometric previews. Manifest includes
  identity/version/source commit, SHA256, units/axes, bounds, triangles and
  materials. Generator/config/seed/command and provenance remain required.
* Large binaries belong in versioned artifacts, with schema/checksum checked
  before an eventual importer trusts them.

The existing [`PlaceholderAsset`](https://github.com/bobo91/life-sim-game/blob/863906b5de720bca72105bfeeb126a5ba7a0af08/Assets/LifeSim/Runtime/World/PlaceholderAsset.cs#L19)
defines dimension ordering explicitly: **X width, Y height, Z depth**. Neither
the canonical file nor the reviewed issue bodies supplies numerical dimensions,
bounding tolerances or triangle/material caps for these five new props. Do not
relabel proposed art dimensions as game-approved requirements.

| Asset ID | Verified request and role | Limits still unconfirmed |
| --- | --- | --- |
| `prop_mailbox_001` | [#51](https://github.com/bobo91/life-sim-game/issues/51): mailbox near the spawn/gate, collider, letter interaction; within 8 m of spawn, reachable in 3 s, prompt visible from 5 m | Size, collision shape, exact placement, front override, opening/lid mechanism and interaction anchor |
| `prop_cafe_counter_001` | [#53](https://github.com/bobo91/life-sim-game/issues/53): outdoor serving counter at the cafe front; collider; Ava must remain visible/talkable, and it must read as a counter rather than a wall | Width/height/depth, staff/customer sides, standing points, collider and clearances |
| `prop_cafe_table_001` | [#55](https://github.com/bobo91/life-sim-game/issues/55): two terrace tables with persisted setup states; colliders must leave the cafe doorway/counter reachable | Table size, footprint, chair count, seat/stack anchors, state hierarchy and named attachment points |
| `prop_cafe_chair_001` | [#55](https://github.com/bobo91/life-sim-game/issues/55): reusable chairs, stacked on the table before setup and arranged around it afterwards | Size, seat height, stacking clearance, collision and attachment convention |
| `prop_tin_001` | Owner/art candidate ID; **not named** in the reviewed game tickets or pinned code. [#56](https://github.com/bobo91/life-sim-game/issues/56) supplies narration/story flags, not a physical tin interaction or inventory | Every geometry/import requirement, scale, lid, content meshes and whether it is actually shown in the game |

The [approved script v2](https://github.com/bobo91/life-sim-game/issues/51#issuecomment-6385024357),
updated **2026-10-24 13:58:28 UTC**, is the story authority. It specifies a blue
coffee tin dented at one corner, with a brass key on string and a paper tag
reading `P.H. MILL, STOREROOM`. This is appearance/narration evidence, not a
requirement to model all those parts now. It does not prescribe an opening
animation or a legible in-world label at distant camera scale.

For the terrace, both the issue and approved script specify the change:
**bare table with chairs stacked on it → chairs around it, cloth, cups and a
small parasol**. It must be visibly different at camera distances **6, 16 and
30 m**. GAME-042 owns the state switching, collision layout and pixel-difference
measurement; art should preserve separable reusable objects and propose any
attachment conventions explicitly. Those conventions are not already frozen.

No new prop ID appears in pinned main's `Assets` or `docs/contracts`. Its
contract directory contains only `ART_CONTRACT.md`; the versioned per-prop JSON
requests still need to be reconciled with game-side implementation.

## Actual camera: perspective, with a 40-degree FOV

These values are read from code and the serialized Bootstrap scene, not inferred
from a screenshot:

| Setting | Verified value and source |
| --- | --- |
| Projection | **Perspective**; scene `orthographic: 0` |
| Vertical FOV | **40°**, explicitly assigned by [`ProjectBootstrapper`](https://github.com/bobo91/life-sim-game/blob/863906b5de720bca72105bfeeb126a5ba7a0af08/Assets/LifeSim/Editor/ProjectBootstrapper.cs#L104) |
| Pitch | **50°** fixed; [`CameraRig`](https://github.com/bobo91/life-sim-game/blob/863906b5de720bca72105bfeeb126a5ba7a0af08/Assets/LifeSim/Runtime/Camera/CameraRig.cs#L13) |
| Distance | **6–30 m**, default **16 m** |
| Default yaw | **180°**, set by the [generator](https://github.com/bobo91/life-sim-game/blob/863906b5de720bca72105bfeeb126a5ba7a0af08/Assets/LifeSim/Editor/StarterNeighborhoodBuilder.cs#L106), also serialized in the [scene](https://github.com/bobo91/life-sim-game/blob/863906b5de720bca72105bfeeb126a5ba7a0af08/Assets/LifeSim/Scenes/Bootstrap.unity#L722) |
| Focus | Player target position + **1 m up**, with follow smoothing |
| Rotation/position | `Quaternion.Euler(pitch,yaw,0)`; `focus + rotation * (Vector3.back * distance)`; [`CameraMath`](https://github.com/bobo91/life-sim-game/blob/863906b5de720bca72105bfeeb126a5ba7a0af08/Assets/LifeSim/Runtime/Camera/CameraMath.cs#L21) |
| Clip planes | **0.3–1000 m** in the serialized scene |
| Evidence viewport | **1280×720**; [`EvidenceCapture`](https://github.com/bobo91/life-sim-game/blob/863906b5de720bca72105bfeeb126a5ba7a0af08/Assets/LifeSim/Editor/EvidenceCapture.cs#L16) |
| Player settings | **1920×1080** defaults, native-resolution flag on; actual runtime resolution was not tested |

The scene also serializes a focal-length field of 50 and sensor size 36×24.
That is **not evidence that a physical 50 mm camera is the effective projection**.
Use the explicit 40° perspective FOV to build a comparison. Do not replace it
with the art benchmark's orthographic isometric camera and call the result a
game-camera test. Front/isometric views remain the canonical technical pair;
add separately labelled perspective readability views.

At yaw 180°, pitch 50°, distance 16, the formula yields an offset from focus of
approximately `(0,12.257,10.285)` m. This is a calculation from verified code,
not a measured camera capture. The subject position, yaw, distance and viewport
must be recorded for each preview; a prop's centering in a standalone preview
is an approximation of gameplay framing.

**Stale-context warning:** #48 and #53 mention yaw 0 as the default in older
measurements. The pinned generator, scene and evidence camera use **180°**.
The current capture's other views are yaw 215°/distance 30 m and yaw
125°/distance 8 m. A future integration view should use actual scene positions.

Useful context, not new prop-placement requirements: the pinned spawn is
`(-8,0,-6.5)` m; cafe root `(12,0,-11)` m with its door side local +Z. The player
controller is 1.8 m tall with radius 0.35 m. GAME-038/040/042 own the eventual
mailbox/counter/terrace placements and path-clearance tests.

## Import, materials, collisions and budgets

Pinned project settings name **Unity 6000.5.8f1**, **URP 17.5.0** and Linear
color space. Existing generated materials use **Universal Render Pipeline/Lit**
with `_BaseColor` and smoothness 0.1. The canonical GLB contract exists, but no
dedicated GLB importer, glTF package, asset replacement pipeline or new-prop
prefab contract was found in pinned source/direct package dependencies.
This review therefore does **not** establish game-side GLB import compatibility.
An FBX derivative would be additional evidence, not a replacement for the
agreed GLB delivery or proof that integration has run.

The art direction's opaque core-glTF metallic/roughness materials, authored
normals and small shared material palette are suitable proposals for this
stage. The **2,400-triangle / four-material** small-civic-prop targets in
`ART_DIRECTION.md` remain provisional authoring targets, not mailbox/table
acceptance limits or demonstrated runtime performance. No new-prop texture/LOD
budget is approved in the reviewed game sources.

The new issues require colliders for mailbox/counter/table arrangements but do
not give their primitive types or dimensions. Existing buildings use a root
BoxCollider, trees/lamps use simpler proxies and child visual primitives often
have colliders removed. These are implementation examples, not authority to
export a whole visual mesh as the collider. Unity components, interaction ranges,
prefabs, NavMesh/path clearance and saved table states stay game-owned.

[#48](https://github.com/bobo91/life-sim-game/issues/48) proposes `building_*`
occlusion registration and `prop_*` ignore by default, with URP-compatible
materials or a declared shader family. That proposal is not in pinned main;
its PR #50 is explicitly outside the First Playable Day milestone. Do not add
building-fade requirements, transparent materials or occlusion scripts to these
props merely because the camera ticket discusses them.

## Milestone and handoff boundary

Issue metadata confirms #51–58 belong to milestone **1, First Playable Day**, in
GAME-038–045 order. #51 letter/mailbox, #52 menus/save, #53 counter/meeting, #54
choices, #55 terrace, #56 payoff, #57 end-to-end evidence, #58 rest/night.
The dedicated milestone detail endpoint was unavailable through the connector,
and a read-only CLI fallback returned 404; due date and full milestone progress
metadata are therefore unverified. The issue membership and script approval are
verified separately.

Before a final replacement contract is frozen, game/art owners should reconcile
per-prop dimensions, collision envelopes, handedness/import path, shader mapping,
footprints and table/chair attachment/state conventions. New meshes can be
reviewed meanwhile as **art proposals** with their own explicit dimensions and
tests. This report neither edits the game nor accepts any unrendered asset.
