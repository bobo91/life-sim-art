# Reproduce MALE-NEUTRAL-A01

Tested on Windows with Blender 4.5.14 LTS, bundled Python 3.11.15 and system Python 3.14.6/Pillow. No Linux or GPU execution is claimed. Commands use `blender` for the installed executable; the tested path was `C:/Users/rcalm/tools/blender/blender-4.5.14-windows-x64/blender.exe`.

Use fresh output directories. The scripts refuse to overwrite earlier models. Source scripts remain disabled. Obtain only the owner-authorized [Snow v4 official ZIP](https://studio.blender.org/download-source/files/ba/0f/ba0fe6d810333b1d73c1c359e4dc03cb-6.zip), verify the hashes in PROVENANCE.md, and extract unchanged under `build/source-audit/original/`. Do not enable its embedded rig scripts.

```powershell
python scripts/prepare_male_textures.py --source build/source-audit/original/Snow/textures --output build/male-neutral-a01/textures-portable --max-size 2048 --config configs/male-neutral-a01.json
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/build_male_neutral_a01.py -- --source build/source-audit/original/Snow/snow_v4.2.blend --config configs/male-neutral-a01.json --textures build/male-neutral-a01/textures-portable --out build/male-neutral-a01/delivery-002
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/verify_male_neutral_a01.py -- --blend build/male-neutral-a01/delivery-002/character.blend --glb build/male-neutral-a01/delivery-002/chr_player_male_poc_001.glb --expected build/male-neutral-a01/delivery-002/asset-report.json --out build/male-neutral-a01/delivery-002/verification.json
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/inspect_male_neutral_contacts.py -- --blend build/male-neutral-a01/delivery-002/character.blend --out build/male-neutral-a01/delivery-002/contact-diagnostics.json
python scripts/compose_male_neutral_review.py --input build/male-neutral-a01/delivery-002 --source-gate build/source-audit/base-renders --out evidence/male-neutral-a01/previews
```

Source gate command actually run before editing:

```powershell
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/render_male_source_gate.py -- build/source-audit/original/Snow/snow_v4.2.blend build/source-audit/base-renders
```

For the independent reproduction, use the same builder command with fresh `--out build/male-neutral-a01/reproduction-002 --views front`. Compare GLB SHA256, mesh hashes and decoded front pixels; PNG metadata/bytes and blend metadata need not match. The final nine original renders use one geometry set. The exact config/seed is versioned.

## Isolated Unity check

`scripts/MaleNeutralA01ImportCheck.cs` adapts the existing art static-GLB checker; it is not game code. `scripts/run_male_neutral_unity_check.py` uses an installed Unity editor and an existing local package cache. It creates a fresh project under art/build, imports the GLB, checks texture bindings/material factors and geometry, performs an actual URP render and saves/reopens the probe scene. It never opens the game project or modifies existing editors. The broad T-pose probe collider is not a gameplay controller.

```powershell
python scripts/run_male_neutral_unity_check.py --input build/male-neutral-a01/delivery-002 --project build/male-neutral-a01/unity-static-004 --editor 'C:/Program Files/Unity/Hub/Editor/6000.5.8f1/Editor/Unity.exe' --package-cache 'C:/dir/life-sim-art/build/first-playable-props-unity/probe-002/Library/PackageCache'
```

The tested cached packages are glTFast 6.20.0 and URP 17.5.0. Another machine must provide compatible locally installed/cached packages; the runner does not fetch or install them. Built-in `com.unity.modules.imageconversion` and `com.unity.modules.unitywebrequesttexture` are loaded from the editor installation. Those are required for PNG textures, as documented in the installed official glTFast ProjectSetup manual. The source project/cache paths are dependencies of this local check, not files in the review ZIP.

There is no Humanoid/animation, player build, actual game-camera/lighting or NPC-load test in Phase A.
