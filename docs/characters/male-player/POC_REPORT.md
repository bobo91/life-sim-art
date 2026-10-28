# MALE-NEUTRAL-A01: Phase A result

2026-10-28. **GO for owner visual review of this Snow-derived static candidate; NO-GO for shipping or Phase B without separate visual approval.** No further artistic iteration is proposed inside this experiment. The base clearly improves on our primitive/morph face experiments, but it has not demonstrated an original, reusable 20-50 NPC pipeline.

## Actual images

[Four body views](../../../evidence/male-neutral-a01/previews/four-views.png) | [Face and near perspective](../../../evidence/male-neutral-a01/previews/face-and-near.png) | [Native 16 m front](../../../evidence/male-neutral-a01/previews/game_16m_front.png) | [Native 16 m back](../../../evidence/male-neutral-a01/previews/game_16m_back.png) | [Actual isolated Unity URP](../../../evidence/male-neutral-a01/previews/unity-three-quarter.png) | [Source face comparison](../../../evidence/male-neutral-a01/previews/source-comparison.png).

All nine native Blender images are in the previews directory. They show the same final asset; per-view geometry hashes were asserted during rendering. Composite sheets only resize/layout these images and add labels. There is no image generation, retouching or view-specific mesh.

## Recommendation and alternatives

| Method | Evidence and costs | Recommendation |
| --- | --- | --- |
| Original procedural geometry | Python reliably produces data and exports; rejected MPFB/Studio-head Ava trials did not establish face/hair quality. No new from-scratch mannequin was built here. Blender is free; artistic labor is not eliminated. | Do not repeat parameter searches as the primary character method. |
| Artist-authored open base, then bounded edits and automation | Snow v4 is free CC BY 4.0. Its actual authored body, clothes, face and hair were inspected and rendered locally. Static Blender-to-GLB-to-Unity now works with the repairs below. External spend: **0 SEK**. | **Best tested direction.** Approve or reject the visual result before investing in rig/variation. |
| Paid modular pack | BoZo Base Pack advertised **USD 40 before tax**; Synty Modern Civilians advertised **USD 199.99** on 2026-10-28. These are vendor prices, not purchases or tested meshes. Source sharing and AI-assisted inspection rights remain problematic/unconfirmed. | No purchase or vendor contact. A pack is only useful if its style and license both fit; it does not prove closer face quality. |

The [historical study](PHASE_A_REVIEW.md) records primary-source comparisons and earlier failed work. Its pre-approval access/policy statements are superseded by this report and the [source/license evidence](PROVENANCE.md). No other model base was imported.

**What automation actually achieved:** source/hash audit, static extraction from existing authored deformation, one configured hairstyle edit, existing facial control sampling, texture packing/tint bakes, PBR conversion, cameras, GLB export, reopen checks, point-cloud roundtrip, reproduction and isolated Unity checks. The attractive underlying anatomy, hands, feet, clothes and hair were authored by Blender Studio. Python did not invent that quality.

**What still requires artistic work:** a distinctive facial identity, expression design, alternative hair silhouettes, body/age families, clothing fit, skin weights and deformation assessment. A single adult male source does not prove female/child anatomy or interchangeable clothing. No time-per-new-NPC or automation percentage has been measured.

## Visual assessment

- Face: coherent jaw, nose, lips and cheeks from multiple views. Slightly lowered authored upper lids and lifted mouth corners soften the original stare. The result is reserved and a little sleepy, rather than strongly warm/expressive. Source Snow facial identity remains prominent; this is not a newly designed identity or proof of Ava fitting.
- Eyes: no obvious black sockets, detached globes or cut-through lids in the reviewed front, three-quarter and profile images. Static diagnostic distances are not a signed-clearance certificate: the two 24-vertex socket boundary groups sit about **1.3-8.3 mm** from the nearest eye surface. Head/eye triangle intersections are expected at the socket and need deformation review before animation.
- Hair: an actual 3D cap and six retained authored crown/front components, visible from back and side. Six rear bun components were removed; the crown is compressed/swept and made matte dark brown. The top still reads as chunky braided/locked ridges; the rear is plain and the temple edge abrupt. This is not a finished modular hair pipeline.
- Neck/shoulders/hands/feet: coherent source anatomy and clothing in the static T-pose, with separate fingers and modeled shoes. The neck is long and stylized. Open clothing edges are intentional. No animation, finger articulation, skinning or pose-dependent intersections were tested.
- Palette: sage shirt, slate-blue trousers, brown hair and muted sneakers work with the existing warm art direction. Fine skin/clothing texture detail is substantially lost at gameplay distance.
- 16 m proxy: genuine **16 m**, **50-degree elevation**, **40-degree vertical FOV**, **1280x720**. The character is roughly 80 px tall; silhouette and clothing blocks survive, expression and iris details do not. This is the art camera proxy, not a verified current game camera. The image was not zoomed to make readability look better.

