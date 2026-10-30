# Rain source and attribution — ART-041

The owner approved Rain v3 and controlled edits of its actual meshes on 2026-10-30. This is the explicit exception recorded in AGENTS.md. The rejected procedural Ava is not used.

## Actual downloaded payload

- Official [Rain v3 page](https://studio.blender.org/characters/rain/v3/), free download, retrieved 2026-10-30 08:38 UTC. The actual page associates its download with **CC BY 4.0** and the requested credit below.
- [Exact official download](https://studio.blender.org/download-source/files/ee/a7/eea73e55dba1cea31c09848df6a794b2-4.zip). UI download name: `rain-v33.zip`. It contains **`Rain v3.3/rain_v3.2.blend`**, not a file called v3.0. We retain that version/name discrepancy in provenance.
- ZIP: 67,579,177 bytes; SHA256 `80217f163f6392dc829233d63c2cfb5e1376775bc34101ad14f39631fea70d24`.
- Actual native file: 9,167,189 bytes; SHA256 `831ab6d837c679040285862b15dc9ee5180b018442a88aeaf92aaa7509b80258`.
- 23 payload files: the native file and 22 PNGs. Per-file hashes are in `evidence/ava-rain/source-provenance.json`. The original ZIP, extracted payload and downloaded page are retained locally under `build/ava-rain-v01/source/`, separately from every edited copy. Hashes were checked before and after Blender work. No original save, source-script execution or original-rig modification occurred.

## Licence evidence inside that file

Blender was opened with `--disable-autoexec`, `--offline-mode` and `use_scripts=False`. The **actual native file's embedded `ReadMe.txt`** explicitly identifies the character rig as CC-BY and links `https://creativecommons.org/licenses/by/4.0/`. Exact extracted text is retained as `evidence/ava-rain/Rain-ReadMe.txt`; SHA256 `2009ec5ebe690c97b3d7b6240f2682202714ada7f96385da5452137f4bb70d88` (581 UTF-8 bytes). Thus this is evidence from the downloaded character, not an inference from a general website footer.

The embedded software has a separate status: `cloudrig.py` declares `SPDX-License-Identifier: GPL-3.0-or-later`; `rain_shading.py` has no explicit licence header. **Neither is executed or included in the static derivative or review bundle.** All native rig/actions/drivers/embedded Text blocks are excluded from the delivered static model. Materials are rebuilt with core Principled BSDF nodes. Unmodified original software remains only in the separately preserved source ZIP/native file. No claim that CC BY relicenses software is made.

## Credit to carry with derivative assets and images

> Rain Rig (CC) Blender Foundation | studio.blender.org

Source: [Blender Studio Rain v3](https://studio.blender.org/characters/rain/v3/). Licence: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) ([legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en)). Credit is embedded in `.blend` and GLB metadata; source/licence links and this modification notice accompany both files in the bundle and PR. CC BY permits commercial redistribution and adaptation subject to its attribution terms; Blender Foundation does not endorse this derivative.

**Changes by the life-sim-art project:** static rest-pose extraction; authored neck/shoulder/chest surfaces retained; bounded edits of Rain's head/eyes/brows/ears/nose/cheeks/jaw/chin/lips; longer outer arms; Rain ponytail recontoured to a bun and original strand adapted/mirrored; original torso surface duplicated, trimmed and eased into a cream rolled-sleeve top; fitted olive apron/ties/straps; original jeans/sneakers; remapped/downsampled original skin, eye and denim textures, brown iris tint and seeded subtle freckles; plain PBR; static mesh reduction, metre scale and export. No previous Ava body, MPFB, AI concept image or additional third-party mesh contributes to the model. The modified Rain character data is distributed under CC BY 4.0 with this notice.

A03 comparison only: unchanged approved static v0.3, SHA256 `dcd7681255f49fa704844492b0ffc6964e434ccb4ae59aaba7788b0af56ffd90`. Its base is [Snow v4](https://studio.blender.org/characters/snow/v4/), **Snow Rig (CC) Blender Foundation | studio.blender.org**, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). A03 is not included in Ava's exported asset or modified by this work.

## v0.2 final static visual refinement

Owner-requested follow-up uses the preserved v0.1 authoring copy. Native Rain lip-neutral/widening deltas and eyelid/brow selections guide static face edits; no rig or animation is produced. Jaw/cheek/nasal planes are refined while the neck junction, body and eye globes remain unsculpted. The actual source ponytail forms a tucked wrap with a local contact weld; original framing-lock attachments are retained. Existing garment surfaces receive restrained folds/drape, cloth UVs and two project-generated 256² knit/canvas normal images. The old procedural Ava is still excluded. Root translation alone recentres changed hair bounds; it does not alter anatomy or scale. Same Rain attribution/CC BY terms apply, with this modification notice. No additional third-party sources or code were acquired.
