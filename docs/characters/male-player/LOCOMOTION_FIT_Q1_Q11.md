# A03 Locomotion Fit — integration contract and Q1–Q11

Status: **technical GO for the steady4m/s loop fit; NO-GO for unqualified gameplay integration or claims of clean transition/pivot contact**. Final demonstration uses0.08s start/stop fades and phase0. The measured steady loops fit their intended translation speeds; starts/stops and rapid turns retain contact limitations documented below. The owner must judge the normal-camera tradeoff. This is the owner-authorized motion-only follow-up on B02, not B03/B04. B02's A03 identity, 29,367 triangles and 58-joint rig are unchanged. The owner accepts its elbow limitation for the normal distant camera only, not close-ups. Nothing in this document approves merge, Phase C or automatic gameplay integration.

## Q1 — Candidate, source and delivery

Asset ID remains `chr_player_male_poc_001`; review version is `male-locomotion-fit-v0.1`. The saved delivery is `build/male-locomotion-fit/delivery-001/`, not an intermediate candidate directory. Final GLB SHA256 is **`532ce438b24f69e14c099d956706d69e6e6b8531e0c162e92f72756bb60046b0`**; editable `character_locomotion_fit.blend` SHA256 is **`1af66dd0d78bc047492615d578e3cd122fb08e6d107ea9d2f881aca4e80ae25e`**. Archive/release/download fingerprints belong to the accompanying `evidence/male-locomotion-fit/artifact.json` delivery record; this source snapshot does not embed a self-referential ZIP hash. These are new candidate hashes, not copied B02 hashes. Owner approval is a separate gate.

The only geometric source is preserved B02 `character_b02.blend`, SHA256 `8300f581fa4e5a7f012d70ae9aadd0d7ca9eb99214b5a8699a1f65f0a9c8e96c`. Historical B02 GLB SHA256 is `4faa2eec33d131b7fcdc4b41720e5abbd16e03eab594bf764f3d7ae041de3d33`; **this is not the new candidate hash**. B03/B04 models, shapes and topology are excluded.

Neutral dimensions remain 1.738315 × 1.749405 × 0.306273 m (width includes extended arms). Bounds after glTFast's X mirror are min `(-0.8691574, -0.000000496, -0.1531364)`, max `(0.8691574, 1.7494049, 0.1531364)` m. Fresh validation003 confirms exact B02 raw geometry/skin/UV/normals/indices, bind matrices, joint order, materials and embedded image bytes in the new GLB. The saved source also preserves all ten meshes, weights, rest bones, object hierarchy and idle action exactly.

## Q2 — Real stride, cadence, phase and playback

All clips are in place: actual asset-root translation is zero. Design speed is the speed the controller must supply to cancel the planted sole's backward travel. A full same-foot stride is speed × full-cycle duration; it is not merely the excursion during stance.

| B02 baseline | Walk | Run |
| --- | ---: | ---: |
| Full-cycle duration | 1.000 s | 0.750 s |
| Stance fraction / duration | 0.58 / 0.580 s | 0.40 / 0.300 s |
| Stance excursion | 0.320 m | 0.460 m |
| Inferred design speed at1× | 0.551724 m/s | 1.533333 m/s |
| Measured maximum planted sole-centre speed,24fps | 0.551724796 m/s | 1.533334824 m/s |
| Same-foot effective stride | 0.551724 m | 1.150000 m |
| Cadence | 120 steps/min | 160 steps/min |
| Playback rate required for4m/s | 7.250× | 2.608696× |

Those playback multipliers imply870/417 steps/min and were rejected as the main fitting method. The new run is authored for4.0m/s at1×; walk represents a lower partial-stick speed instead of pretending4m/s is ordinary walking. Final GLB and Unity imported durations match the recipe:

| Final recipe and confirmed export timing | Walk | Run |
| --- | ---: | ---: |
| Designed translation speed | 1.4m/s | 4.0m/s |
| Full-cycle duration | 1.000s | 0.625s |
| Cadence | 120steps/min | 192steps/min |
| Same-foot stride at target speed | 1.4m | 2.5m |
| Stance fraction / duration / designed excursion | 0.60 / 0.600s / 0.840m | 0.30 / 0.1875s / 0.750m |
| Nominal playback rate | 1.0× | 1.0× |

The scene remains24fps and the idle action is exact B02 data. New gait curves are keyed every0.25frame (96Hz), exported without forced scene-frame resampling. Raw GLB and Unity durations are **idle2.000s, walk1.000s, run0.625s**; no extra1/24s padding remains. Each clip has174 baked TRS channels and exact raw first/last endpoint values, including support joints. The full same-foot stride is designed speed × confirmed full-cycle duration; foot-contact quality is measured separately below. Playback1× is the tested fit; no broader safe playback range or arbitrary partial-stick blending interval is certified.

