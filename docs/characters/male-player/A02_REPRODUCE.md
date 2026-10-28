# Reproduce A02, preserving A01

Tested: Blender4.5.14 LTS, CPU Cycles32samples/6threads, seed28102026, Windows. No GPU/Linux test claimed. The source Snow blend and the A01 blend are SHA-pinned in configs/male-neutral-a02.json. All output paths must be fresh.

The tested A01 input is build/male-neutral-a01/delivery-002/character.blend. To reproduce from the public A01 review ZIP, extract it independently, verify its ZIP/blend hashes from provenance.json, and use its character.blend as --source. Its textures/ has all13 maps A02 actually renders. Copy that ZIP's evidence/texture-processing.json into textures/atlas-mapping.json to supply the unchanged tile map. The local test used17 prepared PNGs; the four unused extra maps are not required by the builder.

```powershell
python scripts/prepare_male_a02_textures.py --source build/male-neutral-a01/textures-portable --output build/male-neutral-a02/textures --config configs/male-neutral-a02.json
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/build_male_neutral_a02.py -- --source build/male-neutral-a01/delivery-002/character.blend --config configs/male-neutral-a02.json --textures build/male-neutral-a02/textures --out build/male-neutral-a02/delivery-002 --clay-comparison
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/verify_male_neutral_a01.py -- --blend build/male-neutral-a02/delivery-002/character.blend --glb build/male-neutral-a02/delivery-002/chr_player_male_poc_001.glb --expected build/male-neutral-a02/delivery-002/asset-report.json --out build/male-neutral-a02/delivery-002/verification.json
```

The single reproduction run used --out build/male-neutral-a02/reproduction-001 --views face_front and omitted --clay-comparison. All geometry hashes/GLB bytes and that image's decoded pixels matched. Other views were not repeated.

For the existing isolated Unity import, use scripts/run_male_neutral_unity_check.py with --input build/male-neutral-a02/delivery-002 and fresh --project build/male-neutral-a02/unity-static-001. Installed editor/cache arguments are the same as A01; exact commands are captured in evidence/male-neutral-a02/unity-command.json. No game project is opened.

For the render-only matched URP review, copy scripts/RenderMaleA02UrpReview.cs to that isolated project's Assets/Editor, then launch installed Unity batchmode/D3D11 with -executeMethod RenderMaleA02UrpReview.Run -reviewOutput <fresh-art-output> -a01Glb <preserved-A01-glb>. Exact final command is in urp-review-command.json. This adds only a transient art review scene/profile setup and does not save changes to either character. Final preset has no post-processing; key1.5/fill0.5/ambient0.4.

```powershell
python scripts/compose_male_a02_review.py --a01 build/male-neutral-a01/delivery-002 --a02 build/male-neutral-a02/delivery-002 --urp build/male-neutral-a02/urp-review-final --out evidence/male-neutral-a02/previews
```

The static deformation is intentionally defined in the evaluated A01 frame. It is not a ready-to-apply original rig bind edit; see the visual report's animation caveats. No generic parameter bank, body generation, rig, animations or clothing system is created.
