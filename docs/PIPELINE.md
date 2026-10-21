# Headless pipeline (ART-001)

All model vertices, faces and PBR materials originate in `art_pipeline/blender_build.py`.
There are no imported meshes, textures, packs, HDRIs or paid generation calls.
The streetlamp is a pipeline benchmark, not an approved ART-003 production delivery.

## Supported environment

Pin **Blender 4.5.14 LTS** exactly; the generator rejects another version. Host Python
3.11+ uses only its standard library. Blender supplies `bpy`, `bmesh` and `mathutils`.
CPU Cycles, one thread, fixed samples/seed and AgX form the reference renderer.
No GPU is required. Reproducibility is asserted on the same Blender/OS/runtime;
different platforms or Blender builds can produce different floating point pixels.

Download the portable distribution from the official Blender release directory:
<https://download.blender.org/release/Blender4.5/>. Verify its SHA256 against the
official `blender-4.5.14.sha256` before extracting. Do not download asset libraries.

Windows x64 ZIP: `blender-4.5.14-windows-x64.zip`, SHA256
`b9533d2397ac1984db4466fb23a7a4649391cca93f6e84209f9bcc60d071c8b9`.

## Commands

From the repository root in PowerShell:

```powershell
$env:BLENDER_BIN = 'C:\Users\rcalm\tools\blender\blender-4.5.14-windows-x64\blender.exe'
python -m art_pipeline audit
python -m unittest discover -s tests -v
python -m art_pipeline build --config configs/streetlamp.json --output build/run-a
python -m art_pipeline validate build/run-a
python -m art_pipeline build --config configs/streetlamp.json --output build/run-b
python -m art_pipeline compare build/run-a build/run-b
```

Use `--blender /absolute/path/to/blender` instead of `BLENDER_BIN` on any platform.
Each build requires a new/empty output directory and never deletes old results.
A failed build returns nonzero, leaves its log for diagnosis and does not publish a
valid manifest. Blender also uses `--python-exit-code 1` so script failures propagate.
Re-running `build` renders both previews; `validate` never needs Blender.

## Output and provenance

Each bundle contains `<assetId>.glb`, `front.png`, `isometric.png`, `manifest.json`,
`build_report.json` and `blender.log`. The manifest embeds the full config/seed,
canonical config hash, Git source commit, dirty state, source Python digest,
tool versions, command, GLB/PNG hashes, dimensions and validation metrics.
PNG text/time metadata is removed; rendered pixels and color chunks are untouched.

`compare` independently validates both bundles then requires matching input hashes,
tool versions and byte-identical GLB/front/isometric output. Seed-dependent bolt
rotation makes seed changes observable in geometry. Material order is fixed and
independent of JSON key order. No wall clock or random OS entropy enters geometry.

Blender checks finite vertices, manifold edges, loose vertices, degenerate and
duplicate faces, triangle budget and applied transforms before export. The separate
standard-library GLB validator inspects exported accessors, world transforms,
indices, normals, materials, bounds and bottom-center pivot. Bundle validation checks
checksums, previews and required provenance; it does not merely trust a producer's
success message. See the unit tests for rejected malformed exports and bundles.
The streetlamp build additionally verifies a single identity-transform exported mesh
and the service plate's positive-Z coordinates; `scripts/verify_seed.py` independently
rechecks those facts on the actual baseline and changed-seed GLBs. Generic bounds
alone cannot infer semantic forward or the origin of an arbitrary imported hierarchy.

## Coordinates and Unity boundary

Config `dimensionsMeters` always means exported **X width, Y height, Z depth**.
Blender is X-right, Z-up, -Y-forward. glTF export converts to X-right, Y-up,
+Z-forward. The service plate marks the lamp's front (-Y in Blender, +Z in GLB).
The mesh origin is bottom-center; minimum exported Y is zero and X/Z bounds are
centered. Materials use core glTF metallic/roughness, opaque base colors, and no
external textures/extensions. Amber panes are intentionally opaque at this stage.

Unity itself uses a left-handed world; a glTF importer must perform its normal
handedness conversion. This pipeline validates the right-handed glTF data and does
not apply an extra reflection. **Unity import has not been verified** until a game
repository records an actual import test. Rigging/animation and collisions/LODs are
outside ART-001. The canonical and art mirror contracts remain provisional; no
production release should ship before their reconciliation.

## Review and artifacts

Commit source/configs/tests, a small preview pair and validation manifests under
`evidence/`. Generated GLB and Blender logs remain in ignored `build/`. CI uploads
the complete verified bundles as versioned workflow artifacts; production GLB files
belong in versioned releases after contract reconciliation and visual approval.
Do not infer production quality from automated pass/fail. Inspect the actual renders
and state limitations in the PR. Never auto-merge.
