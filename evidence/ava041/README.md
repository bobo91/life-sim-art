# Ava Morgan static visual candidate — ART-041

**Appearance approval pending. Stop before rigging/animation.**

[Turnaround](previews/turnaround.png) · [face](previews/face_three_quarter.png) ·
[Ava/A03 at the same scale](previews/ava_a03_same_scale.png) ·
[normal game camera](previews/game-camera-pair.png) ·
[Juniper daylight full](previews/cafe_daylight_full.png) / [face](previews/cafe_daylight_face.png).

The final Windows build generated **12 actual Blender renders** in **106.015 s**:
Blender 4.5.14 LTS `62c1db4208e8`, Python 3.11.15, Cycles **CPU**, six render
threads, 40 samples, denoising, AgX. System Python 3.14.6 / Pillow 12.3.0 made
the labelled evidence layout. HIP devices were enumerated, including a Radeon
RX 9070 XT; GPU rendering was not tested. The device probe's device lists are
not a CUDA/OptiX availability or acceleration claim.

Measured candidate: **28,991 triangles / nine mesh groups / nine materials /
12 exported material primitives / zero image textures**; 0.671925 × 1.692000 ×
0.288007 m exported XYZ. Zero rigs, skins, actions, animations or embedded
executable text. The static GLB is **760,316 bytes**.

- [Asset metrics and exact generator/config hashes](runtime/asset-report.json)
- [Camera/render settings and image hashes](runtime/render-metadata.json)
- [Actual environment probe](runtime/environment.json)
- [Source reopen, independent GLB and fresh reimport: 67 checks passed / 0 failed](runtime/validation.json)
- [Two separate processes: byte-identical GLB and frozen source/config checks](runtime/reproduction.json)
- [Static visual roundtrip](runtime/roundtrip.json): front mean RGB difference
  0.0001141; face three-quarter 0.0001983, against the 0.002 limit. These are
  Blender-loaded PNG float RGB values. Reimport images are retained alongside
  the report. No claim of exact image identity or Unity compatibility follows.
- [Generated file SHA256 manifest](runtime/manifest.json)
- [Preview source hashes and transformations](preview-manifest.json)

GLB SHA256: `35dcb5549c577305b72553595cd361cf90ca5efdb741b815cbb0d5c02c153f45`.

The same A03 source hash was verified before and after comparison. It is a
separate attributed Snow v4 derivative: **Snow Rig (CC) Blender Foundation |
studio.blender.org**, [source](https://studio.blender.org/characters/snow/v4/),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Ava is original
procedural geometry; A03 is not its mesh base.

Read the [critical quality review](../../docs/characters/ava-morgan/ART041_QUALITY_REVIEW.md),
[preflight/contracts](../../docs/characters/ava-morgan/ART041_PREFLIGHT.md),
[provenance](../../docs/characters/ava-morgan/ART041_PROVENANCE.md),
[review import contract](../../docs/characters/ava-morgan/ART041_IMPORT_CONTRACT.json)
and [exact reproduction commands](../../docs/characters/ava-morgan/ART041_REPRODUCE.md).

Facial finish remains below A03: graphic eyes/lids, simple lower-face forms,
pinched/overlapping sculpted hair strands in close-up and simplified hands/shoes
are explicit review limitations. At 16 m the cafe silhouette reads; face detail
is largely lost. Static geometry passes do not grant visual approval or prove
deformation/contact quality. The daylight is a Blender approximation of the
documented outdoor game light, not a Unity screenshot or terrace integration test.

Full `.blend`, GLB, original renders, source and indexed manifests are delivered
as a versioned Actions review artifact; no model binary enters Git. The draft
PR links its verified download. No game write, A03 change, merge, rigging or
animation production is part of this delivery.