In actual Unity PlayMode after the start fade has settled, straight run samples from1.3s to<3.0s translate at4m/s with maximum stable-contact-vertex speed **0.013607m/s**, mean of per-frame maxima0.005298m/s over20 contact-bearing frames. Settled walk from8.1s to<9.0s at1.4m/s has maximum0.008057m/s, mean per-frame maxima0.002856m/s over21 contact-bearing frames. These values support the steady-state speed fit; they do not certify starts/stops or pivots.

B02 and the new recipe start left landing at normalized0 and right at0.5 in both gaits. Shared nominal foot phase does not alone prove pop-free blending, because duty factors, pelvis height, pose and velocities differ. Raw GLB endpoints are exact and Unity loop closure at sampled poses is0m. Continuous velocity matching and pop-free walk/run phase-preserving blends are not certified. No runtime phase-matching framework is included.

## Q3 — Turning and controller authority

The old1.5s skeletal90° `turn` demonstration is **not a gameplay-turn source**. The intended candidate clip set is `idle`, `walk`, `run`; omission of `turn` is deliberate and must be reflected in importer/controller bindings. No replacement turn animation or root-motion system is supplied.

Controller-owned heading remains authoritative, `applyRootMotion=false`. At720°/s,90° takes0.125s and180° takes0.250s. A cyclic forward run cannot guarantee world-locked stance feet under arbitrary rapid yaw; actual turn sliding, limb crossing and pose discontinuities must be visible in the art-side Unity probe. Root acceleration, deceleration or yaw limits must not be silently eased to make footage look better than the real controller.

## Q4 — Rig and support joints

Required hierarchy is `CHR_PlayerMale_A01` with sibling children `A03_B01_Rig` and the ten `M01_*` skinned mesh nodes. Joints begin at `CHR_PlayerMale_A01/A03_B01_Rig/Hips`. Preserve all58 names, parents, paths and rest matrices, mesh/datablock names, weights and material bindings. Body datablock is `GEO-snow-body.002`.

`LOCOMOTION_FIT_IMPORT_CONTRACT.json` contains the full58 name/parent/path entries. The six support joints are `B02_Elbow.L/R`, `B02_Knee.L/R`, `B02_Wrist.L/R`. Validation003 confirms baked translation, rotation and scale for all58 joints in **every delivered clip**, including idle:174 channels per clip. New motions use the existing half-angle support behavior; no new rig, weight fix or generic corrective architecture was added.

Use a plain Generic Animator. Humanoid retargeting and automatic support-bone retargeting are unproven and outside this task.

## Q5 — Import, axes and loops

Actual candidate probe is Unity6000.5.8f1, URP17.5.0 and glTFast6.20.0/D3D11, Linear colour space, FourBones skinning and no root motion. The new GLB imports with29,367 triangles,58 assigned bones/bindposes on all ten skinned meshes, finite geometry/indices and maximum weight-sum error1.1921e-7. All nine generated glTF URP shaders are supported and report no shader error. Save/reopen pose checks pass.

B02 settings were `nodeNameMethod:1` (OriginalUnique), `animationMethod:2` (Mecanim), mipmaps1, texturesReadable0, filters9729, anisotropy1, secondaryUV0; instantiation mask−1/layer0/skinUpdateWhenOffscreen1/lightFactor1/sceneObjectCreation2. These are glTFast ScriptedImporter settings, not FBX ModelImporter settings.

Cached glTFast6.20 forces `loopTime=true` on imported Mecanim clips. Actual PlayMode readback confirms imported `idle`, `walk`, `run` are all loops, durations2/1/0.625s,580 Unity scalar curves each. Removing demonstration turn avoids falsely relying on a non-loop flag that GLB does not encode. No non-joint node is animated. Actual probe `.meta` GUID is `4d70365c4e63d4540bc5ad014ef91400`; it is not the game's GUID. Preserve the game-owned GLB `.meta` GUID when integration is separately approved; the prior proposed GUID `21a7210ba3d850b09caae51343d7c144` is not a checked game reservation.

Units are metres. Blender uses Z-up/−Y-front; glTF/Unity is Y-up/+Z-front after glTFast's X mirror. Root has zero translation, identity rotation and unit scale in bind. No baked asset-root translation or heading is intended. Pelvis sway/bob is skeletal motion. Flat-plane ground tolerance is a measured result, not a controller grounding guarantee.

## Q6 — Materials and textures

Required appearance is exactly B02: nine OPAQUE, double-sided, metallic0 materials and thirteen embedded2048² PNG textures; no new material, texture, hair, clothing or appearance change. Complete B02 slot/factor/image-hash metadata is included in the JSON contract and must be compared against the new GLB.

