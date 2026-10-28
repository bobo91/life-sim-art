# MALE-NEUTRAL-A02: visual revision for owner review

A01 method: owner GO. A01 protagonist appearance: owner NO-GO. A02 is the requested second static visual candidate, **not visually approved**. PR39 remains draft. No Phase B, rig/animation/clothing system, purchase, vendor contact, game change or merge.

## Actual images

[Face A01/A02](../../../evidence/male-neutral-a02/previews/a01-a02-face-comparison.png) | [Same clay material](../../../evidence/male-neutral-a02/previews/a01-a02-clay-comparison.png) | [A02 front/side/three-quarter body](../../../evidence/male-neutral-a02/previews/a02-body-views.png) | [Native16m](../../../evidence/male-neutral-a02/previews/game_16m_front.png) | [A01/A02 at16m](../../../evidence/male-neutral-a02/previews/a01-a02-game16m.png) | [Matched URP faces](../../../evidence/male-neutral-a02/previews/a01-a02-urp.png).

Nine colored Blender views, four clay comparison views and four final Unity views are supplied. Native images are unchanged; sheets only resize/layout/add labels. Blender A01/A02 camera metadata matches exactly, with the same retained A01 world and area lights. Clay uses one identical neutral material on both, making the geometry change visible independently of complexion.16m means16m camera-target distance,50-degree elevation and40-degree vertical FOV at1280x720; this remains the art proxy, not a newly verified game camera.

## Geometry and identity

- The cranium/cheek region is narrowed, with a less narrowed chin so the outline becomes more oval. Chin projection is reduced and the lower face relaxed.
- Ears are locally shortened and tucked; nose wings/tip are narrowed and projection reduced. A pointed central nasal underside found in QC was locally rounded, leaving the rest of the correction intact.
- Upper/lower lips are transformed together about their measured shared seam at A01 Z1.495m. Their cushion and width are reduced; corners rise slightly.
- Eyeballs receive uniform scale around each center, coordinated with the socket region. Upper-lid tissue opens slightly. Brow masses are thinner and gently arched.
- All five retained A01 braided crown pieces are replaced by **three original broad swept forms**. Only the authored scalp cap remains. The first A02 scalp slit was closed by overlapping the quiff volumes.

Head topology stays **3,719 vertices /7,264 triangles**, with identical vertex order, polygon connectivity and UV. Mean head-vertex displacement from A01 is **7.44mm**, maximum **29.07mm**. The sampled deformation Jacobian is positive at all head vertices (minimum0.313); this detects local inversion at those samples, not every possible surface intersection.

**What remains from Snow:** underlying head/eye/brow topology and authored anatomical structure, eye texture,547-vertex scalp cap, plus all body, clothing, shoe geometry and their textures. All six body/clothes/shoe geometry hashes are unchanged. This is an attributed derivative, not an entirely original character mesh. The fair warm skin remap retains subtle source variation across head/neck/arms/hands; color is supplementary to the shape changes, not their substitute.

## Is Snow still suitable, and can the rig survive?

**Yes as the present visual/topology base:** the clay comparison shows substantial identity changes without replacing facial loops. No additional base is downloaded or proposed for a parallel experiment. The source body remains a useful authored foundation.

**Animation compatibility is not yet proven.** The original head has50 relative shape-key blocks, including its Basis/Fixholes structure, and named skin weights. A01 froze evaluated geometry and omitted its rig/group definitions. A02 is a deformation in that evaluated A01 metre frame, not a verified new original bind shape. Do not paste this posed head into the original Basis and retain unchanged correctives: that can double-apply Fixholes/lattice corrections.

After visual approval only, the safe path is an explicitly rebased bind-space identity edit preserving vertex order/UV/named weights, transforming each original absolute key consistently. Relative delta becomes `F(K)-F(K_relative)`. Eye/bone pivots, lattice domains and combined blink/smile/jaw shapes must be transported and tested. Original head lattices differ between viewport/render evaluation, which must be reconciled. Same topology alone is not a rig guarantee. The internal teeth/gums/tongue omitted in A01 also remain absent here; jaw-open fidelity is untested. No such rig rebuilding or animation tests are implemented here.

