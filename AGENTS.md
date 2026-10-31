# Agent operating rules — Life Sim Art
Owner: Codex (exclusive). Art repository for bobo91/life-sim-game (exclusively owned by Claude Code).
## Repository ownership
- Codex exclusively owns Blender, 3D models, characters, animations, materials and the asset pipeline in this repository.
- Claude Code exclusively owns Unity, gameplay, NPCs, dialogue, UI, integration and testing in bobo91/life-sim-game.
- Deliver versioned assets and import contracts to Claude; future Codex changes in the game repository require a new explicit owner instruction.
## Mission
Generate all final 3D meshes and materials from scratch for a cohesive stylized low-poly 3D adult life simulator in a modern American small town.
## Rules
- No purchased packs, prebuilt meshes, or manual modeling. Blender Python procedural geometry and self-generated texture/material workflows are preferred.
- Audit Blender/Python/GPU availability first; do not claim tools or renders ran unless verified.
- Version generator scripts, manifests, tests and small previews; publish large GLB files as versioned artifacts, not normal Git blobs.
- Honor docs/ART_CONTRACT.md; reconcile contract differences with game repo via issues.
- Each asset requires source script, seed/config, deterministic command, geometry checks, GLB export, SHA256 manifest, front and isometric previews, and provenance.
- Quality is judged from actual preview renders; primitive blockouts are not production-quality.
- Never use copyrighted reference meshes or import unlicensed 3D content.
- No auto-merging, destructive actions or paid model/API calls without approval.
## First tasks
ART-001: headless Blender pipeline; ART-002: visual bible/palette; ART-003: house/tree/lamp; ART-004: original adult character and rig feasibility.
## Delivery
Every PR states generated assets, preview locations, commands/tests actually run, quality limitations, Unity compatibility.

## Owner-approved exception — ART-041 Rain v3 visual prototype (2026-10-30)

The owner explicitly authorizes Blender Studio Rain v3 as Ava Morgan's base,
free source acquisition, component licence verification, and controlled
artist-directed editing of independent mesh copies. Preserve the downloaded
original unchanged with hashes, attribution and modification records. Retain
Rain's authored anatomy, especially neck/shoulders/chest/arm transitions; form
Ava's identity and fitted cafe clothes on that base. Python may automate source
preparation, rendering, export and provenance; it must not replace the character
with new primitive/procedural body geometry. The rejected procedural Ava is not
a source and remains NO-GO.

Scope is one static visual prototype in draft PR #42 with real face/body,
matched-pose A03 comparison and game-camera/daylight/shade renders. Existing
source rig may be inspected and used only to extract a static pose; no rigging
or animation production, Unity integration, game-repository changes, A03 changes,
paid services, purchases or merge. Stop for the owner's visual GO/NO-GO.

## Current ART-041 owner instruction — head prototype NO-GO; methods only

The owner approved the Ava B head sheet in PR #42 on 2026-10-31. Its neutral
front/profile/three-quarter are the fixed form reference; the discreet smile
is expression reference only, not the default pose. Preserve the reference
images and identity. No more alternative-face generation. See the immutable
image hashes in docs/characters/ava-morgan/AVA_B_REFERENCE_LOCK.json.

The owner finally rejected Ava B's first 3D head/hair prototype on 2026-10-31:
wrong facial volumes, tired/stiff lids, incorrect nose/mouth/chin profile
transitions, monolithic hair and insufficient B identity. Do not make another
iteration of that head or use it as the starting geometry for a new candidate.
Preserve its files and images as NO-GO history; B design and A03 stay unchanged.
Model production is paused. Current authorization is a short sourced practical
comparison of a professional female basemesh, specialized character software,
and a bounded human-artist sculpt pass with agents doing technical support.
Rank by B fidelity, include cost/licence/agent capability/small future test and
NPC-contract compatibility. Do not run the proposed tests now. No new model,
sculpting, rigging, animation, Unity integration, life-sim-game/A03 changes,
purchases, artist hiring/contact, paid services or merge. Keep PR #42 draft.
The hard triangle cap remains 30,000; v0.2's 31,290 is over contract and not an
approved budget exception. Do not damage the face with premature reduction.
