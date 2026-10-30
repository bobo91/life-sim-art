# ART-041: Ava Morgan Phase A preflight

Audit date: 2026-10-30. This is a new static visual candidate, tracked in
[issue #41](https://github.com/bobo91/life-sim-art/issues/41) on branch
`art/041-ava-morgan-phase-a`, based on art main
`facdbc400973193c10eb5ab012ee6445555daa6d`.

## Scope and existing work

The issue/PR audit found no earlier ART-041 task before this issue was created.
The still-open historical Ava work is recorded separately:

- [#11 / ART-009](https://github.com/bobo91/life-sim-art/issues/11): character-production coordination.
- [#28 / ART-009E](https://github.com/bobo91/life-sim-art/issues/28): model/material stage.
- [#30 / ART-009E1](https://github.com/bobo91/life-sim-art/issues/30): earlier blockout and reference direction.
- [draft PR #33](https://github.com/bobo91/life-sim-art/pull/33): conditional purchased-head policy proposal; rights/purchase gates remain closed. It supplies no production mesh or permission for this task.
- [PR #39](https://github.com/bobo91/life-sim-art/pull/39): A03 and subsequent motion work; preserved independently.

ART-041 uses original procedural Ava geometry and materials. It may reuse
working A03 render/export/validation techniques; A03 meshes are only an unchanged
comparison reference. Snow-derived A03 permissions do not authorize a female
derivative. No MPFB generation, historical rejected Ava geometry, purchased base,
new third-party mesh, paid service or AI concept image substitutes for model evidence.

The reviewed rules are [AGENTS.md](../../../AGENTS.md),
[ART_CONTRACT.md](../../ART_CONTRACT.md),
[ART_DIRECTION.md](../../ART_DIRECTION.md), [PIPELINE.md](../../PIPELINE.md),
the [existing Ava reference dossier](README.md), the A03 static import contract
and provenance at the pinned revision below, and the game's
[shared contract](https://github.com/bobo91/life-sim-game/blob/fd565fe1598f8eb9925519c370cc4b7c354f8afc/docs/contracts/ART_CONTRACT.md).
Delivery remains meters, Blender Z-up/-Y-front converted to glTF Y-up/+Z-front,
foot-centered origin, versioned binary artifacts, reproducible source/config,
geometry checks, SHA256 records and actual preview renders. No contract change
or game-repository write is part of this task.

## Existing identity and conflicts

The game checkout was clean at `fd565fe1598f8eb9925519c370cc4b7c354f8afc`.
GitHub main NPC data and story were also read through the connector and matched
the inspected content. The game [NPC data](https://github.com/bobo91/life-sim-game/blob/fd565fe1598f8eb9925519c370cc4b7c354f8afc/Assets/LifeSim/Data/willow_creek_npcs.json#L61-L65)
records `npc:ava`, Ava, home and cafe-counter workplace. It specifies no age,
surname, hair, eyes, skin, clothing or proportions. The game still draws an
orange placeholder capsule (`Assets/LifeSim/Editor/NpcBuilder.cs:17-23,61-82`),
which is not an appearance reference.

The [locked first-day script](https://github.com/bobo91/life-sim-game/blob/fd565fe1598f8eb9925519c370cc4b7c354f8afc/docs/story/first-day-script.md#L5-L13)
establishes Juniper Cafe and a warm, slightly dry, friendly Ava; the scene is
explicitly not romantic. Existing art direction in the dossier and issue #30
specifies an adult woman of 29, brown eyes, brunette loose high bun with framing
strands, freckles, ivory rolled-sleeve sweater, deep olive apron with brown
straps, dark cuffed jeans, white sneakers and small gold jewelry. These are
existing art-side reference choices, not newly established game canon or an
approved ART-041 model.

Two stale reference differences were reported before modeling: the dossier's
provisional **The Daily Bean** branding conflicts with approved **Juniper Cafe**;
its **childhood friend** description is unsupported by the locked first meeting
(`first-day-script.md:54-57`, including Ava's introduction and “someone new at my
counter”). No logo, new relationship, tattoo or family-history detail is added.
The reference boards are creative direction, not geometrically exact turnarounds.

## Actual camera and Juniper lighting evidence

The serialized `Assets/LifeSim/Scenes/Neighborhood.unity:6496-6501,6539` records
the normal perspective camera: yaw 180 degrees, elevation 50 degrees, distance
16 m, focus 1 m above the player and vertical FOV 40 degrees. These agree with
`Runtime/Camera/CameraRig.cs:13-17` and `Editor/NeighborhoodBuilder.cs:102`.
Zoom ranges from 6 to 30 m. A Blender view using these parameters is a camera
proxy for this candidate, not a Unity integration test.

The cafe counter is outdoors: `Editor/NeighborhoodNpcBuilder.cs:81,103-105`
places it at Unity X/Z (-11.5, 7.2), facing 180 degrees, `kind="outdoor"`.
There is no established separate cafe-interior lighting rig. Shared neighborhood
daylight in [NeighborhoodBuilder.cs:48-52](https://github.com/bobo91/life-sim-game/blob/fd565fe1598f8eb9925519c370cc4b7c354f8afc/Assets/LifeSim/Editor/NeighborhoodBuilder.cs#L48-L52)
uses a directional sun, RGB (1, 0.94, 0.82), intensity 1.2, soft shadows and Unity
Euler (50, 150, 0), with flat ambient RGB (0.52, 0.57, 0.61). Blender evidence
should reproduce this warm directional/cool ambient relationship and record its
own settings. Renderer exposure, intensity units and color management prevent a
claim of pixel-identical Unity lighting.

## Immutable A03 comparison and current game pin

The static appearance comparison is
[male-neutral-a03-v0.3](https://github.com/bobo91/life-sim-art/releases/tag/male-neutral-a03-v0.3),
source revision `3ae0723b1c450d41ab42f83875164af495949fee`:

| Item | Static comparison pin |
|---|---|
| Archive | `male-neutral-a03-v0.3-review.zip` |
| Archive SHA256 | `3ae53894ae1aef5c909a82d1c3d60b3f153005ca8dee0b11cfb646b2b09da6fc` |
| GLB SHA256 | `bed475ead3c8ab6ad21463085ed52ffa09467ccd64654f7850999655105c55a1` |
| Cost/scale | 29,367 triangles; 10 meshes; 9 materials; 13 images, maximum edge 2048; height 1.7494054 m |

Sources: pinned `docs/characters/male-player/A03_IMPORT_CONTRACT.json` and
`evidence/male-neutral-a03/{artifact,manifest,provenance}.json`. This is a static
T-pose asset with no delivered rig or animations. It remains unchanged.

The game's [current catalog](https://github.com/bobo91/life-sim-game/blob/fd565fe1598f8eb9925519c370cc4b7c354f8afc/ArtSources/Characters/catalog.json)
instead pins the subsequent **male-locomotion-fit-v0.1** delivery: archive SHA256
`9c7c1f556f17b3bb84ea708ffccaac9b479191ab468b98199f787498f6174885`, GLB SHA256
`532ce438b24f69e14c099d956706d69e6e6b8531e0c162e92f72756bb60046b0`, contract
revision `4ff25307e9797b20d57e8ca7dcca2fe4529032c2`. Its 58-joint motion asset
shares the approved 29,367-triangle appearance; it is not the static comparison
file and is not modified by ART-041.

A03 is a modified [Blender Studio Snow v4](https://studio.blender.org/characters/snow/v4/)
asset under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Any Ava+A03 comparison must credit **Snow Rig (CC) Blender Foundation |
studio.blender.org**, identify A03 as the modified comparison asset, and retain
its source/license links. This attribution applies to A03, not to the original
procedural Ava. No Snow source script is executed for Ava.

## Evidence and stop

The game-side draft [NPC_CHARACTER_CONTRACT.md](https://github.com/bobo91/life-sim-game/blob/32aae2ef7ad2905e88889e6ed71e7bf9be5b68e1/docs/contracts/NPC_CHARACTER_CONTRACT.md)
was also read. GAME-049/#75 proposes 1.60–1.75 m height, <=30,000 triangles,
<=12 skinned meshes, <=10 materials and <=8 images/2048px, plus later rig/clips,
8/16 m terrace/shade evidence, fixed GUID and pinned release. This task's static
appearance gate precedes its animated cafe milestone; it does not fulfill or
authorize those later requirements. Ava's measured static budget fits the
proposed limits. The proposed production ID `chr_npc_ava_morgan_001` differs
from this explicit review ID `chr_ava_morgan_041`; reconcile the production
identity and vertex-colour material transport before any integration release.
These deltas are recorded on art issue #41 and in the draft PR, without editing
the game contract or treating its draft as owner approval for rigging.

Runtime availability, actual Blender commands, geometry/export validation and
image findings belong in the execution evidence; this document claims no new
render, rig or import test by itself. The required candidate review contains
front/side/back full body, face close-up, same-scale Ava+A03, normal game-camera,
and Juniper-like material/hair/clothing views, plus a critical quality report.
Automated checks cannot grant visual approval.

Stop after delivering the visual candidate in a draft PR. Rigging and animation
production require the owner's later explicit appearance approval. No merge,
life-sim-game change, or change to any approved A03 source or pinned release.
