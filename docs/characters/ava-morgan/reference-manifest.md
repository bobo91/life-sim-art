# Ava Morgan — visual reference manifest (v0.1)

## Status
- Owner approved overall identity, character style, initial turnaround, expression range and first wardrobe direction in ChatGPT conversation.
- These approvals are **conceptual**; exact per-view geometry, identity consistency and final 3D remain subject to review.
- Binary PNG source images are **NOT YET UPLOADED TO THIS REPOSITORY**. Do not claim to have inspected them or start identity-sensitive 3D production until they are available.

## Character identity
Ava Morgan, age 29, brunette barista and childhood friend in Willow Creek. Softwood 3D: warm, stylized, recognizably adult. Signature loose brunette high bun, brown eyes, freckles, expressive friendly face, natural proportions. Work outfit: cream knit sweater, forest-green apron with brown ties, cuffed dark jeans and white sneakers. Other outfits: casual, gym, evening, outdoor and summer; variants are concepts and should be refined before production.

## Required binary reference assets
Upload the four original PNGs from **ava_morgan_3d_reference_pack_v0.1.zip** to these exact paths:

| Path | Purpose | Status |
| --- | --- | --- |
| `docs/characters/ava-morgan/references/01_identity_master.png` | Face/identity anchor; highest priority for identity match | Upload pending |
| `docs/characters/ava-morgan/references/02_turnaround.png` | Front/three-quarter/side/back body reference | Upload pending |
| `docs/characters/ava-morgan/references/03_expressions.png` | Facial expression references | Upload pending |
| `docs/characters/ava-morgan/references/04_wardrobe.png` | Outfits and material direction | Upload pending |

Keep filenames stable, track changes with versioned manifest and never overwrite an approved identity anchor without owner approval. Use the reference PNGs as guidance, not exact orthographic measurement; AI image turnaround may contain view-to-view inconsistencies.

## Agent workflow
1. Confirm **all four files exist** and can be opened; record dimensions and hashes in PR.
2. Inspect existing art contracts and pipeline before creating new scripts.
3. Prioritize facial identity anchor over contradictory secondary views. Document any conflicts for owner review.
4. Create editable Blender blockout with separated body, hair, clothing and accessories.
5. Render face close-up, front, side and elevated gameplay camera; compare against source and list mismatches.
6. **STOP for owner visual review** before detailed modeling, rigging or final Unity delivery.

## Tickets
- Parent #11 ART-009
- #24 dossier; #25 face alternatives; #26 turnaround; #27 expressions and outfits
- #30 3D blockout; #28 detailed modeling; #29 rig/export

## Source package
Prepared in the ChatGPT conversation as `ava_morgan_3d_reference_pack_v0.1.zip`. This conversation artifact is not automatically available to GitHub-based agents. The user must upload its PNG contents to the repository paths above, or use a supported binary-upload mechanism. No external image URLs should be invented.