Base-colour RGB decodes sRGB; normal and metallic/roughness maps use linear data. glTF roughness is G, metallic B; URP smoothness is1−roughness. Do not remap a glTF packed map directly as Unity metallic/smoothness-alpha. Normal maps are tangent-space RGB. No required/used glTF extension, compression, AO map, emissive map or transparent hair cards were present in B02. A1024 set is not generated or approved in this motion-only task. Actual target-hardware residency/performance remains unprofiled.

## Q7 — Pivot, contacts and measured tolerances

Pivot remains feet-centred in neutral bind, original lowest POSITION approximately−0.000000496m. Baseline sole sampling uses188 bottom vertices per side and a3mm contact classifier. B02 dense96fps minimum sole heights: idle−0.000706mm, walk−0.449270mm, run−5.870420mm. These must not be called perfect contact.

New saved-skin measurement `build/male-locomotion-fit/contact-001.json` samples at**192Hz** after adding the declared straight controller translation. It tracks the same sole vertex within3mm of the floor in both adjacent samples. Percentiles/RMS are over qualifying individual vertex-pair velocities; maxima include rolling/contact-boundary samples. The separate foot-centre metric is not automatically ground slip, because heel/toe roll moves a centre even with a planted contact patch.

| Dense192Hz steady clip | Minimum sole height | Stable contact P95 | Stable contact RMS | Stable contact maximum |
| --- | ---: | ---: | ---: | ---: |
| idle,0m/s | −0.000706mm | 0.0000158m/s | 0.0000080m/s | 0.0000257m/s |
| walk,1.4m/s | +0.792183mm | 0.004659m/s | 0.027979m/s | 0.704543m/s |
| run,4.0m/s | −0.050254mm | 0.025679m/s | 0.043849m/s | 0.418523m/s |

Run has3,540 and walk11,732 qualifying vertex-pair samples. The maxima must not be hidden by the low P95; neither result is literally zero sliding. This dense source measurement and the following actual Unity24Hz trajectory measurement have different sampling populations and must not be relabelled as the same statistic. No continuous-time or terrain guarantee follows.

Actual Unity002 captures use the **same sole vertices within3mm of the floor in both adjacent frames**, then report the maximum planar world velocity among those pairs. A frame without qualifying pairs reports0 and must not be averaged as a planted-foot success. Reported means below include only contact-bearing frames and average each frame's maximum. This is a24Hz flat-plane measurement, not continuous collision/terrain certification. Initial0.12s/0.16s results remain diagnostic history; final selected demonstration is the one permitted0.08s/0.08s setting comparison, with unchanged phase0, mesh, clips and root trajectory.

| Initial0.12s/0.16s-fade Unity scenario | Minimum sole height | Maximum stable-contact vertex speed |
| --- | ---: | ---: |
| Settled straight4m/s,1.3–<3.0s | +1.000mm | 0.013607m/s |
| Settled walk1.4m/s,8.1–<9.0s | +1.000mm | 0.008057m/s |
| First start including pose fade | −16.519mm | 6.803663m/s |
| First run→idle stop | −29.540mm | 3.010712m/s |
| Restart including pose fade | −16.607mm | 6.806957m/s |
| Right90° scenario at720°/s | +1.000mm | 5.928896m/s |
| Reverse180° scenario at720°/s | +1.000mm | 8.227756m/s |
| Return90° scenario at720°/s | +1.000mm | 4.573676m/s |
| Second run→idle stop | −38.040mm | 3.033829m/s |
| Walk start including fade | −30.621mm | 4.102524m/s |
| Walk→idle stop | −17.831mm | 4.159882m/s |

The single fade-setting correction shortens the sampled defect exposure but does not improve every peak:

| Scenario | Initial minimum sole | Final0.08s/0.08s minimum sole | Frames below−1mm, initial→final | Final maximum contact speed |
| --- | ---: | ---: | ---: | ---: |
| First start | −16.519mm | −17.865mm | 2→1 | 8.196471m/s |
| First run→idle stop | −29.540mm | −9.041mm | 3→1 | 2.134770m/s |
| Restart | −16.607mm | −17.952mm | 2→1 | 8.200893m/s |
| Second run→idle stop | −38.040mm | −29.471mm | 3→1 | 4.168762m/s |
| Walk start | −30.621mm | −25.084mm | 2→1 | 5.455765m/s |
| Walk→idle stop | −17.831mm | −35.202mm | 3→1 | 6.070451m/s |

These are sampled frame counts at24Hz, not a claim of continuous defect duration. The final start and walk-stop peaks worsen while the number of below-floor samples falls. Turn metrics and settled loop fit are unchanged. **Steady loops are well fitted; pose crossfades still do not maintain the floor plane, and rapid pivots do not plant feet.** A technically passing capture must not be described as clean start/stop/contact. No zero-sliding claim and no further tuning.

