# First Playable Day: original environment props

2026-10-24. Scope: two concrete quality proofs first, followed by owner visual
review. The remaining three props are planning only. Ava work remains paused;
policy PR #33 stays draft. No purchased content, manual modeling, downloaded
textures/HDRIs, paid generation, seller contact, game-code change or merge.

## Five IDs and proposed authoring envelope

All sizes below are **proposals**, in meters, exported X width / Y height / Z
depth. Gameplay colliders, interaction ranges, placement and prefab states are
game-owned. The [pinned contract review](FIRST_PLAYABLE_CONTRACT_REVIEW.md)
distinguishes verified requirements from outstanding agreement.

| Asset ID | Role / issue | Proposed X/Y/Z | Art approach and status |
|---|---|---|---|
| `prop_mailbox_001` | Spawn/gate letter interaction, game #51 | 0.36 / 1.43 / 0.62 | **Quality proof built**: authored tunnel shell/door, raised flag, tapered timber post/bracing and restrained stone foot. Four own PBR roles. Static closed model; opening/letter/collider not implemented. |
| `prop_cafe_table_001` | Terrace, game #55 | 0.78 / 0.74 / 0.78 | **Quality proof built**: rounded-square four-plank warm timber top over sage cast-metal pedestal/four feet. Reusable bare table; setup decorations remain separate. |
| `prop_cafe_counter_001` | Outdoor service counter, game #53 | 2.20 / 1.05 / 0.70 | **Not built**: broad warm wood service top, soft edge and quiet painted front. Keep Ava visible above/around it; agree customer/staff sides and traversal envelope before authoring. |
| `prop_cafe_chair_001` | Reused stacked/arranged chairs, game #55 | 0.44 / 0.82 / 0.48; seat 0.45 high | **Not built**: rounded slat back and clear leg silhouette matching table timber/sage. Need game-owned stacking and placement anchors; do not bake a chair stack into the table mesh. |
| `prop_tin_001` | Owner's proposed visual for story tin; physical asset not specified in game #56 | 0.14 / 0.18 / 0.12 | **Not built**: blue rounded coffee tin with one restrained dent; key/string/tag only if required later. Confirm whether it is an actual world prop or narration/detail view. Tiny label text cannot carry gameplay at 16–30 m. |

The approved script v2 describes the blue coffee tin, brass key/string and
`P.H. MILL, STOREROOM` tag. It does not establish an inventory model, opening
animation or a requirement to model these details now. Table setup requires
chairs/cloth/cups/small parasol in the game issue; only the bare table is in
this proof. Those extra components and their IDs need separate agreement.

## Visual and production approach

Use the proposed civic_sage art direction: warm timber and stone, quiet sage
painted metal, sparse terracotta accents. Broad forms, realistic adult scale,
controlled bevels and readable material groups do the work. No noisy textures,
photographic maps or premade meshes. Every production vertex/face/material is
created by versioned Blender Python and a seed/config.

Bottom-center pivot, Blender Z-up/-Y-front, GLB Y-up/+Z-front, meter scale and
stable names are shared with the game contract. Both proof budgets are 2,400
exported triangles and four material slots, proposed for this review rather
than a frozen performance specification. No LOD, collision mesh, runtime state,
interaction marker or seating behavior is claimed.

Render canonical front/isometric views and reconstruct the actual pinned game
camera: perspective, 40-degree vertical FOV, 50-degree pitch, yaw 180, focus
1 m above a ground-level player, distances 6/16/30 m, 1280x720 evidence viewport.
An additional yaw225 view at16m checks normal camera rotation. This is an actual
Blender render with matched camera parameters, not a Unity screenshot, final
game lighting or evidence of cafe-placement/occlusion. Pixel crops retain 100%
scale, so distant detail is not silently enlarged.

## Review and import coordination

Before proceeding to counter/chair/tin, the owner reviews actual silhouettes,
color/material hierarchy and game-distance readability. Technical checks are a
separate gate: actual GLB dimensions/pivot/axes/winding/materials, Blender mesh
health, save/reopen and GLB roundtrip, hashes and reproducible command.

The pinned game revision has no glTF importer despite GLB in the provisional
contract. Request Claude's confirmation on the relevant existing game issues:
stable IDs, dimensions, simple collision envelopes and import/material path.
Do not add a game package or change game code. Do not quietly switch the agreed
deliverable to FBX. A requested format/contract change is a separate coordination
decision. Keep paid assets and Ava exception PR completely outside this work.

Small renders, configs, sources and reports belong in the art review PR. GLB and
editable `.blend` outputs go into a versioned **CI review** artifact,
with SHA256 and 30-day retention; no production release or automatic merge. Human visual acceptance
remains pending even when geometry checks pass.
