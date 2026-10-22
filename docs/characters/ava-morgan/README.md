# Ava Morgan — 3D character reference package v0.1

**Project:** Willow Creek / life-sim-art  
**Character:** Ava Morgan, 29, café barista, childhood friend  
**Status:** Approved *creative direction* by owner in chat; NOT an approved exact technical orthographic model sheet or completed 3D asset.

## Priority of references
1. `01_identity_master.png` — face identity and warm Softwood 3D look. Preserve brown eyes, brunette messy bun, soft freckles, adult facial proportions, warm approachable expression.
2. `02_turnaround.png` — preferred café outfit, silhouette, four views. Note: AI-generated multi-view art is NOT geometrically guaranteed; resolve inconsistencies manually.
3. `03_expressions.png` — neutral, happy, laughing, surprised, sad, irritated, thoughtful, flirty. Use for expression targets; do not assume these are production-ready blendshape specifications.
4. `04_wardrobe.png` — outfit concepts: café, casual, sports, evening, outdoors, summer. Visual direction only; garment details may conflict between views.

## Stable character identity
- Female adult, 29; brown eyes; medium/dark brown hair in loosely pinned high bun with face-framing strands; natural freckles across nose/cheeks.
- Stylized adult proportions, readable silhouette at elevated third-person/top-down game camera. No childlike proportions.
- Softwood 3D: warm stylized shapes, subtle textured materials, not photorealistic.
- Café outfit: ivory knit sweater with rolled sleeves, deep olive green apron, dark cuffed jeans, white sneakers, brown leather apron straps, small gold pendant and earrings.
- Work location branding `The Daily Bean` is provisional pending game lore and brand approval; do not bake lettering into geometry.
- Tattoos and additional family backstory shown in generated boards are NOT canon unless separately approved.

## Production deliverables
- Original editable Blender `.blend` source, reproducible generation scripts, and versioned GLB export.
- Separate modular hair, body, clothing and accessories; consistent skeleton/attachment slots; avoid hidden clipping.
- Face expression implementation plan (shape keys or bones), humanoid skeleton and basic idle/walk/talk/gesture clips if supported.
- Neutral studio front/side/back renders plus game-camera tests (elevated top-down, close dialogue) under day/night lighting.
- Manifest: asset id, version, scale/axes, parts, texture maps, animation names, file checksums, tool versions, provenance.
- Geometry/material/performance budgets must be proposed and approved in context of project platform, not invented here.

## Quality gates / stop conditions
1. Review references and list ambiguities (apron ties, side/back construction, hair shape, proportions).
2. Produce a **graybox character blockout** and two camera-distance previews before detailed modeling. Human review required.
3. Produce textured model and expression tests; human review required.
4. Rig/export/Unity import only after approval. Report exact commands/results and blockers.
5. Do not infer exact geometry from inconsistent AI multi-view images. No claim of successful Unity import without test.

## Agent instructions
Read `AGENTS.md`, `docs/ART_DIRECTION.md`, `docs/ART_CONTRACT.md` and `docs/PIPELINE.md` in `life-sim-art`. Coordinate asset contract with `life-sim-game` GAME-002. Follow ART-009 and child issues ART-009A–ART-009F. Avoid third-party meshes or paid API calls without explicit approval. Deliver a small PR per gate, no auto-merge.
