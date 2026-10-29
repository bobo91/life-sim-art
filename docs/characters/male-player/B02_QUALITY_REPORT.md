# MALE-NEUTRAL-B02 - local corrective rig and motion pass

**NO-GO for actual playable-character integration.** Foot contact and joint volume improve, and the technical export/runtime checks pass, but the matched Unity run elbow still has a pronounced triangular inner crease/outline corner. The local pass is stopped here as requested. A03 remains the approved identity; this is not A04. No merge or Phase C.

## Actual images and motion

[Matched B01/B02 run joints](../../../evidence/male-neutral-b02/previews/b01-b02-run-joints.png) | [Walk joints](../../../evidence/male-neutral-b02/previews/b01-b02-walk-joints.png) | [Idle joints](../../../evidence/male-neutral-b02/previews/b01-b02-idle-joints.png) | [Identity comparison](../../../evidence/male-neutral-b02/previews/b01-b02-face-identity.png).

[New MP4 - four clips](https://github.com/bobo91/life-sim-art/releases/download/male-neutral-b02-v0.2/a03-b02-unity-motion.mp4) | [16m MP4](https://github.com/bobo91/life-sim-art/releases/download/male-neutral-b02-v0.2/a03-b02-unity-16m.mp4) | [Animated preview](../../../evidence/male-neutral-b02/previews/motion-preview.gif) | [Four phases](../../../evidence/male-neutral-b02/previews/motion-four-clips.png) | [16m sheet](../../../evidence/male-neutral-b02/previews/game16m-four-clips.png).

Both videos use126 actual Unity URP frames at24fps,5.25seconds, from imported idle2s/walk1s/run0.75s/turn1.5s. They are reproducible direct clip samples. Separate actual PlayMode evidence tests real Animator advancement and five crossfades. No frame synthesis or pose/image retouch; layout/labels/downscale only. Video cuts between clips are not presented as transitions. The16m camera remains the art proxy at50degree elevation/40degree vertical FOV, not Neighborhood or actual game lighting.

## What changed, and what did not

Only local weights on **794 body and326 pants vertices** were changed. A weight-only pass did not meaningfully restore elbow volume. Six explicitly baked half-angle support joints were therefore added: elbow/knee/wrist on each side, **52 to58 bones**. The original52rest frames are retained. Knee support uses half strength after full strength produced a boxier fold; no further variants are pursued. Finger hinge weights are locally smoothed without extra finger bones.

**29,367 triangles, ten meshes, nine materials remain.** Raw positions/topology, UV/material/packed-image hashes are unchanged. Head/eyes/brows/hair are not processed by the local weight pass. Matched Unity bind-face front and three-quarter decoded RGB pixels are **exactly identical** B01/B02. Original Snow, A01, A02, A03 and B01 files/evidence remain unchanged.

The supports are ordinary skinned bones with baked TRS channels in these four clips; no runtime CloudRig, constraint, dual-quaternion or custom corrective system. Future animations/retargeting must bake appropriate support channels. A Humanoid avatar will not invent them automatically.

## Joint quality: actual improvements and limits

- Elbow and wrist hold more volume, but the Unity run comparison still shows an angular elbow and triangular inner crease. More projected area does **not** mean the joint is visually fixed.
- Knees are somewhat fuller/less pinched; trouser seam ridges and low-density angular outlines remain. The ordinary-run change is modest. Finger/wrist stress looks rounder but remains stylized/angular.
- Fixed-ring covariance-area ratios to bind improve for run elbow0.8404 to0.9857, elbow90stress0.7192 to0.9819, wrist45stress0.9205 to0.9655. These9/32-vertex ring diagnostics are **not enclosed-volume or visual-quality certification**. The matched images determine the NO-GO.
- Matched everyday reach/gesture and natural knee-flexion poses were rendered on the final saved source; original major-bone pose differences stay below4.18e-7 in matrix elements. No exploding mesh/new open tear was found in reviewed views. This is not exhaustive self-intersection or unrestricted range-of-motion proof.
- **B01 test correction:** its standalone knee test rotated the downward shin by-90degrees, anatomically hyperextension. That historical comparison is retained but not called ordinary flexion. B02 also compares physiological+90degree flexion on both versions. B01 history is not rewritten.

[Everyday reach/gesture comparison](../../../evidence/male-neutral-b02/previews/everyday-comparison.png) | [Natural knee flexion](../../../evidence/male-neutral-b02/previews/natural-knee-comparison.png) | [Joint selection and rejected alternatives](../../../evidence/male-neutral-b02/joint-selection.json).

## Turn contact - measured with the same B01 method

The turn now uses three placements: R45degrees outward, L90degrees, R90degrees. World-space stance position and orientation are locked. Swing separates smooth lift, raised planar transfer and lowering; existing two-link legs are used without stretching. The32mm lift and timing avoid the initial candidate's crossing feet and excessive knee speed. A0.05mm pose clearance addresses numerical subframe penetration; the bind mesh is not moved.

| Measurement | B01 | B02 final delivery |
| --- | ---: | ---: |
| Maximum stance-foot planar speed, same24fps/188+188sole vertices/3mm contact test |0.206781245m/s|0.000000682m/s|
| Additional96fps subframe stance speed |not compared|0.008511359m/s|
| Minimum sole height, additional96fps |not compared|+0.02439mm|

Main24fps reduction exceeds99.9996%; do not conceal the nonzero subframe residual. There is no sampled penetration in the final96fps test, not a guarantee on arbitrary terrain/physics. The path check finds zero projected sole-hull overlap at96fps; it is not exhaustive3D collision detection. Knee bend is20.26-45.02degrees, maximum sampled speed about280degrees/s, maximum step2.92degrees at96fps, and length error below0.000000072m. The smooth analytic target path is baked at24fps; it is not mathematically jerk-free after arbitrary engine interpolation.

[Exact paired final measurements](../../../evidence/male-neutral-b02/paired-contact.json) | [Path/reach evidence](../../../evidence/male-neutral-b02/turn-path-clearance.json). An earlier two-step candidate passed the contact number but crossed shoe footprints and was rejected, demonstrating why numeric checks alone were insufficient.

## Actual export and Unity verification

- Blender4.5.14 saved-source reopen and independent GLB reimport:58bones, normalized at most4influences, no discarded mapped mass; five poses per clip match within **0.000004758m** bidirectional nearest vertex distance.
- A fresh repeated build produces identical GLB bytes and geometry/appearance/weights/support/motion report. Blend container bytes and another full Unity sweep were not repeated.
- Actual isolated Unity6000.5.8f1/URP17.5/glTFast6.20/D3D11 import/render/reopen passes:10skins/58bindposes/29,367triangles/9supportedURPmaterials, no probe/import errors, source/import GLB unchanged and same reopened sampled pose.
- Actual PlayMode advances all four clips. Five0.2second crossfades idle-walk-run-walk-idle-turn remain finite and reach targets; fifty actual near/16m transition captures exist. Maximum monitored vertex step is0.172m in walk-run, but sampling is not cadence-normalized, so this does **not** certify smoothness, acceleration/jerk or planted transition feet.
- Unity Search indexing, licence-token-update and Mono shutdown warnings are recorded separately; probe assertions pass. No claim that the entire editor log is error-free. Blender diagnostic renders used CPU Cycles12samples; no Linux or Blender GPU run claimed.

[Actual crossfade captures](../../../evidence/male-neutral-b02/previews/playmode-crossfades.png) | [Runtime report](../../../evidence/male-neutral-b02/playmode-report.json) | [GLB roundtrip](../../../evidence/male-neutral-b02/blender-glb-roundtrip.json) | [Identity evidence](../../../evidence/male-neutral-b02/identity-comparison.json).

## Remaining blockers and smallest next action

1. **Elbow shape at ordinary run remains the primary art blocker.** Local weights/supports alone did not achieve sufficient near-view quality. Do not continue parameter tweaking or expand the rig.
2. Knee seam/finger angularity and transition cadence/contact remain quality limitations. Walk/run speeds are still not matched to a gameplay controller. Turn is a visual skeletal90degree yaw, not tested game-heading/root-motion integration.
3. Humanoid retargeting, new animation support baking, facial keys/blinks, clothing/body variation, performance/build/collision/terrain integration remain unproven. The source still contains only visible masked body surfaces, not a complete wardrobe-ready hidden body.

**Recommend one separate, local elbow trial using a small corrective shape activated by elbow bend, beginning with the exact same run pose.** Keep neutral A03, triangle count, face and the existing rig; no new general animation system. Verify visual benefit before propagating to clips. This is a proposal only, not performed or labelled Phase C. If a local corrective cannot solve the crease, propose narrowly scoped elbow topology work rather than rebuilding Snow or changing the protagonist.

## Delivery and licensing

[Commands](B02_REPRODUCE.md) | [Import contract](B02_IMPORT_CONTRACT.json) | [Download record](../../../evidence/male-neutral-b02/artifact.json) | [Provenance](../../../evidence/male-neutral-b02/provenance.json).

Source remains [Blender Studio Snow v4](https://studio.blender.org/characters/snow/v4/), **Snow Rig (CC) Blender Foundation | studio.blender.org**, modified under [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Source credit/licence/change notice retained; no new external mesh, animation, purchase or service. Source CloudRig/UI code is not executed/delivered. Four original B01 motion clips are locally corrected; no purchased animation library. Spend0SEK.

PR39 stays draft. No game-repository change, automatic merge, Phase C or additional model iteration. Stop for owner review of the partial improvement and NO-GO.
