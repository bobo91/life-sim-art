# B03 - isolated elbow corrective-shape proof

**NO-GO. The clear visual-improvement gate was not met, so B03 stops before GLB export and Unity.** This does not establish a glTF/Unity limitation: neither was tested. No topology change, second shape recipe, merge or Phase C.

## Actual matched renders

[Exact run25% - both sides](../../../evidence/male-neutral-b03/previews/run25-comparison.png) | [Physical90degree elbow - both sides](../../../evidence/male-neutral-b03/previews/elbow90-comparison.png) | [Nearly straight10degree arms](../../../evidence/male-neutral-b03/previews/near_straight10-comparison.png). Native800x800PNG pairs are in previews/native/.

These are actual Blender4.5.14 CPU Cycles12sample renders of the preserved B02 and the same single B03 candidate, using identical pose/camera/lights within each pair. The source run25% is exactly frame5.5, matching the prior B01/B02 Unity comparison. No frame synthesis or image retouch; sheets only resize/layout/add labels.

- **Run:** the right elbow is a little rounder, but remains faceted. The left gains a small upper-inner protrusion and retains its notch/outer corner. Improvement is uneven rather than clearly successful.
- **90degrees:** both remain broad and chamfered; the left becomes flatter around the bend and still has an inner notch. This is not a consistently natural rounded contour.
- **Nearly straight:** activation returns to0 and both B02/B03 decoded RGB images are exactly identical. No new straight-arm bulge was found.

The initial diagnostic pass used a legacy T-pose/worldZ test for90/nearstraight. Only those diagnostic poses were corrected: final pass002 holds the actual run upperarm and hinge-plane and sets physical direction angles to90/10degrees. The corrective coordinates are hash-identical across both passes, so this is **one shape candidate, not two model iterations**. The final judgement uses pass002; initial metadata is retained as intermediate evidence.

## What was actually built and checked

Two relative keys on M01_body, one per elbow, are derived by a tightly masked posed-space Taubin relaxation at the exact run pose, then inverted through the existing blended linear-skin matrix. Correction is limited to?65mm along the elbow zone, with a7mm maximum posed displacement. Saved nonzero key coordinates affect34vertices left/31right; rest-key maximum about7.56mm. No new triangles, weight painting, bone, material or facial change.

Activation is calculated from the angle between posed upper/lower bone directions minus their neutral rest-angle, not clip name or forearm twist. Neutral rest angle is about8.74degrees. Reference run physical angles are72.21degrees L/72.69R, giving incremental bend63.47/63.95degrees and full corrective weight. Activation is0 below12incremental degrees, smoothly reaches1 at each measured run bend, and is clamped thereafter. Physical90degrees is full weight; physical10degrees returns0. In this isolated proof the Python harness evaluates the angle and sets the two values per test pose. It is **not a delivered live runtime system or baked animation pipeline**.

Focused saved-file reopen checks confirm:

- All ten raw meshes/UVs/materials/skin weights,58bone rest hierarchy and four original action curves are identical to B02.
- Neutral Basis is exactly preserved; evaluated neutral float error is below0.000000358m.
- Total geometry remains29,367triangles. Head/hair/eyes/brows are untouched; no identity redesign.
- Original B02 source SHA remains8300f581fa4e5a7f012d70ae9aadd0d7ca9eb99214b5a8699a1f65f0a9c8e96c.

[Preservation results](../../../evidence/male-neutral-b03/preservation.json) | [Pose/activation metadata](../../../evidence/male-neutral-b03/isolated-proof.json) | [Visual decision](../../../evidence/male-neutral-b03/visual-gate.json).

B02's turn curves/leg rig/shoe meshes are unchanged and the morph masks affect only the elbows, so its contact data is retained by construction. There was **no new B03 foot-contact or Unity regression run**. Full morph-driven idle/walk/run playback, GLB target export/import and runtime return-to-straight remain untested because the first visual gate failed. The saved candidate opens at the corrected reference run sample; it is an inspection prototype, not an automatically activated player asset.

## Why a local shape was insufficient

Actual topology audit found a fully triangulated low body with2,748vertices/5,460triangles and no custom normals. The crease is real sparse geometry, not stale split-normal shading. Each elbow has only29vertices within?55mm and11within?20mm, with irregular valences rather than regular bending loops. A shape can reposition these existing corners but cannot add silhouette sampling.

The preserved A03 high body has3,268vertices/6,500triangles, with126vertices per elbow within?55mm and54within?20mm. The earlier global body optimization therefore removed much of the elbow-zone density. This is a concrete local fallback source, not a reason to replace A03's accepted identity.

[Low-body audit](../../../evidence/male-neutral-b03/mesh-audit.json) | [High/optimized local counts](../../../evidence/male-neutral-b03/high-density-comparison.json).

## Smallest proposed next action - not performed

Recover a **small band of elbow bending loops only**, using the preserved A03 high connectivity as a guide and projecting to the current neutral elbow surface/boundary. Keep the approved face, neutral silhouette,58bones and materials. Reuse local B02 weighting and compare the same run/90/10poses on both sides before considering export. The exact added triangle count must be measured in that separately approved local patch trial; no budget or success is promised here. **Do not apply the topology change without owner approval.**

## Export status and delivery

[Commands](B03_REPRODUCE.md) | [Unexecuted conditional export notes](B03_EXPORT_FEASIBILITY.md) | [Provenance](../../../evidence/male-neutral-b03/provenance.json) | [Review artifact record](../../../evidence/male-neutral-b03/artifact.json).

The installed exporter/glTFast source was inspected for a minimal morph path, but no B03 GLB, Unity import, PlayMode run or video was generated. No generic corrective architecture was built. The artifact is explicitly a rejected Blender-only inspection proof.

Source remains [Blender Studio Snow v4](https://studio.blender.org/characters/snow/v4/), modified under [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Required credit: **Snow Rig (CC) Blender Foundation | studio.blender.org**. No new external mesh/animation/service or purchase; source CloudRig/UI code is not executed or included. A01/A02/A03/B01/B02 history is preserved. No life-sim-game change, merge or Phase C. Stop for owner review.
