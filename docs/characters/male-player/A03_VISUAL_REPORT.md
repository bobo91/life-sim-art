# MALE-NEUTRAL-A03: focused polish and appearance-first optimization

A02 is owner-approved as the visual foundation. A03 is pending the next visual decision. **No merge, production or Phase B.** A01/A02 remain unchanged.

**Budget result:29,367 triangles. The25-28k target is not fully met:1,367 above the upper target.** The28,263 candidate damaged lace volume in close-up; the selected gentler shoe recipe preserves the rounded form better. This is an explicit appearance-first tradeoff, not a claim that the target was achieved.

## Actual views

[A02/A03 face](../../../evidence/male-neutral-a03/previews/a02-a03-face-comparison.png) | [A03 body front/side/three-quarter](../../../evidence/male-neutral-a03/previews/a03-body-views.png) | [Matched URP](../../../evidence/male-neutral-a03/previews/a02-a03-urp.png) | [Native Blender16m](../../../evidence/male-neutral-a03/previews/game_16m_front.png) | [A02/A03 at16m](../../../evidence/male-neutral-a03/previews/a02-a03-game16m.png).

[Actual Unity16m](../../../evidence/male-neutral-a03/previews/A03_unity_game16m.png) | [A02/A03 Unity16m](../../../evidence/male-neutral-a03/previews/a02-a03-urp16m.png). These are isolated art-camera proxy captures, not the game world.

Optimization quality: [body before/after](../../../evidence/male-neutral-a03/previews/optimization-body-comparison.png), [shoe close-up](../../../evidence/male-neutral-a03/previews/optimization-shoe-comparison.png), [hand close-up](../../../evidence/male-neutral-a03/previews/optimization-hand-comparison.png), [high/optimized16m](../../../evidence/male-neutral-a03/previews/optimization-game16m.png). These are actual unretouched renders with matching cameras/lights, not view-specific geometry. Sheets only resize/layout/add labels. The shoe/hand views are extra inspection close-ups, much closer than normal gameplay.

## Small visual refinements

- Eyes and coordinated sockets95% of A02 size; lower-lid tissue rises0.6mm to reduce the lower white ring. No additional upper-lid drop or gaze change.
- Local jaw smoothing and chin projection back1mm soften the contour. Head topology/UV remain identical; maximum head shift from A02 **1.94mm**, mean **0.39mm**. Nose/lips/overall identity are retained.
- Brow corners are gently rounded with a tiny arch adjustment, preserving the relaxed placement.
- Existing swept locks get rounded front caps,6% bounded width variation and1-2mm crest variation. Hair cross-section height is slightly flattened, with the overlapping silhouette retained.144 extra triangles support rounded ends. Roughness.86 replaces.83; the brown hue is unchanged. Hair remains deliberately broad sculpted masses, not a realistic groom.
- Skin, eyes, clothing colors and all13 source PNG files remain byte-identical to A02. Body proportions remain the approved foundation.

## Measured optimization

| Part | A02 | A03 editable high | A03 selected optimized |
| --- | ---: | ---: | ---: |
| Head/eyes/brows |11,524|11,524|11,524|
| Hair |2,384|2,528|2,528|
| Arms/hands |6,500|6,500|5,460|
| Shirt |3,246|3,246|2,368|
| Pants |5,179|5,179|3,365|
| Shoes combined |11,812|11,812|4,122|
| **Total** |**40,645**|**40,789**|**29,367**|

Reduction: **27.7% versus A02**, **28.0% versus the refined A03 high source**. Head/eyes/brows/hair hashes remain identical before/after optimization. All2,504 protected hand positions and boundary/material/sharp/UV-seam positions remain exact within1e-7m. Body bounds remain unchanged; these facts do not imply an identical surface everywhere.

The chosen shoes use gentler decoration ratio.45 and sole.30. Decoration sampled source-to-optimized p95 falls from1.23mm in the tighter candidate to about0.39mm, maximum from4.17 to1.10mm. Source split-normal transfer improves shoe shading without changing simplified geometry. A final own-face hemisphere guard replaces reversed transferred corner normals on thin shoe surfaces; this fixes shading only, not geometry or triangle count. The UNSUBDIVIDE alternative was visually rejected. This stays one controlled optimization iteration, not a new modeling/rigging system.

**Actual losses:** tiny shoe-decor/sole curves are still more angular in extreme close-up, and some cloth/arm contours are slightly simplified. The first candidate's clearly flattened/jagged laces are not the final model. No meaningful loss was apparent in the reviewed native16m pair; normal full-body/near views preserve the face, hair and clothing forms. It is not lossless. Bidirectional surface sampling is diagnostic, not a full Hausdorff, self-intersection or screen-space certificate. No new visible open eye/lip/cloth tear was found in the reviewed views.

The unoptimized **character_high.blend** is retained alongside the optimized **character.blend** and GLB. Further reduction is deferred rather than sacrificing approved face/hair or introducing another identity pass.

## Export, URP and rig status

The established Blender4.5.14 saved/reopened-source and GLB checker passed243 checks,0 failed. The final geometry/GLB and one decoded face render reproduced identically; the other16 views were not repeated. No broad test suite was expanded.

Actual isolated Unity6000.5.8f1/URP17.5/glTFast6.20 D3D11 import/render/reopen passed. Texture bindings/material factors are present, with no import diagnostics. A02 and A03 are captured under the same no-postFX review key1.5/fill0.5/ambient0.4 setup. Core PBR remains supported with no extensions; hair is matte and skin keeps A02's roughness. This is not game-world integration or a game-lighting match.16m uses the same art proxy:50-degree elevation,40-degree vertical FOV,1280x720.

**Snow-rig reuse remains explicitly unproven.** Original Snow with its rig/50-key head is untouched. A01/A02/A03 are static evaluated derivatives with no delivered rig, animation, teeth/tongue or shape-key set. Body/cloth/shoe vertex order changes during simplification; original weights cannot be copied by index. The high copy is editable static reference, not a verified rigged source. A separately approved bind/key/pivot/lattice rebase and high-to-LOD weight transfer would be needed before animation claims. None is built here.

[Measured import contract](A03_IMPORT_CONTRACT.json) | [Reproduction commands](A03_REPRODUCE.md) | [Provenance](../../../evidence/male-neutral-a03/provenance.json) | [Download record](../../../evidence/male-neutral-a03/artifact.json).

Source credit: **Snow Rig (CC) Blender Foundation | studio.blender.org**, modified under CC BY4.0. No source rig/UI code executed or included. No purchases, vendor contact, game changes or merge; external spend0SEK. **Stop for A03 visual approval.**