## Triangle reduction plan, not yet performed

Current A02: **40,645 triangles**, down1,432 from A01 solely through the hair replacement. No face-budget decimation is hidden in this visual revision.

| Part | A01 | A02 | Proposed first LOD0 budget |
| --- | ---: | ---: | ---: |
| Head |7,264|7,264|**7,264 unchanged**|
| Eyes |2,756|2,756|**2,756 unchanged**|
| Brows |1,504|1,504|**1,504 unchanged**|
| Hair |3,816|2,384|2,000|
| Arms/hands body |6,500|6,500|4,000|
| Shirt |3,246|3,246|2,200|
| Pants |5,179|5,179|3,200|
| Shoes combined |11,812|11,812|2,400|
| Total |42,077|40,645|**25,324 estimated**|

First optimize the shoes: they consume28.1% of A01, including5,372 triangles in decorative parts and1,920 in a thin sole. Replace/reduce decorative loops and retain the shoe silhouette with the existing normal maps. Then reduce cloth loops that do not affect silhouette and arm density while protecting finger-joint loops. Hair sweep sampling can be reduced modestly. Preserve the **entire face/eyes/brows** in this first pass. Compare near and16m images plus geometry/export before accepting each optimized copy; keep the high-quality source.

This is a credible **25-28k** first target, about40% below A01, not an achieved measurement or a promise of zero visual loss.16k requires later LOD/retopology choices, not blind global Decimate. Material consolidation and population/skin performance also remain untested. None of this optimization production starts before the visual gate.

## URP look and actual checks

A02 uses metallic0, IOR1.5 and standard dielectric specular0.5 throughout. Roughness: skin.72, lips.67, hair.83, shirt.84, eyes.30. The final GLB has **no extensions**, eliminating A01's ignored `KHR_materials_specular`. Actual Unity6000.5.8f1/URP17.5/glTFast6.20 import has no warning/error diagnostics; all nine material factors and texture bindings pass.

The old intensity2 hard key clipped the fair skin. Final matched A01/A02 review uses key1.5, fill0.5 and ambient0.4, with **post-processing explicitly disabled**. An earlier requested ACES/+1EV gave identical pixels in the minimal probe, so it is not claimed as working. Final actual captures show matte skin/hair rather than the former strong plastic sheen. Blender area-light/AgX and this linear/sRGB Unity stage still differ; this is not a game-lighting match or integration approval.

Focused validation reused the existing checker once:243 saved/reopened Blender and actual GLB checks passed,0 failed; static socket/hair diagnostics retained. One face render was repeated: geometry hashes, GLB bytes and decoded face pixels match. No broad test suite or rig/animation test was added. Build/render history records one form pass, one targeted correction and one local nose-QC repair; those earlier models are preserved locally, not passed off as final.

## Limits and decision

The face is more oval and the hair/features differ visibly from A01, but the stylized eye/brow family still has Snow ancestry. Expression remains gentle/reserved and somewhat sleepy; the intended25-30 age and sufficiently independent identity require owner judgement. Hair remains broad sculpted masses, not a finished groom. **Ready for visual review, not production approval.**

[Import contract](A02_IMPORT_CONTRACT.json) | [Commands](A02_REPRODUCE.md) | [Provenance](../../../evidence/male-neutral-a02/provenance.json) | [Actual checks](../../../evidence/male-neutral-a02/verification.json) | [Download record](../../../evidence/male-neutral-a02/artifact.json).

A01 files and release remain unchanged. Source credit: **Snow Rig (CC) Blender Foundation | studio.blender.org**, modified under [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). External spend:0SEK. Stop for the owner's next visual decision. No merge and no Phase B.
