# Reproduce the single B04 elbow proof

Run from the art worktree root with Blender4.5.14 LTS and Python/Pillow. Always use a fresh output directory. Repeating the frozen recipe is a reproducibility check, not authorization for a new design iteration.

Required preserved sources:

| Input | Path expected by config | SHA256 |
| --- | --- | --- |
| B02 | `build/male-neutral-b02/delivery-001/character_b02.blend` | `8300f581fa4e5a7f012d70ae9aadd0d7ca9eb99214b5a8699a1f65f0a9c8e96c` |
| A03 high | `build/male-neutral-a03/delivery-003/character_high.blend` | `e5b4ef5ad0bdde5b2197a0741339841e7e8b1976121c6ac2e25271dded0cb898` |
| B03 comparison | `build/male-neutral-b03/shape-probe-002/candidate.blend` | `d3cd674e377e7c205cf08cd432559e333ce6a3179ddaae60f3541556513ad23a` |

Sources are preserved in the [B02](https://github.com/bobo91/life-sim-art/releases/tag/male-neutral-b02-v0.2), [A03](https://github.com/bobo91/life-sim-art/releases/tag/male-neutral-a03-v0.3) and rejected [B03](https://github.com/bobo91/life-sim-art/releases/tag/male-neutral-b03-v0.3) review archives. Copy source files to these paths without editing originals. Matching B02 asset-report.json and B03 report.json are needed by the pose renderer; source scripts/configs are versioned in this branch. Read their archive manifests for verification.

Commands actually run, with `blender` resolved to the audited executable:

```powershell
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/male_b04_elbow_topology.py -- --out build/male-neutral-b04/topology-001
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/render_male_b04_gate.py -- --candidate build/male-neutral-b04/topology-001/candidate.blend --out build/male-neutral-b04/visual-gate-001 --samples 12
python scripts/compose_male_b04_review.py --input build/male-neutral-b04/visual-gate-001 --out evidence/male-neutral-b04/previews
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/verify_male_b04_preservation.py -- --out build/male-neutral-b04/preservation-001
python scripts/inspect_male_b04_contract.py --out build/male-neutral-b04/contract-audit001
```

The last command audits the preserved B02 GLB, not a new B04 GLB. The versioned integration-baseline directory adds a manually assembled information manifest, actual probe .meta template with proposed stable GUID, attribution and hips-motion readback. These baseline measurements and proposals are identified separately in Q1–Q11.

The single candidate is frozen at SHA256 **194eaa54d52c3b0cb8be764b5d192dacf57f52913c6e990a4f6694edc0b81253**. The first generation's UV diagnostic was corrected after generation without changing the geometry recipe or candidate: use technical-validation.json and the current seam-aware source check, not the obsolete first report's UV diagnostic. No second geometry/weight design was made.

Actual environment: Windows, Blender4.5.14 LTS/Python3.11.15, systemPython3.14.6, audited Radeon RX9070XT plus integrated adapter. Renders use **CPU**, 12 samples and6 threads. No Linux/GPU rendering claim. Blender uses factory startup, offline mode and disabled autoexec; source CloudRig/UI code is never run. No random sampling is used for geometry construction; render settings inherit the same A03 stage.

No GLB/Unity command was run after the mandatory visual gate failed. Conditional Unity preparation was excluded from delivered source because it was unexecuted. Existing B02 Unity results remain historical baseline facts. No broad test-suite expansion was needed; verification targets saved-file preservation, actual images, UV/topology and archive fingerprints.

The rejected review archive contains candidate.blend plus reports, images and source snapshot with SHA256 inventory. It is **not** an import package or playable asset. See [quality report](B04_QUALITY_REPORT.md) before inspecting it. No merge, Phase C or automatic continuation.
