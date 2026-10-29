# Reproduce bounded A03 Phase B01

Use the existing immutable source chain: original Snow hash and A01/A03 release links in provenance.json. Preserve the prior files. Work in the art worktree root. Builder requires configs/male-neutral-b01-skeleton.json and the source/A01/A03 paths currently recorded in the script. Use fresh output directories.

```powershell
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/build_male_neutral_b01.py -- --out build/male-neutral-b01/bind-005
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/verify_male_neutral_b01.py -- --input build/male-neutral-b01/bind-005 --out build/male-neutral-b01/roundtrip-003
python scripts/run_male_b01_unity_check.py --input build/male-neutral-b01/bind-005 --project build/male-neutral-b01/unity-003 --editor "C:/Program Files/Unity/Hub/Editor/6000.5.8f1/Editor/Unity.exe" --package-cache "C:/dir/life-sim-art/build/first-playable-props-unity/probe-002/Library/PackageCache" --clips idle,walk,run,turn --fps 24
```

Existing local cached packages only. The Unity runner creates an isolated project, adds installed builtin animation/image modules, imports after URP/Linear setup, samples/bakes actual skins, captures frames and verifies scene reopen. No life-sim-game project is opened. The archived exact capture-checker-source.cs corresponds to the final capture command hash; the current checker retains that Run method and adds the separately tested RunPlayMode method. Reproduction with current Run uses the same capture logic, not a claim of byte-identical checker source.

To reproduce the separate actual runtime smoke, after the import/capture above launch the same editor/project with -batchmode -force-d3d11 -executeMethod MaleNeutralB01AnimationCheck.RunPlayMode -b01Output <fresh-playmode-output> -b01Expected <project>/expected.json -logFile <fresh-log>. Exact command/source hash is in evidence/male-neutral-b01/playmode-command.json. It creates only a four-state art probe controller, enters real PlayMode and measures advancing Animator poses. Use a fresh project for another full run; existing controller/assets are preserved.

```powershell
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/render_male_b01_deformations.py
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/check_male_b01_contacts.py
python scripts/compose_male_b01_motion.py --input build/male-neutral-b01/unity-003/evidence --out build/male-neutral-b01/review-001 --previews evidence/male-neutral-b01/previews --fps 24
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/encode_male_b01_motion.py -- --layout build/male-neutral-b01/review-001/layout.json --out build/male-neutral-b01/review-001/a03-b01-unity-motion.mp4
```

Stress/contact scripts use the recorded final005 and fresh named outputs; adjust output path to a fresh directory for reruns. Outputs are independent copies; none saves original Snow or approved A03. Stress poses are unsaved diagnostic poses, not extra delivered gameplay clips. Video uses all126actualUnityframes at24fps; no additional model render or frame synthesis.

A fresh repeated builder run was performed as reproduction-001 and produced identical GLB bytes and the geometry/weight/pose report. Blend container bytes and another full Unity/render sweep were not repeated. Final GLB SHA256:9a5c1976e06c0d059825715bc0b3eb23c572855452b30bddec0ea586e6266931.

Actual tested platform: Windows, Blender4.5.14LTS/Python3.11.15, systemPython3.14.6, Unity6000.5.8f1/URP17.5/glTFast6.20/D3D11. No Linux/headlessGPU Blender result claimed. See B01_MOTION_REPORT.md for the NO-GO integration gate and known deformation/contact problems. No broad test-suite expansion or new generic framework.
