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

## Current ART-041 owner instruction — 2D design GO, 3D production paused

Rain Ava v0.2 is visually rejected (NO-GO). Keep Rain's approved base/anatomy,
but do not change meshes or produce models, rigs, animations or integration.
The owner now authorizes a structured AI-first design phase: exactly two final
face/hair concept directions A/B, actual raster design images using built-in
image generation, shown beside unchanged approved A03 as a style reference.
No external character artist is to be hired. No full turnaround sheet yet.
Stop for the owner's choice; this does not authorize mesh/rig/animation work.
The hard triangle cap remains 30,000; v0.2's 31,290 is over contract and not an
approved budget exception. No merge or life-sim-game changes.
