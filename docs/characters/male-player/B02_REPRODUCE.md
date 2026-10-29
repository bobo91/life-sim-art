# Reproduce the bounded B02 correction

Use preserved B01 bind-005/character_b01.blend SHA256 a9fb4a469aeec6cf9b82cfb580bafe8d658055c29b8b297925983fda380e126e. Input provenance/release is in evidence/male-neutral-b02/provenance.json; it is a separate source file, never overwritten. Run at art worktree root with fresh output directories.

```powershell
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/build_male_neutral_b02.py -- --out build/male-neutral-b02/delivery-001
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/verify_male_neutral_b02.py -- --input build/male-neutral-b02/delivery-001 --out build/male-neutral-b02/roundtrip-001
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/check_male_b02_contacts.py -- --after build/male-neutral-b02/delivery-001 --out build/male-neutral-b02/paired-contact-001.json
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/render_male_b02_daily.py -- --input build/male-neutral-b02/delivery-001 --out build/male-neutral-b02/daily-001
python scripts/run_male_b02_unity_check.py --input build/male-neutral-b02/delivery-001 --project build/male-neutral-b02/unity-001 --editor "C:/Program Files/Unity/Hub/Editor/6000.5.8f1/Editor/Unity.exe" --package-cache "C:/dir/life-sim-art/build/first-playable-props-unity/probe-002/Library/PackageCache" --baseline build/male-neutral-b01/bind-005/chr_player_male_poc_001.glb --clips idle,walk,run,turn --fps 24
```

Builder uses versioned male-neutral-b02-joints.json and male-neutral-b02-turn.json. It reads the old baked clips, preserves original52rest frames/approved appearance, applies only local weights/supports, replaces turn legs and keys the58ordinary bones. No source script/CloudRig executes, no generic system or facial edit. All new support behavior is baked: future animations/retargeting must supply corresponding support channels.

The runner uses installed local cached packages, never life-sim-game. Exact capture command/hashes are in unity-command.json; exact separate actualPlayMode/crossfade call/hashes are in playmode-command.json. After the import/capture run, launch the same editor/project with -batchmode -force-d3d11 -executeMethod MaleNeutralB02AnimationCheck.RunPlayMode -b02Output <fresh-runtime-output> -b02Expected <project>/expected.json and a fresh -logFile. Use a fresh project if recreating controller assets. The archived capture-checker-source.cs pins capture execution.

```powershell
python scripts/compose_male_b02_review.py --input build/male-neutral-b02/unity-001/evidence --out build/male-neutral-b02/review-001 --previews evidence/male-neutral-b02/previews --fps 24
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/encode_male_b02_motion.py -- --layout build/male-neutral-b02/review-001/layout.json --camera full --out build/male-neutral-b02/review-001/a03-b02-unity-motion.mp4
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/encode_male_b02_motion.py -- --layout build/male-neutral-b02/review-001/layout.json --camera game16m --out build/male-neutral-b02/review-001/a03-b02-unity-16m.mp4
python scripts/compose_male_b02_checks.py --out build/male-neutral-b02/check-sheets-001 --previews evidence/male-neutral-b02/previews
```

All252nativevideo-input hashes are in previews/layout.json and video.json. Delivered artifact frames retain frames/<clip>/ and frames16m/<clip>/ so new layouts can be regenerated without local absolute paths. Video encode uses installed Blender VSE/FFmpeg H264, no external encoder service. No stills are retouched; frame sampling and labels are documented.

Actual tested Windows Blender4.5.14LTS/Python3.11.15, systemPython3.14.6, Unity6000.5.8f1/URP17.5/glTFast6.20/D3D11. Diagnostic Cycles CPU12samples, inherited A03 seed; corrections use no random sampling. No BlenderGPU or Linux result claimed. One repeated builder run produced identical GLB/report; no repeated full Unity sweep. Final GLB SHA256:4faa2eec33d131b7fcdc4b41720e5abbd16e03eab594bf764f3d7ae041de3d33.

Read B02_QUALITY_REPORT.md before using the artifact: current elbow quality remains NO-GO for playable integration. No merge or Phase C.
