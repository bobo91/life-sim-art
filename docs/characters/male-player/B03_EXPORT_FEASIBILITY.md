# B03 conditional morph export plan - inspected, not executed

**Final B03 visual gate: NO-GO. The plan below was not implemented or tested.**

This is a short read-only plan for the visual gate. No B03 GLB export, Unity import or activation test has been run by this audit. Proceed only if the isolated Blender corrective is clearly better; otherwise stop and propose local topology as requested.

## Smallest existing-pipeline path

Keep the current58-bone animation and two relative keys on M01_body (L/R elbow; unchanged Basis). Bake each side's weight from its actual hinge-direction bend angle, including the rest-direction offset. Use the corrective author's canonical angle function; a relative quaternion angle alone would also count twist and is not labelled physical flexion.

For each existing clip idle/walk/run/turn, key BOTH corrective weights at every original frame, including explicitzero weights in straight/idle phases. Store each morph action under a distinct datablock name such as B03_Morph_run. Put its single strip on the shape-key datablock's NLA track named exactly run, matching the armature's single-strip track. Before export clear active actions on both armature and Key datablock, leaving tracks as the action source; active+NLA duplicates can otherwise get separate suffixed exports. Existing muted tracks are collected by ACTIONS mode; strip.mute must beFalse.

The installed Blender4.5.14 exporter supports this without switching architecture to full NLA_TRACKS:

```python
export_animation_mode='ACTIONS',
export_merge_animation='NLA_TRACK',
export_anim_single_armature=False,
export_animations=True,
export_morph=True,
export_morph_animation=True,
export_morph_normal=True,
export_morph_tangent=False,
export_morph_reset_sk_data=True,
export_apply=False,
export_force_sampling=True,
export_anim_slide_to_zero=True,
export_frame_range=False,
export_skins=True,
export_influence_nb=4,
```

Preserve the other proven B02 export flags. With export_anim_single_armature=False, only associated NLA actions are collected; an unrelated stored diagnostic OBJECT action cannot silently become a fifth clip. Optional export_optimize_animation_size=False makes this small proof fully sampled; the installed morph optimizer normally keeps constant channels as first+last keys rather than dropping them. Verify channels in the actual GLB instead of relying on either setting.

## What installed source actually shows

- io_scene_gltf2/__init__.py defines the flags above. ApplyModifiers explicitly prevents shape-key export, so keepFalse.
- blender/exp/animation/action.py collects armature and shape-key single-strip tracks, retaining each track name. With merge NLA_TRACK it groups by the shared name.
- blender/exp/animation/anim_utils.py merge_tracks_perform combines channels/samplers with the same track name; boneTRS and M01_body weights are different targets and can coexist.
- Cached glTFast6.20 Runtime/Scripts/Animations/AnimationModuleProcessor.cs creates SkinnedMeshRenderer curves named blendShape.<targetName> for glTF weights channels.
- Runtime/Scripts/MorphTargetsGenerator.cs uses mesh.AddBlendShapeFrame(name,1f,...). Therefore imported full morph weight is1, not100. Do not blindly use the familiar Unity100 assumption; inspect GetBlendShapeFrameWeight in the actual imported mesh.

These are installed-source observations, not a tested B03 result.

## Limited conditional verification

1. Parse the actual GLB: exactly the original four clip names/durations, each with boneTRS and an M01_body weights channel; two named targets and no new bone/triangle/material. Assert unchanged neutral positions and locality of target deltas.
2. Independent Blender reimport: compare corrected pose to authoring at run25%,90flexion and nearstraight; inspect both sides. Forceweights0 and confirm Basis/neutral equality. Keep B02 turn/foot curves unchanged.
3. In the art-only Unity probe inspect body blendShapeCount/names/frameweights and animation bindings. Sample each clip then inspect GetBlendShapeWeight plus BakeMesh to prove activation is real.
4. Explicit run-to-nearstraight/idle return test: weight returns0 or the canonical small value for actualbend; surface returns to uncorrected shape where it should. Test both arms, actual URP images under matched camera/light, and the existing PlayMode Animator.

No new runtime corrective architecture is needed for the supplied clips. The limitation must be stated: angle weights are baked from those clips, so arbitrary retargeted/new animation must rebake the same two channels. This is not a general live procedural response to all possible elbow poses. If the merge/import fails in the bounded trial, report it rather than building a general replacement system.
