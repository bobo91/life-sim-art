# First Neighborhood — existing asset references

The neighborhood starts from main
`8fd7379a6ce1023cf8fd7a690bad0f5ac5bed33f`. The GitHub state was checked on
**2026-10-26**, before production: all four source PRs were **open and unmerged**.
The neighborhood neither merges nor edits them.

| PR | Immutable source commit | Existing content reused |
| --- | --- | --- |
| [#34](https://github.com/bobo91/life-sim-art/pull/34) | `96eb13ada9bab56a3c8cfa5de307a16753025f65` | Approved mailbox and café table |
| [#35](https://github.com/bobo91/life-sim-art/pull/35) | `6f6306fe56598ab9e32a4946ed0d255174a73ad7` | Counter, chair, tin, cup, tablecloth and parasol |
| [#36](https://github.com/bobo91/life-sim-art/pull/36) | `b290bcf5702344d1a911cd31f793f77d8cafcbaf` | Ten porch/garden props |
| [#37](https://github.com/bobo91/life-sim-art/pull/37) | `573c6756820e1c3baf759286aab7b89f2cf239cd` | Walter and smaller house, original building modules |

PR #35 itself is based on PR #34. This neighborhood does not inherit that
branch stack: it includes the required unchanged project source/config
snapshots at their canonical paths. The classic streetlamp is the existing
main generator `art_pipeline.blender_build.streetlamp`, using
`configs/streetlamp.json`, seed 1701 and asset ID
`prop_streetlamp_pipeline_001`. It is not another lamp design.

## Machine-readable locks and cache

[neighborhood-reference-locks.json](../../configs/neighborhood-reference-locks.json)
records **21 stable reference IDs**, source PR/commit, approved container
digests where available, and **37 source/config SHA256 pins**. The inventory is
two houses, ten porch props plus the mailbox, the café table, six café props,
and the existing main streetlamp. There are no new copies or variants of the
approved models: scene instances reuse these IDs and mesh data.

Early layout inspection may load the lock file's relative `bootstrapPath`
hints from preserved approved local outputs. These paths are **audit/draft
helpers only**. Final generation and CI never require those local build
folders, an unmerged checkout, a download URL or an expiring Actions artifact.

Inside isolated Blender, call:

```python
from pathlib import Path
from neighborhood_references import build_references
references = build_references(Path("build/neighborhood/new-run"))
```

Call it before assembling a neighborhood: the function clears the current
Blender scene for each independent reference. It regenerates the existing
assets from the pinned source functions without re-rendering their previews.
It refuses an existing cache folder and writes:

```text
<output>/reference/<assetId>/<assetId>.glb
<output>/reference/<assetId>/<assetId>.blend
<output>/reference/<assetId>/build_report.json
<output>/reference/reference-cache.json
```

Each original prop export must match its approved GLB SHA256 **byte for byte**.
The main lamp has a pinned canonical source/config; its actual container digest
is recorded on generation because no old local container was required.
The cache also checks mesh health and exported GLB geometry roundtrips.
Editable house files retain their instance hierarchy and omit the unused
source-template object stack.

## House identity and fingerprint limits

House regeneration can legitimately change unused data-block or container
names. Both house entries therefore require a fingerprint measured from the
approved GLB, rather than accepting an arbitrary new mesh or demanding
byte-identical container metadata. `geometry_fingerprint()` hashes sorted,
unique **world-space source positions rounded to five decimals**, with zero
signs normalized, plus the total triangle count. A missing or mismatching
approved fingerprint stops cache generation.

This is a geometry-preservation check with approximately 0.01 mm coordinate
quantization. It does **not** independently prove identical normals, materials,
UVs or triangle connectivity beyond the count. The unchanged source/config
hashes, mesh-health checks, independent GLB validation and actual renders are
the accompanying evidence; a fingerprint alone is insufficient.

The house roots preserve authored floor/entry coordinates and wall/roof hiding
groups from the existing building contract. Neighborhood placement transforms
are separate layout data; they do not remodel the source houses.

## Provenance and verification

All referenced meshes/materials are original project procedural content.
There are no purchased packs, unlicensed reference meshes, external textures
or additional third-party asset licences. This is a provenance statement for
the project's own work, not a grant of a new public asset licence. The original
PRs keep their own review and merge decisions; PR #33/Ava is unrelated.

Run the source-lock and fingerprint regression checks without Blender:

```text
python -m unittest tests.test_neighborhood_references -v
```

These tests validate the lock records and early rejection behavior. Actual
Blender builds, complete geometry/export checks, Linux reproduction and package
read-back results are recorded by the neighborhood runner and quality report;
this document makes no claim about an unperformed render or Unity import.
