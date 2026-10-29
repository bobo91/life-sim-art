# A03 Phase B01 - bounded motion proof

**Integration recommendation: NO-GO for the current proof rig/clips as the playable character. Technical skin/export/Unity playback proof: GO.** A03's approved visual identity and accepted 29,367 triangles stand. No A04, new base, merge or game change. This gate concerns deformation and motion quality, not the face.

## Actual movement evidence

[MP4 - all four clips, 24fps](https://github.com/bobo91/life-sim-art/releases/download/male-neutral-b01-v0.1/a03-b01-unity-motion.mp4) | [Small animated preview](../../../evidence/male-neutral-b01/previews/motion-preview.gif) | [Four phases per clip](../../../evidence/male-neutral-b01/previews/motion-four-clips.png) | [Unity joints/hands](../../../evidence/male-neutral-b01/previews/joint-closeups.png) | [16m camera](../../../evidence/male-neutral-b01/previews/game16m-four-clips.png).

[Actual PlayMode run](../../../evidence/male-neutral-b01/previews/playmode/run_playmode.png) | [Blender elbow90](../../../evidence/male-neutral-b01/previews/blender-stress/stress_elbow90.png) | [Wrist45/fingers60](../../../evidence/male-neutral-b01/previews/blender-stress/stress_wrist45_fingers60.png) | [Knee90](../../../evidence/male-neutral-b01/previews/blender-stress/stress_knee90.png).

The MP4 contains all 126 actual Unity PNG frames at native24fps: idle48, walk24, run18, turn36, total5.25s. It uses reproducible direct imported-clip sampling in an art-only URP scene, not synthesized movement or static turntable shots. The separate PlayMode smoke proves real Animator time advancement and skin deformation. The GIF samples every second native frame. Sheets only resize/layout/add labels; no pose/image retouch. The video was reopened and four frames decoded, image-region mean error below0.91/255. Clips are concatenated with cuts, not a transition demo. Turn intentionally ends90degrees from its start and is not a loop.

## What can be reused from Snow

The actual Snow v4 file has1,494 runtime-rig bones,290deform bones,1,601constraints and1,291drivers. The ten visible source parts reference271deform groups; retaining their ancestors gives569bones and their B-Bones total1,101segments. No invalid driver or unresolved target was found in this audit. The source is effectively T/rest pose; the major FK chains used here match within0.000000239m and0degrees.

**Direct native Snow-rig reuse in Unity: NO-GO.** Its B-Bone curvature/distributed twist, dual-quaternion skinning, corrective smoothing, lattice helpers and facial shape-key rig do not survive a plain glTF linear-skin export. Deleting control bones alone also breaks the intended parent hierarchy. Source actions are pose libraries, not ready idle/walk/run/turn cycles. Embedded CloudRig/UI code was disabled, never executed or delivered.

A bounded **52-joint data-only derivative** reuses source rest landmarks and skin weights, with an explicit new parent hierarchy. Split arm/leg groups are merged,30finger joints retained, facial groups collapsed to Head while preserving the neck/chest blend. Eyes/brows/hair follow Head. The source neck is part of the head mesh, so it is not rigidly parented as a whole. This proves partial data reuse; it does not claim preservation of Snow's full rig quality.

The exact A01 evaluation/normalization was recovered and measured, including source presentation controls. Weights come from evaluated source surfaces, not raw source vertex indices. A03 high provides the same-part correspondence to simplified body/clothes/shoes; nearest-triangle barycentric transfer is used there. All weights normalize to at most4influences, with **zero discarded mapped weight mass** in this result. Worst transfer distance is3.189mm on simplified body. There are no unweighted delivered vertices. Bind-pose skin evaluation differs from raw A03 by at most0.000000247m. All ten raw A03 position/topology hashes remain unchanged; its materials/UVs/palette are retained. Original Snow and A01/A02/A03 sources/evidence are not overwritten.

## Actual checks

| Check | Result |
| --- | --- |
| Saved Blender source reopened,52bones, finite normalized weights | PASS |
| Independent animated GLB reimport,5poses per clip | PASS; maximum4.414e-6m bidirectional nearest vertex error |
| Fresh repeated build | Identical GLB bytes and geometry/weight/pose report; blend container bytes not compared |
| Unity6000.5.8f1 / URP17.5 / glTFast6.20 / D3D11 |10skinned meshes,52bindposes,29,367triangles,9materials; PASS |
| Unity weights/bind matrices/indices/normals/shaders | PASS; max weight-sum error1.19e-7, all9URP shaders supported/error-free |
| Actual clip samples, render, scene save/reopen | PASS; no importer diagnostics; same sampled pose after reopen |
| Actual PlayMode Animator, four simple states | PASS; time advances, finite skin, measured motion for all4clips |
| Rendered deformation inspection | Actual elbow/knee/wrist limitations below; not production approved |

Blender uses CPU Cycles12samples for the additional stress views. Unity uses matched key1.5/fill.5/ambient.4, postFX off. The16m art proxy is50degree elevation/40degree vertical FOV/1280x720. It is not Neighborhood, actual game lighting or a game integration test. No GPU Blender or Linux execution claimed. Local GPU inventory: AMD Radeon RX9070XT plus integrated AMD graphics; Unity actually used D3D11.

Source and final GLB remain unchanged during import/runtime checks. A separate Unity Search indexing ArgumentOutOfRangeException appeared at PlayMode startup; the isolated probe assertions pass, so the whole editor log is not claimed error-free. Earlier setup/capture/interpolation failures and the intentionally aborted intermediate Unity002 are retained in execution.json and intermediate/. No further full test sweep was performed after final success.

## Actual problems and integration gate

- **Visible elbow volume loss and a sharp inner crease**, already visible in the run close-up; stronger at the90degree stress pose. A52bone linear adapter does not retain the source B-Bone/DQ/corrective behavior.
- **Bent knee/trouser pinching and seam stretch**, and angular wrist/finger contours under45/60degree stress. No gross exploding mesh or new open tear was found in reviewed views. These renders are not an exhaustive self-intersection certificate. The tested shoulder range is ordinary locomotion/T-pose, not overhead reach or arbitrary extreme poses.
- **Turn has sliding stance feet**: sampled sole-bottom contact speed reaches0.207m/s while yaw changes. It is a visual90degree proof, not a grounded pivot/turn-in-place animation suitable for shipping.
- Walk/run are in-place. Recipe stance estimates are about0.552m/s and1.533m/s respectively. They have not been matched to the game's controller. Walk boundary sampling retains up to0.045m/s residual at the recipe speed; a controller mismatch would cause more sliding. Sole penetration in sampled poses is below0.001mm, which is a plane diagnostic, not collision/ground-slope behavior.
- Idle/walk/run start/end sampled surfaces close exactly in Unity; turn should not close. Loop flags, blends, left/right turns, stopping, ground adaptation and root-motion/controller behavior are not certified. Humanoid Avatar/retargeting, performance/build/population tests and facial animation are not tested. The actual runtime smoke uses a small Generic four-state Animator, not gameplay architecture.

At16m the silhouette/palette remains legible and close-up joint problems are much less visible, but the playable motion gate should not hide them behind distance. **Do not integrate this review artifact as the finished player character.**

## Limited next step, before any large rebuild

Keep the accepted A03 mesh/face and this measured52joint baseline. Recommend one bounded corrective pass confined to elbow/knee/wrist weights or a very small number of local support joints, plus foot-locking/stride timing for these same four clips. Check the existing near/16m cameras and the same stress poses. Do not restore the entire CloudRig or reconstruct the face. If that bounded pass cannot remove the visible collapse, stop and propose targeted joint retopology/correctives for approval; no automatic general-system work. This corrective pass is a recommendation, not performed here.

## Future clothes and variants

The delivered skin is the source's visible masked body, not a complete hidden torso/legs. New garments need appropriate covered body surfaces/coverage masks, the same bind frame and joint weighting; independent garment transfer can create sleeve/neck/hip gaps. Optimization changed body/clothes/shoe topology; old source weight indices cannot be copied. Body/identity variants will need bind-landmark and weight/key transport validation. Facial expression/blink keys would need a separate identity-preserving rebase; original Snow correctives cannot simply be attached to A03. This proof builds no wardrobe, modular NPC system, facial library or generic animator framework.

## Licensing, source and delivery

Source: [Blender Studio Snow v4](https://studio.blender.org/characters/snow/v4/), with required credit **Snow Rig (CC) Blender Foundation | studio.blender.org**. Source ReadMe links [CC BY4.0](https://creativecommons.org/licenses/by/4.0/), which permits commercial sharing/adaptation with attribution, licence link and modification notice. This is an attributed derivative. The four proof motions are original repository-authored deterministic clips, not purchased/downloaded animations or mocap. The asset/motion/media derivative retains CC BY4.0 attribution; no source GPL rig/UI code is included. External spend0SEK.

[Import contract](B01_IMPORT_CONTRACT.json) | [Commands](B01_REPRODUCE.md) | [Provenance](../../../evidence/male-neutral-b01/provenance.json) | [Download record](../../../evidence/male-neutral-b01/artifact.json).

No game-repository changes, purchases, external service, automatic merge or further model work. PR39 remains draft. Stop for owner review of the motion/deformation gate.
