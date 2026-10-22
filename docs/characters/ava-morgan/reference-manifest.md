# Ava Morgan — visual reference manifest (v0.1)

## Status
- Owner approved overall identity, character style, initial turnaround, expression range and first wardrobe direction in ChatGPT conversation.
- These approvals are **conceptual**; exact per-view geometry, identity consistency and final 3D remain subject to review.
- Four binary PNG files are **present in this repository** as verified by the GitHub directory listing on 2026-10-22. Their visual consistency has not been independently validated in this update. Agents must open and inspect them before identity-sensitive modeling.

## Character identity
Ava Morgan, age 29, brunette barista and childhood friend in Willow Creek. Softwood 3D: warm, stylized, recognizably adult. Signature loose brunette high bun, brown eyes, freckles, expressive friendly face, natural proportions. Work outfit: cream knit sweater, forest-green apron with brown ties, cuffed dark jeans and white sneakers. Other outfits: casual, gym, evening, outdoor and summer; variants are concepts and should be refined before production.

## Required binary reference assets
The four reference PNGs from **ava_morgan_3d_reference_pack_v0.1.zip** are available at these exact paths:

| Path | Purpose | Status |
| --- | --- | --- |
| `docs/characters/ava-morgan/references/01_identity_master.png` | Face/identity anchor; highest priority for identity match | Present — inspect before use |
| `docs/characters/ava-morgan/references/02_turnaround.png` | Front/three-quarter/side/back body reference | Present — inspect before use |
| `docs/characters/ava-morgan/references/03_expressions.png` | Facial expression references | Present — inspect before use |
| `docs/characters/ava-morgan/references/04_wardrobe.png` | Outfits and material direction | Present — inspect before use |

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
Prepared in the ChatGPT conversation as `ava_morgan_3d_reference_pack_v0.1.zip`. This conversation artifact is not automatically available to GitHub-based agents. All four PNGs have been uploaded to the repository paths above; confirm identity and geometry consistency before proceeding. No external image URLs should be invented.
