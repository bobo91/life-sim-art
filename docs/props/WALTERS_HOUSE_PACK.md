# Walter's House Pack: porch and garden environment

2026-10-25. Ten original props, ready for owner visual review. Warm aged timber,
muted sage, terracotta and cream follow PR34/35's established soft stylized
direction. Walter's rocker sits by the window; watering can and flowering pot
form a gardening corner. The small succulent sits on an upturned old crate;
bench and worn mat make a practical entry. The approved mailbox is reused at
the drive, unchanged. These placements convey use rather than a line of props.

## Assets and import assumptions

Measured export dimensions are Unity XYZ (width/height/depth), meters.
Every standalone GLB has one identity-transform mesh and bottom-centre root.
Source is Blender+Zup/-Yfront; exported frame is+Yup/+Zfront. Opaque PBR,
maximum four material slots, no textures or external meshes. Lantern uses
opaque warm emissive panels, not transparent glass or a runtime light.

| Asset-ID | XYZ meters | Triangles | Materials |
| --- | --- | ---: | ---: |
| `prop_porch_bench_001` | 1.3500 / 0.9011 / 0.5880 | 856 | 3 |
| `prop_flower_pot_001` | 0.4768 / 0.7110 / 0.4626 | 2,596 | 4 |
| `prop_flower_pot_002` | 0.3332 / 0.3502 / 0.3373 | 2,100 | 3 |
| `prop_welcome_mat_001` | 0.7600 / 0.0205 / 0.4500 | 632 | 3 |
| `prop_porch_lantern_001` | 0.2300 / 0.3770 / 0.2640 | 484 | 3 |
| `prop_wooden_fence_001` | 1.3800 / 0.8120 / 0.0720 | 464 | 3 |
| `prop_fence_post_001` | 0.1480 / 1.0250 / 0.1480 | 308 | 2 |
| `prop_old_watering_can_001` | 0.5106 / 0.3840 / 0.1720 | 1,648 | 4 |
| `prop_wooden_crate_001` | 0.4800 / 0.3200 / 0.3400 | 2,480 | 3 |
| `prop_porch_rocking_chair_001` | 0.6580 / 1.0830 / 0.8700 | 1,884 | 3 |

[Machine-readable contract](../../configs/walters-house-pack.json) contains
numeric candidate collider centres/sizes and open decisions. Colliders are
proposals only; no collider is exported or agreed on the game's behalf. Pots
use body envelopes with foliage excluded; mat has none. Bench/rocker use
conservative boxes; rocking, seating, opening and watering are not implemented.
The crate is open-top in its canonical model; the scene flips the same mesh
as a plant stand. No second crate variant is created.

Fence roots use1.5m post spacing. The1.38m rails butt against the.12m post
shaft; one post handles both ends and corners. Actual mesh seam error is zero
in the saved demonstration. Lantern rear mount plane is source+Y=.132m,
exported-Z=-.132m; the saved scene verifies contact against its wall.

## Main-based delivery and reference provenance

This branch starts directly at main8fd7379a, not an unmerged art branch.
The seven shared art_pipeline files were checked byte-for-byte against that
main tree. No house geometry exists in the art repository, so the facade,
deck, windows, door, steps and path are explicitly TEMP presentation helpers.
They are not a production house and lock no future house dimensions.

To reproduce the approved mailbox without depending on PR34 being merged,
the pack carries its exact project-owned generator/config under unique
walter-reference filenames. Original source SHA256b76d773d1cdd9e5d0470d9a5f0d2784b5be92ef608e0a55f20873521f272f63c;
config SHA2563f2ba255a195e4271c2d775f66eaa10c34179927d3e9018f89e1afc451d52af7.
The worker rejects any mailbox export other than approved SHA256
b243a55a5d92da3cd3a51c3957d0b1e1f1b9737ad8f6ed988121bae69e654698.
Small inspection/loft methods reuse original project techniques copied into
self-contained Walter files. There is no runtime import from PR34/35 scripts.
PR34/35 keep their own review/merge decisions; neither is modified here.

