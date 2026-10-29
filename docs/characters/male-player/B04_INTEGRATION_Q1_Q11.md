# B04 integration answers — art issue #40, Q1–Q11

Measured 2026-10-29 for [art #40](https://github.com/bobo91/life-sim-art/issues/40), supporting GAME-047. This is an information contract, **not integration approval**. **B04 failed its Blender visual gate and is NO-GO. No B04 GLB exists, and no B04 Unity import or verification was performed.** Values below explicitly identify the preserved B02 GLB; they must not be relabelled as a verified B04 release.

## Q1 — Release, hashes and manifest

There is **no integration-approved release**. The existing review baseline is release [`male-neutral-b02-v0.2`](https://github.com/bobo91/life-sim-art/releases/tag/male-neutral-b02-v0.2):

| Item | Exact value |
| --- | --- |
| assetId | `chr_player_male_poc_001` |
| ZIP | `male-neutral-b02-v0.2-review.zip` |
| ZIP SHA256 | `40d26dd62cb50bbdc6fcffd8ce597f80f2c7f59dfd900387206c65efeff69c31` |
| GLB SHA256 | `4faa2eec33d131b7fcdc4b41720e5abbd16e03eab594bf764f3d7ae041de3d33` |
| Skeleton / clips / materials | 58 joints / `idle`, `walk`, `run`, `turn` / 9 materials |
| Neutral Unity-space dimensions | 1.738315 × 1.749405 × 0.306273 m; width includes extended arms |
| Neutral bounds, min / max | `(-0.8691574, -0.000000496, -0.1531364)` / `(0.8691574, 1.7494049, 0.1531364)` m |
| Licence | Modified Snow v4, CC BY 4.0; notice in Q8 |

The committed audit output `evidence/male-neutral-b04/integration-baseline/contract-manifest-baseline.json` includes the full measured bounds, 58 names/parents/paths, clips, materials and licence with `integrationApproved:false`. It is a baseline information manifest, not a shipping artefact. The rejected local B04 trial changes the body from 2,748 to 3,126 vertices (**+378**) and 5,460 to 6,216 triangles (**+756**); total character triangles rise from 29,367 to **30,123**. There is no B04 GLB hash or replacement integration manifest.

The review-only rejected [B04 proof](https://github.com/bobo91/life-sim-art/releases/tag/male-neutral-b04-v0.4) is published as `male-neutral-b04-v0.4-rejected-proof.zip`, SHA256 `774a74d5ab6fae87d452208028b381b78b71d56c9fc4ed62d9a2833c03b9118b`. Download verification passed for all118 archive entries (117 payload hashes plus the manifest), all75 native image fingerprints and exact frozen candidate bytes. This is not a playable asset or a replacement for the B02 GLB. B04 stops at this failed gate.

## Q2 — Locomotion speed, cadence, phase and loops

These are B02 in-place clips: the asset root has **zero actual locomotion translation**. The nonzero design speeds below are inferred from the source foot-contact recipe; they are neither measured root velocity nor measured gameplay/controller movement:

| Clip | Duration | Stance excursion / duration | Inferred design speed | Effective same-foot stride | Steps/min | Rate needed at fixed 4 m/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| walk | 1.000 s | 0.320 m / 0.580 s | 0.551724 m/s | 0.551724 m | 120 | 7.250× |
| run | 0.750 s | 0.460 m / 0.300 s | 1.533333 m/s | 1.150000 m | 160 | 2.608696× |

A 0.320/0.460 m stance excursion is **not** the full stride. At 4 m/s the implied cadences would be 870/417 steps/min, so arbitrary playback scaling is not an approved solution. A visually safe playback range is **unmeasured**. The fixed-speed controller mismatch is independent of the elbow issue and remains an integration blocker. B04 does not author replacement clips or change gameplay speeds.

The source recipe starts left-foot landing at normalized time 0 and right-foot landing at 0.5 for both gaits. Nominal phase is shared, but stance fractions differ (0.58 walk / 0.40 run). Pop-free phase-preserving blending has not been verified. The existing probe starts each destination clip at time 0 rather than transferring phase.

Raw GLB first/last TRS values match exactly for `idle`, `walk`, `run`, including all six support joints. `turn` does not match, as expected for a quarter-turn. Endpoint equality does not prove continuous velocity or absence of contact pops. See Q5: the actual importer incorrectly-for-this-use loops **all** four Mecanim clips by default.

## Q3 — Turn semantics and controller ownership

`turn` is 1.500 s, left 90°: measured Hips world-yaw delta after glTFast's handedness conversion is approximately −89.999995° about Unity Y (+Z faces toward −X). Rotation is skeletal **Hips** rotation, not GameObject root motion. Neither `CHR_PlayerMale_A01` nor `A03_B01_Rig` has animation channels; asset position, scale and heading stay fixed.

Hips translation changes from approximately `(0.000000406, 0.8510193, -0.0411593)` to `(-0.0411593, 0.8510194, -0.000000381)` in raw glTF space while pivoting around foot contact. It therefore has a small pelvic orbit, not a root translation to apply to the controller. The clip's initial pelvis is 4 mm higher than `idle`; its final visual heading differs by 90°. It is not an exact idle-to-idle settle or a loop.

No right-turn, 180° or short-turn variant is supplied or verified. **Recommendation: omit this clip from gameplay turning**, keep controller-owned heading and `applyRootMotion=false`. The game's 720°/s turn rate would take 0.125 s for 90°, unlike this 1.5 s demonstration. B04 does not change either system.

## Q4 — Hierarchy, all 58 joints and support baking

Actual root hierarchy is:

```text
CHR_PlayerMale_A01
  A03_B01_Rig
    Hips [joint tree below]
  M01_body
  M01_eyebrows
  M01_eyes
  M01_hair_base
  M01_head
  M01_pants
  M01_shirt
  M01_shoes_base
  M01_shoes_bottom
  M01_shoes_parts
```

The ten meshes are **siblings** of the armature. The full joint hierarchy below uses `.L/.R` for two separate, identically parented branches; each finger chain is separate:

```text
Hips
  Spine > Chest > UpperChest
    Neck > Head
    Shoulder.L/.R > UpperArm.L/.R
      LowerArm.L/.R
        Hand.L/.R
          Thumb1.L/.R > Thumb2.L/.R > Thumb3.L/.R
          Index1.L/.R > Index2.L/.R > Index3.L/.R
          Middle1.L/.R > Middle2.L/.R > Middle3.L/.R
          Ring1.L/.R > Ring2.L/.R > Ring3.L/.R
          Pinky1.L/.R > Pinky2.L/.R > Pinky3.L/.R
        B02_Wrist.L/.R
      B02_Elbow.L/.R
  UpperLeg.L/.R
    LowerLeg.L/.R > Foot.L/.R > Toes.L/.R
    B02_Knee.L/.R
```

Machine-readable `skeleton.json` and the baseline manifest enumerate all 58 individual names, parents and paths without abbreviation. Root path is `CHR_PlayerMale_A01/A03_B01_Rig/Hips`. Names and paths are a compatibility boundary, not an invitation to rename the old A01/B01 labels. Preserve mesh datablock names too: body is `GEO-snow-body.002`; glTFast uses subasset names.

Each of the four exported clips has **174 channels = 58 × translation/rotation/scale**. All six `B02_Elbow.L/R`, `B02_Knee.L/R`, `B02_Wrist.L/R` have all three channels in every clip, including idle and turn. These are ordinary weighted joints with baked support motion, not a runtime CloudRig. New/retargeted animation requires the same support-joint treatment; a Humanoid avatar alone is not proven to drive it.

## Q5 — Actual glTFast importer contract and fixed GUID proposal

Measured baseline: Unity 6 URP, glTFast 6.20, local Generic-style node animation using an ordinary Animator; no Humanoid Avatar was built. This is a glTFast `ScriptedImporter`, not an FBX `ModelImporter` setting.

Actual importer settings: `nodeNameMethod:1` (OriginalUnique), `animationMethod:2` (Mecanim), `generateMipMaps:1`, `texturesReadable:0`, default min/mag filter 9729, anisotropic level 1; `generateSecondaryUVSet:0`. Instantiation settings are mask −1, layer 0, `skinUpdateWhenOffscreen:1`, light factor 1, `sceneObjectCreation:2`. The probe sets Animator `applyRootMotion=false`, FourBones skin quality and Linear colour space. Imported clip names are exactly `idle`, `run`, `turn`, `walk` (ordering is irrelevant).

**New concrete finding:** cached glTFast 6.20 `Editor/Scripts/GltfImporter.cs` lines 227–232 sets `AnimationClipSettings.loopTime=true` on every Mecanim clip; `Runtime/Scripts/Animations/AnimationModuleProcessor.cs` also initializes `wrapMode=Loop`. Thus **all four imported baseline clips loop**, including turn. Earlier tests did not assert this flag. Game integration must either explicitly disable turn looping or omit turn; the source GLB does not encode a Unity loop flag. Idle/walk/run are intended to loop.

The audit supplies `chr_player_male_poc_001.glb.meta.template` copied from the real B02 import, with proposed stable GUID **`21a7210ba3d850b09caae51343d7c144`**. ScriptedImporter script GUID is `715df9372183c47e389bb6e19fbc3b52`. The original probe GUID `80b86487468d90940af7ec3e58fdfa73` is not a game contract. The proposal has not been checked for game GUID collisions or adopted there; Claude should retain any existing game-owned GUID or adopt a single checked GUID, then preserve it. External material remaps are still empty in this template.

Scale is metres; root translation zero, rotation identity, scale one. glTFast converts glTF handedness by mirroring X, yielding Unity Y-up/+Z-front in the render probe. Neutral height and bounds are measured in Q1. No accumulated root drift appears in these in-place clips; small periodic pelvis sway/bob is intentional. Formal game-controller alignment and terrain contact remain unverified.

## Q6 — Materials, texture slots and 1024 option

Raw GLB contains 9 materials and 13 embedded PNG images, all **2048×2048**. Every material is **OPAQUE, double-sided, metallic factor 0**. No required/used glTF extension, Draco, meshopt, quantization, alpha hair cards, separate AO map or emissive map is present. Exact per-image hashes, factors, mesh users and sampler settings are in `material-spec.json`.

| Material | Base colour | Normal (scale 0.5 if present) | Metallic/roughness | Roughness factor |
| --- | --- | --- | --- | ---: |
| M01_skin | skin_diffuse_atlas | — | — | 0.72 |
| M01_hair | solid linear RGB (0.022, 0.011, 0.006), shared by brows | — | — | 0.86 |
| M01_eyes | eyes_diffuse | eyes_normal | — | 0.30 |
| M01_skin_darker | skin_darker_diffuse_atlas | — | — | 0.72 |
| M01_skin_upper_lip | skin_upper_lip_diffuse_atlas | — | — | 0.67 |
| M01_skin_lower_lip | skin_lower_lip_diffuse_atlas | — | — | 0.67 |
| M01_pants | pants_tinted_diffuse | pants_normal | pants_roughness | 1.00 |
| M01_shirt | solid linear RGB (0.045, 0.090, 0.060) | shirt_normal | — | 0.84 |
| M01_canvas_shoes | shoes_diffuse | shoes_normal | shoes_roughness | 1.00 |

Base-colour RGB uses sRGB decoding (alpha linear); normal and metallic/roughness maps are linear/data. glTF packs roughness in **G**, metallic in **B**; multiply by factors. URP Lit smoothness is `1−roughness`; do not feed this texture directly as a Unity metallic/smoothness-alpha map. Normal maps are tangent-space RGB. Exact float values in JSON are authoritative over table rounding. All base-colour factors are white except hair/shirt; emissive factors are zero.

A 1024 texture variant is feasible by deliberate resampling or import max-size, but **has not been generated, imported or visually approved**. It is outside B04's unchanged-material requirement. Halving dimensions quarters texel count; actual GPU formats/residency and quality savings are unprofiled. No claim of a ready 1024 package.

## Q7 — Pivot, ground plane and measured tolerance

Root pivot is world origin at the neutral sole plane; neutral lowest POSITION is approximately −0.000000496 m (numeric noise). No root-motion drift is baked. Existing `evidence/male-neutral-b02/paired-contact.json` measures 188 bottom-sole vertices per side, with 3 mm contact classification. It is not a terrain/physics test.

| Clip | Minimum sampled sole height at 24 fps | Minimum at dense 96 fps |
| --- | ---: | ---: |
| idle | −0.000538 mm | −0.000706 mm |
| walk | −0.000553 mm | −0.449270 mm |
| run | −0.000567 mm | **−5.870420 mm** |
| turn | +0.049475 mm | +0.024389 mm |

Therefore **do not confirm perfect foot-plane contact for every clip**. The old no-sampled-penetration statement applies to turn, not all clips. The 96 fps run penetration is a real measured limitation; no gameplay-tolerable threshold has been agreed. Turn's maximum sampled planted-foot sole-centre speed improved from approximately 0.206781 m/s (B01) to 0.000000682 m/s (B02) at 24 fps; dense 96 fps residual is 0.008511 m/s. No ground-collision guarantee follows from those numbers. The separate [B04 preservation verifier](../../../evidence/male-neutral-b04/preservation.json) now passes: all evaluated shoe-vertex positions over all four clips at24/96fps match B02 exactly (1,559,910 vertex samples per version, maximum displacement0m), and original action curves are exact. This proves preservation in Blender, not B04 export or Unity behaviour.

## Q8 — Ready attribution notice

Supply `NOTICE-ASSET.txt` next to the package/executable and preserve it with distributed assets. The ready text is:

```text
A03 / Willow Creek male character (modified Snow v4 derivative)
Snow Rig (CC) Blender Foundation | studio.blender.org
Source: https://studio.blender.org/characters/snow/v4/
Licence: Creative Commons Attribution 4.0 International (CC BY 4.0)
https://creativecommons.org/licenses/by/4.0/

Modified for Willow Creek: approved A03 identity/material/hair edits,
static mesh simplification, a derived 58-joint skeleton, mapped/local
skin weights, original repository-authored motion clips and local
elbow-topology trial as documented in the pinned release. No endorsement
by Blender Foundation is implied. Source CloudRig/UI code is not included
or executed. Preserve this notice with the asset and distributed game.
```

Existing source/provenance records remain authoritative. The exported mesh and original motion are distinct from upstream rig/UI source code; the latter is not shipped here. No external animation service or paid content was used in this pass.

## Q9 — Replacement compatibility

Treat bone names/paths/parenting/bind poses, clip names/durations/phase/root-motion/loop semantics, axes/units/pivot and material/mesh-node/subasset names or texture channel semantics as compatibility boundaries. Changes need a new contract/version and integration review. Local elbow geometry can be a drop-in only if these boundaries remain identical and fresh import confirms the result. Vertex indices/order can change, so any external vertex-index bindings or cached geometry/weights require rebuilding. Never assume a matching assetId alone proves compatibility. Keep the adopted Unity `.meta` GUID through replacements.

## Q10 — Crossfades and stopping

The actual B02 probe called `CrossFadeInFixedTime(next, 0.2f, 0, 0)` through **idle → walk → run → walk → idle → turn**. It reached finite target states in PlayMode. This is an empirical 0.2 s starting point, not a validated Animator exit-time policy, phase matcher or proof of contact-perfect transitions. The probe uses programmatic transitions; no authored exit-time settings were certified.

**Direct run → idle has not been tested.** There is no separate settle/stop clip. A clean stop under the actual fixed-speed controller is not confirmed. No new transition or braking system is included in B04. Recommend retaining immediate controller ownership and visually checking its existing stop behaviour rather than waiting for a loop boundary; gameplay implementation remains Claude's responsibility. Omit demonstration turn from gameplay as noted in Q3/Q5.

## Q11 — Remaining integration blockers and limits

Current status: **B04 failed the Blender gate; NO-GO for gameplay integration.** No GLB export or Unity follow-through was performed. Independently of that visual failure, the baseline also has fixed 4 m/s gait mismatch, unverified direct run→idle stopping, the turn-loop importer behaviour or dense run foot penetration. These remain documented limits, not authorization for another corrective iteration, animation change or game-code change. No automatic continuation after B04.

Other limits: high-angle 50°/16 m evidence is an art-side camera proxy, not a run inside the real Neighborhood scene; Humanoid retargeting, new support-driven clips, clothing/face animation and production performance are unproven. The baseline has 10 skinned mesh objects, 13 primitives/submeshes, 9 double-sided materials and 13 2K images; FPS, GPU skinning cost, target-hardware memory and actual game lighting have not been profiled. Remaining knee/finger angularity must not be hidden by a passing technical test. B04's separate saved-file preservation/replay checks pass, but the visual elbow gate fails. See its quality report; no B04 Unity claim follows.

## What actually ran for this answer

Read-only inspection of preserved B02 GLB bytes/accessors/channels/materials/images, existing Blender contact evidence, B02 Unity `.meta` and capture source, and cached glTFast 6.20 importer/runtime source. `scripts/inspect_male_b04_contract.py` writes the audit to a fresh output directory; it does not launch Unity or change meshes. No new game test, Unity session, speed controller test, 1024 export, model production, issue comment or game-repository change was performed for this contract audit. B04 model/testing work and preservation verification are reported separately; the failed Blender gate prevented B04 export and Unity testing.
