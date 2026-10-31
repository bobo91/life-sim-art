# Reproduce Ava's static visual candidate

Use Blender **4.5.14 LTS**, factory startup, offline mode, auto-execution disabled.
System Python 3.11+ with Pillow is only needed for evidence layout, not modelling
or export. No network, third-party model, paid service or installed character
add-on is needed to generate Ava. Use fresh output paths; scripts preserve prior
outputs.

From this PR checkout:

```powershell
$avaBlender = 'C:\Users\rcalm\tools\blender\blender-4.5.14-windows-x64\blender.exe'
& $avaBlender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/build_ava041.py -- --config configs/ava041.json --out build/ava041
& $avaBlender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/validate_ava041.py -- --blend build/ava041/character.blend --glb build/ava041/chr_ava_morgan_041.glb --out build/ava041-validation.json
& $avaBlender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/build_ava041.py -- --config configs/ava041.json --out build/ava041-repeat --views none
& $avaBlender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/render_ava041_roundtrip.py -- --build build/ava041 --out build/ava041-roundtrip
```

For the required A03 comparison, append `--a03 path/to/character.blend` to the
first build command. Obtain that exact file from the
[unchanged A03 v0.3 ZIP](https://github.com/bobo91/life-sim-art/releases/download/male-neutral-a03-v0.3/male-neutral-a03-v0.3-review.zip).
Verify the archive and Blender hashes in [provenance](ART041_PROVENANCE.md).
The generator rejects another source hash. It reads only the ten mesh objects
for a comparison frame after saving Ava's standalone source/export. It never
saves the imported A03 or adds its data to Ava's source/GLB.

```powershell
python scripts/compose_ava041.py --build build/ava041 --out evidence/ava041
python scripts/package_ava041.py --build build/ava041 --validation build/ava041-validation.json --out build/artifacts/ava-morgan-visual-v0.1.0-review.1.zip
```

Omitting `--a03` intentionally omits that comparison image; the complete owner
review and CI default include it. Image layout requires the full twelve-view
build. The workflow downloads the verified reference without checking out or
changing the A03 branch.

Actual Windows delivery run: `build/ava041-final-005`, with the exact approved
A03 file at `../male-neutral-a01-worktree/build/male-neutral-a03/delivery-003/character.blend`.
Independent regeneration: `build/ava041-reproduce-002 --views none`. Results and
the commands actually run are retained in `evidence/ava041/runtime/`.

Reproduction means identical GLB bytes in two separate processes on the measured
platform. Blender source files contain file/session metadata; no byte-identical
`.blend` or cross-platform pixel guarantee is claimed. The Actions artifact has
its own per-file hashes and platform evidence. Large model/source binaries stay
in the versioned review artifact, outside normal Git blobs.