The source comparison is **not a matched shape-only experiment**. Source: original materials/rig visibility/render subdivision, 24 samples, face framing 0.29 source-height, target 0.89 height. Candidate: static subdivision 0, core PBR, 32 samples, 0.31-height framing, target 0.88 height, light power multiplier 0.55. Both use AgX at exposure 0, but light and framing differences contribute to the appearance change.

Unity uses an orthographic camera and one directional key; Blender uses area lights, AgX and a different near-camera projection/elevation. The Unity image is visibly harder/shinier. glTFast also ignores optional `KHR_materials_specular` on hair/shirt. Therefore this proves an actual URP import/render, **not a Blender/Unity look match or game-lighting approval**.

## Measured technical result

| Check | Actual result |
| --- | --- |
| Source | Official Snow v4 ZIP; contained `snow_v4.2.blend`, file metadata Blender 4.4.32, ReadMe minimum 4.1 |
| Tested Blender | 4.5.14 LTS / bundled Python 3.11.15; CPU Cycles, 32 samples, denoising, 6 threads; no GPU render claimed |
| Blender dimensions X/Y/Z | **1.738315 / 0.306273 / 1.750000 m**, width includes T-pose arms |
| Unity dimensions X/Y/Z | **1.738315 / 1.750000 / 0.306273 m**, unit scale, bottom-center pivot |
| Geometry | **42,077 triangles, 10 mesh objects, 9 materials**, 13 embedded GLB images up to 2048 px |
| Save/reopen + GLB | **243 checks passed, 0 failed**, finite positions/normals, valid indices, no zero-area faces, no >2-face edge junctions; same surfaces/point positions/bounds after roundtrip |
| Open geometry | Intentional source/clothing/socket boundaries remain; this is not a watertight single solid. No all-contact or self-intersection guarantee |
| Reproduction | All geometry hashes and GLB bytes identical; front pixels identical. PNG file bytes differ due metadata. Only the front render was repeated for reproduction |
| Unity | **6000.5.8f1 / URP 17.5.0 / glTFast 6.20.0**, D3D11 import/render and scene reopen passed; expected material factors and texture bindings present |
| Known Unity warning | Optional specular extension unsupported; retained in report. No actual game repository, scene, controller or Humanoid test |
| Source preservation | Original ZIP and blend SHA256 unchanged after all work; no embedded source scripts executed or delivered |

The historical **16k triangle target is exceeded**, and 9 materials/10 meshes plus multiple 2k atlases are not a validated population budget. No LOD, draw-call, texture-memory, skinning or 20-50-NPC performance test was performed. This is a hero-quality static evaluation, not a scalable NPC library.

## Real problems found and repaired

1. Source edit-active `tattoo_light_map` was not render-active `UVMap`. Strict atlas mapping caught the wrong selection; the render UV is now retained without an arbitrary fallback.
2. Source masked body carried 111 unused vertices and 110 wire edges. GLB drops them, which originally caused two bounds/point failures. Cleanup removes these points with **zero surface faces removed**.
3. Replacing material slots initially reset polygon material indices. Those indices are now preserved; nine distinct materials actually reach GLB/Unity. Unused source vertex-color attributes were removed because glTF multiplies them into the base color.
4. Existing linear tint multipliers are baked into PNGs to avoid exporter-dependent color-node handling. Their values did not change; this is a portable representation of the existing look, not another form iteration.
5. The fresh Unity probe lacked built-in Image Conversion/Unity Web Request Texture modules. Already installed modules were enabled locally; missing texture bindings and actual importer errors now fail the check. A partial prefab was never accepted as success.

Earlier failed reports are preserved in [intermediate-failures](../../../evidence/male-neutral-a01/intermediate-failures/). Only the final `delivery-002` model and `unity-static-004` result constitute delivery. One artistic proposal and one targeted correction were used; subsequent runs repaired/tested export representation, not new face designs.

## Reproduction and delivery

[Commands](REPRODUCE.md), [measured import contract](IMPORT_CONTRACT.json), [license/provenance](PROVENANCE.md), [execution evidence](../../../evidence/male-neutral-a01/execution.json), [verification](../../../evidence/male-neutral-a01/verification.json), [artifact record](../../../evidence/male-neutral-a01/artifact.json).

The review ZIP contains the editable independent `.blend`, static GLB, textures, configuration, scripts, credit/license notice, manifests and native previews. Large models are versioned release artifacts, not normal Git blobs. The original source rig, GPL UI scripts, widgets, actions and executable Text blocks are not distributed.

No purchase, vendor contact, external artist, paid generation, game edit or merge. No rig/animation/modular production, Ava work or PR33 changes. **Stop here for owner visual approval.** If the face/hair are not desirable as a player character, reject this candidate rather than extending random parameter adjustments. A later artistic identity pass or another base would require a new explicit scope; neither is started here.
