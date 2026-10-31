# Reproduce the Rain visual prototype

Blender **4.5.14 LTS**, official Windows build `62c1db4208e8`; Blender Python 3.11.15. Texture processing: Python 3.14.6, **Pillow 12.3.0**. Cycles CPU, six threads, 36 samples, AgX, render seed 41032 and freckle seed 41033. GPU enumerated in the source audit; GPU rendering was not used. The recipe is `configs/ava_rain_v01.json` plus the versioned mesh-edit scripts, not the rejected `ava041_*` generator.

From a clean repository checkout, install the stated Pillow version into the Python environment you use, then run (fresh output directory):

```powershell
python scripts/reproduce_ava_rain.py --blender 'C:/Users/rcalm/tools/blender/blender-4.5.14-windows-x64/blender.exe' --out build/ava-rain-reproduce
```

Optional `--a03 <approved-static-character.blend>` uses an existing A03 file after verifying its exact SHA256. Otherwise the recipe fetches the pinned static v0.3 release without changing it. Rain's exact official ZIP/native hashes are mandatory; a changed upstream download stops the recipe. The original is never saved by Blender. All Blender stages disable script auto-execution and source `.blend` opens also set `use_scripts=False`.

The recipe executes acquisition → read-only source/licence/GPU audit → static real-mesh extraction (`EyelidsClose.L/R=.32`, `Smile.L/R=.09`, no animation) → original texture remapping/downsampling → bounded mesh edits and fitted outfit → high editable copy → static reduction → actual studio renders → eight-mesh static GLB → existing independent GLB validator → GLB reimport renders → unchanged A03 comparison → camera/daylight/shade review. It creates no rig, clips or Unity files. Hidden skin is removed under clothing; the editable high file retains the higher-resolution fitted surfaces before reduction. Thin folds/soles have their true flat normal where averaged normals would oppose triangle winding.

Actual local final build used those same stages separately, with source under `build/ava-rain-v01/source/`, static extraction `static-final/`, textures `textures/`, and final candidate `candidate-010/`. The final commands were:

```powershell
& $blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/build_ava_rain.py -- --source build/ava-rain-v01/static-final/static-source.blend --textures build/ava-rain-v01/textures --out build/ava-rain-v01/candidate-010 --samples 36 --optimize
& $blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/review_ava_rain.py -- --candidate build/ava-rain-v01/candidate-010 --a03 C:/dir/life-sim-art/build/male-neutral-a01-worktree/build/male-neutral-a03/delivery-003/character.blend --samples 36
```

`$blender` denotes the full executable path above. The source model and `.blend` output may contain save metadata; cross-platform byte identity and GPU/Unity behavior are not claimed. `evidence/ava-rain/metrics.json` records measured export geometry/source preservation and `reproduction.json` in the bundle records the separate-process export repeat actually run. No new CI/test platform is introduced.

`package_ava_rain.py` only packages actual source/export/renders and assembles labelled copies of those renders into contact sheets. It creates no AI images and retouches no character details. The large ZIP is a **draft review release**, not an approved character release. Small review sheets and provenance are in Git.