## Actual verification and corrections

Blender4.5.14LTS / embedded Python3.11.15, CyclesCPU with four threads. GPU
types were enumerated; no GPU-compute test or GPU rendering is claimed.
All ten meshes pass closed-edge, loose-vertex, degenerate/duplicate/nonfinite
checks, positive volume, save/reopen and static GLB roundtrip. Independent
GLB validation checks bounds, pivot, indices, normals, materials and unit root.
Final exports are byte-identical to geometry-only preflight005.

The first preflight stopped on a palette-role typo, corrected before rendering.
Draft views exposed coplanar crate corner caps: battens now stop13mm below the
rim. Full run001 passed technically but the close-up exposed arm-support feet
outside the rocker's seat. Their lower ends now meet the front legs. Run002
verified that correction. A scene review then caught the pot above the open
crate; run003 uses the crate upside down, so actual boards support the pot.
All earlier outputs stay local; they are not passed off as final images.

Targeted checks reopen the real .blend files: both front arm supports intersect
their legs; crate caps clear the rim; rail/post and lantern/wall gaps are zero;
two vertical rays verify boards0.5mm below the small pot. These are specific
regressions, not an exhaustive solid-intersection or gameplay-physics proof.
Closed construction components deliberately meet/overlap at attachments.
The existing52 independent-validator tests passed separately.

Final run003 rendered26 actual images in 192.393s. Front/isometric
previews exist for every asset, plus overview,6m,16m and three detail views.
At16m the bench, rocker, plant masses and fence silhouettes read; petal/stem
details are secondary.6m intentionally frames the porch and crops the outer
fence/mailbox.16m contains every prop. The lighting is the same Blender studio
method as the cafe proofs, not actual Unity URP lighting. No new Unity import,
navigation, avatar clearance, animation or final game placement was tested.

## Evidence, commands and review decision

[Ten-model contact sheet](../../evidence/walters-house-pack/contact-sheet.png) ·
[Porch scene](../../evidence/walters-house-pack/porch_scene.png) ·
[6m](../../evidence/walters-house-pack/porch_game_6m.png) ·
[16m](../../evidence/walters-house-pack/porch_game_16m.png) ·
[Rocker close-up](../../evidence/walters-house-pack/rocking_chair_closeup.png) ·
[Lantern close-up](../../evidence/walters-house-pack/porch_lantern_closeup.png) ·
[Fence joints](../../evidence/walters-house-pack/fence_module_joints.png).

```powershell
<Blender4.5.14> --background --factory-startup --offline-mode --disable-autoexec --threads 4 --python-exit-code 1 --python scripts/build_walter_porch.py -- --output build/walter-porch/preflight-new --geometry-only
python scripts/run_walter_porch.py --blender <Blender4.5.14> --preflight build/walter-porch/preflight-new --output build/walter-porch/run-new
<Blender4.5.14> --background --factory-startup --offline-mode --disable-autoexec --threads 4 --python-exit-code 1 --python scripts/verify_walter_contacts.py -- --input build/walter-porch/run-new
python scripts/compose_walter_porch.py --input build/walter-porch/run-new --output build/walter-porch/sheets-new
python scripts/package_walter_porch.py --input build/walter-porch/run-new --sheets build/walter-porch/sheets-new --output build/artifacts/walters-house-pack-v0.1.0-review-new.zip
```

Use fresh directories and replace the executable placeholder. Sources, configs,
manifests, checks and small previews are versioned; large GLB/.blend files are
versioned review artifacts with SHA256 index, outside normal Git blobs. The
latest PR CI reproduces on Linux; its status and verified download link are
recorded in the PR after completion. Raw host logs stay local.

Recommendation: GO for owner visual review. No automatic merge or game changes.
No purchased assets, paid/external generation services, manual modeling,
character work or changes to Ava/PR33. All final geometry/materials are original
project output except the explicitly reused original-project mailbox.
