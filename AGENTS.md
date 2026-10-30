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

## Conditional exception — AVA-NEUTRAL-FEAS-01
The owner has approved the bounded experiment plan, not a purchase or execution
before the gates below. This exception covers only Valentin Fischer / wysp's
**Stylized Female Basemesh**, ArtStation product **dB9BJ**:
https://valentinfischer.artstation.com/store/dB9BJ/stylized-female-basemesh.
It is not permission for substitute assets or a character library.

### Mandatory gates before acquisition or model work
- Obtain and retain the seller's written clearance for the exact asset and
  selected license: commercial game use, modification, future derived NPC and
  the intended cloud-Codex workflow. Permission must expressly cover licensed
  mesh/geometry data and source-derived screenshots/renders as AI inputs for
  inspection, Blender-assisted editing and render evaluation. Identify and
  resolve any NoAI restriction consistently with applicable marketplace terms;
  general commercial-use or local-Python permission alone is insufficient.
- Report the rights evidence, exact license, restrictions and total checkout
  cost including applicable tax/fees to the owner. Then obtain the owner's
  separate purchase/start go-ahead. These may be approved in one concrete
  decision. Candidate selection, this policy or its PR/merge is insufficient.
- Until both gates pass, do not download/acquire the purchased mesh, process
  it, or provide licensed model data or source-derived private inputs to Codex.
  Public product/license research is allowed. No training permission is implied.

### Scope, time and quality
- After both gates pass, allow the named licensed source and bounded direct
  mesh editing/sculpting on independent copies. Only one head with a short
  neck, separate eyes/brows, simple skin/eye materials and one temporary
  coherent messy-bun hairstyle are in scope. A supplied body stays unchanged
  in private source storage; do not develop or export it in this experiment.
- Within that scope only, this overrides the from-scratch mission, the
  purchased/prebuilt/manual-modeling ban and the blanket copyrighted-reference
  mesh ban. Unlicensed content remains prohibited.
- Maximum **six aggregate active Codex/Blender work hours**, **one main form
  pass and at most one targeted correction**. Log active work across all
  contributors and subprocess/wait time separately; parallel agents do not
  receive separate six-hour allowances. Source preparation counts in the cap.
  Do not build a parameter bank or extend the test with random adjustments.
- Stop early if extensive face reconstruction, retopology or repairs are
  needed. The primary criterion is Willow Creek's approved visual quality and
  recognizable Ava identity; mesh modification or export success alone is not
  success. The owner decides visual acceptance against approved references,
  accounting for unknown reference cameras, pose and lighting.
- No new body, wardrobe, rig, animation pipeline, NPC production, Unity/game
  integration or game-repository changes. No external artist, additional asset
  purchase, subscription, GPU rental or new paid generation/API expenditure.
  This exception authorizes none of those costs. No automatic merge.

### Source and evidence
- Preserve the acquired original unchanged; record author, product/version,
  license/permission, receipt and SHA256. Keep raw purchased/derived assets
  private; publish assets or previews only where the applicable rights permit.
- For this authored stage, the editable versioned `.blend`, named neutral
  form delta/shape key, provenance and edit record are canonical. A script need
  not reconstruct artistic edits from primitives. Retain reproducible
  render/export/check scripts and configs; retain seeds for procedural parts.
- Deliver actual unretouched front, profile and three-quarter views in both
  neutral clay and simple color/look, plus normal game-distance evidence and
  source/reference comparisons. Record cameras, lighting and image layout.
  AI-generated portraits cannot substitute for renders of the actual mesh.
- Verify/report geometry and actual defects, eye seating and eyelid/lip
  contacts, save/reopen and static GLB export/reimport. Distinguish intentional
  boundaries from defects and state check limitations. Retain commands actually
  run, hashes, edit/time records and visual GO/NO-GO; do not claim rig validation.
- Stop after the bounded report for owner visual approval. Broader work or
  delivery-contract changes require a later decision; no automatic continuation.
