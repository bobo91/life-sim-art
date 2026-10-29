# Reproduce B03 isolated elbow proof

Input: preserved B02 delivery-001/character_b02.blend, SHA2568300f581fa4e5a7f012d70ae9aadd0d7ca9eb99214b5a8699a1f65f0a9c8e96c, available from the B02 review release. Run at art worktree root, use fresh output directories.

```powershell
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/male_b03_elbow_shape.py -- --source build/male-neutral-b02/delivery-001/character_b02.blend --config configs/male-neutral-b03-elbow.json --out build/male-neutral-b03/shape-probe-002
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/verify_male_b03_isolated.py -- --candidate build/male-neutral-b03/shape-probe-002/candidate.blend --out build/male-neutral-b03/preservation-003.json
python scripts/compose_male_b03_review.py --input build/male-neutral-b03/shape-probe-002 --out evidence/male-neutral-b03/previews
```

The generator imports only the existing update_support_matrices helper from scripts/male_b02_joint_weights.py; it does not apply B02 weighting again. It creates one candidate,12actual matched renders, keys/pose metadata and an independent candidate.blend. The current generator uses the corrected physical90/10diagnostic plane. For the optional identical-shape-across-diagnostic-passes preservation check, the verifier also opens the retained original shape-probe-001/candidate.blend. If recreating from scratch, first generate the identical current candidate under that path; comparison remains of shape coordinates, not a reproduction of the old test-plane mistake.

The read-only low mesh audit command is:

```powershell
blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/audit_male_b03_elbow.py -- --out build/male-neutral-b03/mesh-audit-001
```

It audits the unchanged B02 body at runframe5.5. The saved high-density comparison was a separate read-only inspection of A03 delivery-003/character_high.blend, M01_body, with the same B02 rest elbow center/axis and radius75mm; count vertices inside longitudinal?55mm and?20mm. No source mesh was saved or changed.

Actual platform: Windows, Blender4.5.14LTS/Python3.11.15, systemPython3.14.6. Render CPU Cycles12samples/6threads with inherited A03seed. No randomness in corrective construction, no GPU or Linux execution claim. No GLB/Unity command was run: the visual gate failed and the owner explicitly made export conditional on clear improvement. The separate export note is an unexecuted source inspection, not a compatibility result.

No topology work, game change, merge or Phase C. The candidate is a rejected inspection prototype, not a runtime-ready character. Read B03_QUALITY_REPORT.md before using it.
