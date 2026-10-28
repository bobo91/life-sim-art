# Reproduce A03

Use preserved A02 character.blend as the SHA-pinned input. Its public v0.2 artifact/source hashes are in evidence/male-neutral-a03/provenance.json. The adjacent textures/ folder supplies the same13 PNGs; no new textures or external base are downloaded. Use fresh output directories. Tested Windows/Blender4.5.14 LTS, CPU Cycles32samples/6threads; no GPU/Linux execution claimed.

```powershell
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/build_male_neutral_a03.py -- --source build/male-neutral-a02/delivery-002/character.blend --config configs/male-neutral-a03.json --out build/male-neutral-a03/delivery-003 --optimize
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/verify_male_neutral_a01.py -- --blend build/male-neutral-a03/delivery-003/character.blend --glb build/male-neutral-a03/delivery-003/chr_player_male_poc_001.glb --expected build/male-neutral-a03/delivery-003/asset-report.json --out build/male-neutral-a03/delivery-003/verification.json
```

The builder saves character_high.blend before static simplification, captures high/optimized comparisons, then exports only the optimized character. It never saves the A02 input. Head/eye/brow/hair topology is protected by the optimizer; the refinement itself changes hair caps by144 triangles. The explicit final recipe chooses gentler shoes and source split normals; strict DEFAULT_RECIPE is not the delivered recipe. The29,367 result is intentionally above the25-28k target.

For the one-view reproduction use a fresh --out and --optimize --views face_front. Geometry hashes/GLB bytes and that image's decoded pixels matched. High QC views are skipped in this focused repeat.

Use existing scripts/run_male_neutral_unity_check.py with --input build/male-neutral-a03/delivery-003, fresh --project build/male-neutral-a03/unity-static-002 and the same installed editor/package-cache arguments as A02. Exact command is in unity-command.json. Then copy scripts/RenderMaleA03UrpReview.cs into the isolated project's Assets/Editor and run installed Unity batchmode/D3D11 -executeMethod RenderMaleA03UrpReview.Run -reviewOutput <fresh-art-output> -a02Glb <preserved-A02-glb>. Exact final call is in urp-review-command.json. No game project is opened.

```powershell
python scripts/compose_male_a03_review.py --a02 build/male-neutral-a02/delivery-002 --a03 build/male-neutral-a03/delivery-003 --urp build/male-neutral-a03/urp-review-final-003 --out evidence/male-neutral-a03/previews
```

No new rig, animation system, shape-key library or clothing system. Snow binding/weights remain unproven; do not treat the optimized static mesh or retained high static copy as a ready-to-animate character.
