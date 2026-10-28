# Agent operating rules â€” Life Sim Art
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

## Approved limited Phase A exception (2026-10-28)

Owner reply: "kÃ¶r pÃ¥" to the named Snow v4 experiment described in
docs/characters/male-player/POLICY_EXCEPTION_PROPOSAL.md. This authorizes only
MALE-NEUTRAL-A01; all unrelated rules remain. Evidence: evidence/male-neutral-a01/authorization.json.

Owner-approved exception â€” MALE-NEUTRAL-A01, Phase A only

Allow one static male-player quality experiment using Blender Studio Snow v4
under its documented CC BY 4.0 asset terms. Allow free source acquisition,
AI-assisted inspection of legally permitted mesh/render data, and bounded
artist-directed mesh editing on independent copies. Inspect embedded component
and script licences before enabling scripts or publishing derivatives.
No additional third-party source or paid service is authorized.

Preserve the original unchanged with its source URL, version, licence and SHA256.
The artist-authored .blend and recorded changes are the canonical editable
source; Python/config must reproduce render, export and validation, not invent
the same artistic forms from primitives. Retain all required attribution,
licence links and modification notices in source, artifacts and game delivery.
Do not use unlicensed components or claim this derivative is entirely original.

Scope: one young-adult male neutral, one coherent hairstyle and one simple
modern outfit, with a distinct Willow Creek identity and no fixed player name.
The source may contain an existing rig, but Phase A only inspects it and extracts
a static presentation/export; no rig rebuilding, animation, NPC library or
game-repository changes. No new generic parameter bank.

Limit: six active work hours, one artistic form/look pass and one targeted
correction. Stop at the source gate if permissions, topology or extensive
reconstruction prevent a credible bounded trial. Stop on inadequate visual
quality or when the cap is reached; do not switch to another base automatically.

Deliver real front/side/back/three-quarter renders, face close-up, near and
16-metre proxy camera views, geometry/contact results, reopen and GLB roundtrip,
measured dimensions/budget, limitations and provenance. Visual approval is
required before Phase B, rig/animation work or further character production.

This exception applies only to the named source and scope. No purchases,
commissions, subscriptions, paid model/API calls, vendor contact or automatic
merge. All other repository rules remain in effect.

## Owner-authorized Phase A visual revision A02 (2026-10-28)

The owner visually rejected A01 while approving its technical method and explicitly
requested a distinct second male visual iteration on the same PR #39. This extends
the completed A01-only pass limit solely for A02: retain the source, A01 and its
evidence unchanged, reuse the same approved CC BY Snow source and working export
pipeline, and perform artist-directed facial geometry/material changes with
traceable multi-view comparison. Evaluate future deformation compatibility and
triangle reduction without building a rig, animation or clothing system.
No additional base acquisition, purchase, vendor contact, paid service, game-repo
change, merge or Phase B is authorized. Stop after A02 review delivery.

## Owner-authorized Phase A refinement A03 (2026-10-28)

The owner approved A02 as the visual foundation, explicitly rejected Phase B/
production for now, and requested A03 on the same draft PR39. Permit only subtle
eye/jaw/chin/hair/brow refinement of the existing A02 copy, controlled static
optimization toward25-28k without sacrificing appearance, and actual matched
Blender/isolated URP verification. Preserve A01, A02 and original Snow unchanged.
Keep a high-quality editable A03 source before optimization. Rig reuse remains
unproven unless actually tested; do not build any rig/animation/clothing system.
No new base, purchase, vendor contact, game edit, merge or Phase B. Stop after
A03 visual review delivery. This extends only the completed A02 pass limit.

## Owner-authorized Phase B A03 motion feasibility (2026-10-28)

The owner explicitly approved A03 visual identity and its 29,367-triangle budget,
retaining A01/A02 as history with no A04 or merge. Permit a bounded Phase B on
the same approved Snow/A03 source copies: inspect source rig/weights, test skinning
and basic idle/walk/run/turn motion, export/reimport and isolated Unity URP proof.
Preserve approved face, palette and overall style. No life-sim-game changes, new
generic animation/clothing/character system, purchases, paid services or merge.
If the source rig proves unsuitable, document it and propose a limited alternative
before extensive rebuilding. Existing source licences/credit and script-isolation
requirements remain. Stop at a documented playable-character GO/NO-GO review gate.
