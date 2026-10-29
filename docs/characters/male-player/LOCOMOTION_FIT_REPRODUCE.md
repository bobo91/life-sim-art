# Reproduce A03 Locomotion Fit v0.1

Run from the art worktree root using the preserved B02 release files at `build/male-neutral-b02/delivery-001/`. Source .blend SHA256 is8300f581fa4e5a7f012d70ae9aadd0d7ca9eb99214b5a8699a1f65f0a9c8e96c. Preserve the sibling asset-report.json for its existing support-joint definitions. All commands use fresh output paths, except the explicitly documented single fade-only reuse of the Unity project.

```powershell
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/build_male_locomotion_fit.py -- --out build/male-locomotion-fit/delivery-001
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/verify_male_locomotion_fit.py -- --input build/male-locomotion-fit/delivery-001 --out build/male-locomotion-fit/validation-003
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/measure_male_locomotion_contacts.py -- --input build/male-locomotion-fit/delivery-001 --out build/male-locomotion-fit/contact-001.json
python scripts/run_male_locomotion_fit_unity.py --input build/male-locomotion-fit/delivery-001 --project build/male-locomotion-fit/unity-002 --editor "C:/Program Files/Unity/Hub/Editor/6000.5.8f1/Editor/Unity.exe" --package-cache "C:/dir/life-sim-art/build/first-playable-props-unity/probe-002/Library/PackageCache" --fps 24
```

The current runner creates a fresh isolated project, imports/reopens/renders the candidate, then captures the final0.08s-fade settings in actual PlayMode. The recorded run originally used0.12/0.16 and then reran **only motion** after the one fade-setting correction. Its exact commands/checker hashes are in evidence/male-locomotion-fit/unity-import-command.json and unity-motion-command.json. The fade-only call was:

```powershell
Unity.exe -batchmode -force-d3d11 -projectPath <art>/build/male-locomotion-fit/unity-002 -logFile <art>/build/male-locomotion-fit/unity-002/unity-motion-correction.log -executeMethod MaleLocomotionFitMotionCheck.Run -fitOutput <art>/build/male-locomotion-fit/unity-002/motion-correction-001
python scripts/compose_male_locomotion_fit.py --input build/male-locomotion-fit/unity-002/motion-correction-001 --out build/male-locomotion-fit/review-001 --previews evidence/male-locomotion-fit/previews
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/encode_male_locomotion_fit.py -- --layout build/male-locomotion-fit/review-001/layout.json --camera full --out build/male-locomotion-fit/review-001/a03-locomotion-fit-unity.mp4
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/encode_male_locomotion_fit.py -- --layout build/male-locomotion-fit/review-001/layout.json --camera game16m --out build/male-locomotion-fit/review-001/a03-locomotion-fit-unity-16m.mp4
```

Final sheets were laid out once more under review-layout-002/final-layout-002 to include explicit crops of measured worst transition frames. Source Unity frames and video pixels/timing are unchanged. Native frame hashes cover both cameras and close-ups; MP4 timing/reopen/decode records are in video-full.json/video-16m.json. The archive contains the final native frames and selected decoded views. This is local Blender VSE/FFmpeg encoding; no external service or paid API.

Actual tested Windows environment: Blender4.5.14 LTS/Python3.11.15, systemPython3.14.6, Unity6000.5.8f1/URP17.5.0/glTFast6.20 onD3D11. The Unity report records the actual graphics backend. No new Blender GPU, Linux, OS-input or game test is claimed. Source CloudRig/UI autoexec stays disabled throughout.

Retained empty/failed reach-preflight directories precede the first saved candidate006; they are not six artistic model iterations. Candidate006 identified a direct-export frame1 time offset; final delivery001 keeps the same poses and normalizes only animation-input seconds to0. The STEP-sampler diagnostic fix in the read-only verifier handles existing constant baseline channels; it does not alter the candidate. Failed and successful test evidence are identified separately.

Large .blend/.glb/MP4 and native image sequences belong to the versioned review archive, not Git. Source/config/report/previews are versioned. See the quality report for the unresolved transitions/pivots and the required owner review stop.
