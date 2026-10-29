# A03 Locomotion Fit v0.1

**GO for the steady4.0 m/s gait fit at playback1×. The complete start/stop/rapid-turn experience remains a qualified review candidate, not an unconditionally approved integration.** Owner visual approval is required. No merge, Phase C or game integration.

The source is **B02 only**: approved A03 identity,29,367triangles,58bones. No B03/B04 mesh or shape is used. No vertex, weight, material, rest bone or elbow correction was made. B02's elbow limitation remains visible in close-ups and accepted only at the distant camera under the owner's instruction.

## Actual Unity evidence

[Movement storyboard](../../../evidence/male-locomotion-fit/previews/motion-storyboard.png) · [50°/16m storyboard](../../../evidence/male-locomotion-fit/previews/game16m-storyboard.png) · [Elbows retained](../../../evidence/male-locomotion-fit/previews/elbows-retained.png) · [Foot samples](../../../evidence/male-locomotion-fit/previews/feet-start-stop-turn.png) · [Worst transition frames](../../../evidence/male-locomotion-fit/previews/transition-worst-frames.png).

The two10second MP4s are actual Unity URP/PlayMode frames: `a03-locomotion-fit-unity.mp4` and `a03-locomotion-fit-unity-16m.mp4`, published with the [versioned review release](https://github.com/bobo91/life-sim-art/releases/tag/male-locomotion-fit-v0.1). Each retains all240frames at24fps, with only an80pixel footer added. Container timing/frame count and reopening/decoding one frame per scenario were verified. No synthetic motion, video speed-up, interpolated frames, recolouring or model retouch. Native evidence and selected decoded frames are included in the archive.

The probe reuses the B02 Unity setup. It runs an ordinary Generic-style Animator in **actual PlayMode**, explicitly evaluated at24Hz with automatic evaluation disabled to avoid double advancement. This is a scripted art-side trajectory, **not OS input, the real controller or Neighborhood**. Speed changes immediately0↔4m/s; there is no acceleration, root-height correction, foot-locking or hidden root easing. Desired movement direction changes immediately while visible heading catches up at720°/s. This input/heading relationship is an explicit probe assumption for the game owner to confirm.

The full camera follows translation from a fixed world angle. The standard camera uses50°pitch,16m distance and40°verticalFOV, following translation without rotating its world offset. A1m ground grid and shadows expose contact and translation. This is not a certification of game lighting, terrain or performance.

All contact heights refer to the contract planeY=0; the presentation floor is2mm lower. Reported negative heights therefore differ from visible floor penetration by2mm.

## Gait changes and measurements

| | B02 walk | New walk | B02 run | New run |
| --- | ---: | ---: | ---: | ---: |
| Intended world speed at1× |0.552m/s|**1.4m/s**|1.533m/s|**4.0m/s**|
| Full cycle |1.000s|1.000s|0.750s|**0.625s**|
| Steps/min |120|120|160|**192**|
| Same-foot stride at matching speed |0.552m|1.400m|1.150m|**2.500m**|
| Designed planted excursion |0.320m|0.840m|0.460m|**0.750m**|

Run is authored for4m/s, rather than playing the old clip at2.61×. Walking4m/s was rejected as visually implausible; the walk is a lower-stick example, not a new gameplay walk/run mechanic. Intermediate stick speeds and walk/run phase-preserving blends are not certified.

New curves use96Hz keys on the existing24fps scene timebase. Analytic leg reach is checked before saving/exporting, without ankle clamping. A modest run lean, knee recovery, heel/toe roll and counter-swing are authored within the existing rig. The animated pelvis is lowered95mm for run and65mm for walk to accommodate the actual short leg chain; neutral geometry/proportions remain exact. Hands remain stylized/open and joints retain B02's angularity.

Before any model was saved, retained reach preflights found late-swing overextension. The landing excursion was centred under the measured hip rather than extending the skeleton. `candidate-006` was the first saved motion; its direct exporter retained an extra positive frame1 offset. The final `delivery-001` uses the **same authored poses**, with only animation-input timestamps normalized to zero. GLB durations are now exactly idle2s/walk1s/run0.625s. The preserved idle Fcurves are exact; exported idle TRS matches baseline within9.54×10⁻⁷ components at96Hz. The normalization does not touch TRS values, meshes or skins.

Actual final Unity samples after fades settle:

- Straight4m/s: maximum world speed of stable near-ground sole vertices **0.01361m/s**, mean of per-frame maxima0.00530m/s. Cadence looks like a brisk, stylized run; persistent old speed-mismatch skating is removed.
- Settled1.4m/s walk: corresponding maximum **0.00806m/s**, mean0.00286m/s. This supports only the tested speed.
- Idle retains its existing motion and practically stationary sole contact.

The independent saved-Blender192Hz check finds run minimum sole height−0.0503mm, contact-vertexP95speed0.02568m/s/RMS0.04385/max0.41852; walk minimum+0.792mm,P95speed0.00466/RMS0.02798/max0.70454. Maxima include rolling/lift-off boundaries. These distributions are **not** the same statistic as Unity's per-frame maximum. Foot-centre motion is recorded separately because a rolling foot's centre moves despite a near-stationary heel/toe contact. Neither metric proves terrain/physics grounding.

## Starts, stops and turns — remaining problems

One bounded Animator-setting correction compared initial0.12s start/0.16s stop to **0.08s/0.08s**, destination time0 and identical GLB/root commands. This shortens the sampled bad-contact exposure; it is not a universal improvement.

| Segment | Initial minimum sole | Final minimum sole | Initial/final frames below−1mm at24Hz |
| --- | ---: | ---: | ---: |
| Start4m/s |−16.52mm|−17.86mm|2 /1|
| First stop |−29.54mm|−9.04mm|3 /1|
| Restart |−16.61mm|−17.95mm|2 /1|
| Second stop |−38.04mm|−29.47mm|3 /1|
| Walk start |−30.62mm|−25.08mm|2 /1|
| Walk stop |−17.83mm|−35.20mm|3 /1|

These are sampled frame counts, not continuous-time guarantees. Final start/restart near-ground contact-speed maxima rise to~8.2m/s; the walk-stop maximum rises to6.07m/s. Feet reposition abruptly during the short blend. At16m the depth error is small on screen, but the brief change in leg/hip pose remains a quality tradeoff. **Do not call the transitions clean or contact-locked.** Worst frames and their neighbours are deliberately shown; those sheets crop native full-camera pixels as documented, not new 3D renders.

90° and180° direction changes reach the commanded720°/s and retain approximately1mm minimum sole clearance in the sampled sequence. However, contact-point sliding peaks at **5.93/8.23/4.57m/s** across the three turn segments. The model turns without the old1.5s turn clip, without lean/pivot animation or world-space foot locking. Fast turns look responsive but mechanical; they are not realistic planted pivots. No camera-distance waiver for these defects is implied by B02's elbow waiver.

## Technical results and decision

- Saved-file reopen: all10meshes, UVs, normals, weights, material bindings,9materials/13images,58restbones/hierarchy and raw idle action are **exact B02 data**.29,367triangles unchanged.
- New GLB geometry/skins/UV/normals/indices, inverse binds, joint order, materials and embedded images are exact against B02. Only motions/version metadata differ.
- Repeating the frozen authoring/config in a fresh Blender process produces a **byte-identical GLB**, SHA256532ce438b24f69e14c099d956706d69e6e6b8531e0c162e92f72756bb60046b0. Blend-container byte identity is not claimed.
- Three clips only: idle/walk/run. All58joints have baked TRS channels (174channels per clip), including six supports; endpoints match. No old turn or root motion.
- Fresh Blender GLB reimport: nine phases per clip, maximum sampled skinned surface difference below8µm (1mm test tolerance). Not an exhaustive posed-intersection test.
- Actual Unity6000.5.8f1, URP17.5.0/glTFast6.20/D3D11: skin/material/import, scene save/reopen, three clips and scripted PlayMode trajectory capture pass. All three imported loops are true; no turn-loop trap remains.
- The exporter warns about meshes being siblings of the armature rather than children. This is the preserved B02 hierarchy; raw bindings, fresh reimport and actual Unity skin checks pass. Instanced/duplicated armatures are not tested.
- Root speed measurement matches commands within0.000022m/s and yaw never exceeds720°/s. No actual game controller, OS-input, performance or Humanoid retargeting test was run.

**Recommendation:** retain this candidate as a successful4m/s loop fit and review the two videos at the intended16m camera. There is **NO-GO for an unqualified claim of clean starts/stops, planted turns or unrestricted integration**. A limited First Playable use would require the owner's explicit visual acceptance of the documented brief transition/pivot tradeoffs. Close-up elbow quality remains NO-GO under the existing decision. Stop here; no further tuning, new animation system, game edit, merge or Phase C is authorized automatically.

[Import contract](LOCOMOTION_FIT_IMPORT_CONTRACT.json) · [Q1–Q11 update](LOCOMOTION_FIT_Q1_Q11.md) · [Commands](LOCOMOTION_FIT_REPRODUCE.md) · [Artifact fingerprints](../../../evidence/male-locomotion-fit/artifact.json).

Snow Rig (CC) Blender Foundation | studio.blender.org; modified [Snow v4](https://studio.blender.org/characters/snow/v4/) under [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). No upstream CloudRig/UI code is included or run; no external animation service, new model or purchase.