## Q8 — Licence and ready notice

Snow v4 derivative remains **CC BY4.0**, with source <https://studio.blender.org/characters/snow/v4/> and licence <https://creativecommons.org/licenses/by/4.0/>. Keep the following notice with the model source, archive and eventual game distribution:

```text
A03 / Willow Creek male character (modified Snow v4 derivative)
Snow Rig (CC) Blender Foundation | studio.blender.org
Source: https://studio.blender.org/characters/snow/v4/
Licence: Creative Commons Attribution 4.0 International (CC BY 4.0)
https://creativecommons.org/licenses/by/4.0/

Modified for Willow Creek: approved A03 geometry, identity, hair and materials;
static mesh simplification; B02 derived58-joint skeleton/local skin weights;
original repository-authored locomotion clips adapted for the documented
controller speed. No endorsement by Blender Foundation is implied.
Source CloudRig/UI code is not included or executed.
Preserve this notice with distributed assets and the game.
```

New motion is authored within the repository; no downloaded animation, paid service, purchase or new external mesh is authorized or needed. This candidate returns to B02 and does **not** include rejected B03/B04 elbow changes.

## Q9 — Versioning and replacement

This is **not a semantic drop-in for B02 animation**: clip timing/speed/contact may change and `turn` is intentionally removed. The unchanged asset ID, mesh and skeleton do not make the altered motion contract interchangeable. Pin the new version and hashes only after owner visual approval and Claude's separate integration work.

Bone/rest/bind names and paths,58-joint count, axes/units/pivot, mesh/material names, weights and appearance must remain unchanged. Clip-set, clip-duration, designed-speed, loop/phase or transition changes are contract changes even without topology changes. Keep existing game-owned `.meta` identity; no game repository modifications are made here.

## Q10 — Transitions and stopping

Required proof: actual Unity idle, straight4m/s movement at1×, idle→run, run→idle and rapid heading changes, including50°/16m and close views. The probe must use fixed4m/s root translation while movement is commanded and720°/s heading, not an eased substitute controller.

B02's five0.2s programmatic crossfades only established finite target states. The initial new trajectory used0.12s start/0.16s stop pose fades. The **final demonstrated setting is0.08s start/0.08s stop**, destination normalized time0, with immediate root-speed commands and up to720°/s root heading; `turn` is never played. Each240-frame actual PlayMode capture executes without reported runtime error. This proves the requested scenarios ran, not that their contacts are clean. The shorter setting reduces below-floor sample counts to one per tested start/stop, but some depth/velocity peaks worsen. Use it only as the demonstrated review setting, not a universal recommended crossfade policy. Direct run→idle **does not have a certified clean settle**. No braking clip, foot locking, runtime ground correction, motion matching or generic Animator system is delivered.

## Q11 — Decision, remaining limits and what ran

Recommendation is **technical GO for steady4m/s motion; NO-GO for unqualified integration or clean-contact transition claims**. Numerical steady-state fit improved strongly at the target speed, and the full-body run is credible enough for normal-camera owner review. Starts/stops and foot-locked rapid turning retain measured defects. The owner must decide whether those brief distant-camera tradeoffs are acceptable for First Playable; this is not automatic integration approval. B02's elbow limitations are accepted for the normal distant camera only and remain visible in close-up. Knee/seam/finger limitations, terrain, Humanoid retargeting, facial animation, wardrobe and target-platform performance remain known/unverified areas. No larger IK/grounding or animation architecture is proposed or built in this delivery.

Actual executed records read for this contract: saved `delivery-001/asset-report.json`; fresh `validation-003/report.json` (B02/saved source/GLB preservation and Blender GLB roundtrip); `contact-001.json` (saved skinned sole at192Hz plus intended straight translation); `unity-002/evidence/unity-animation-report.json` (URP import, rendering and reopen); initial `unity-002/motion-evidence/motion-report.json` and final `unity-002/motion-correction-001/motion-report.json` with commands (two actual240-frame PlayMode trajectories, one fade-only comparison). Validation's maximum sampled skin point-cloud roundtrip error is7.974µm, original idle GLB TRS sample error at96Hz is≤9.537e-7 component units. This is not exhaustive continuous-time intersection validation.

The motion probe uses deterministic manual `Animator.Update` at24Hz inside actual PlayMode with automatic Animator updates disabled. It is not OS input, the real game controller, Neighborhood lighting or gameplay/physics integration. Full and50°/16m cameras follow root translation with fixed offsets,40° vertical FOV and a1m ground grid. Final footage, archive fingerprints and download verification are supplied by the accompanying quality/artifact records. Owner approval remains separate.

No life-sim-game change, controller change, new character, arm correction, Phase C, merge or automatic integration. Stop after the candidate delivery for owner approval.
