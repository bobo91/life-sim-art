# ART-041 source and attribution

Candidate `chr_ava_morgan_041`, `0.1.0-review.1`, seed **41029**. Appearance is
pending owner review. This is a new static Ava task under issue #41.

All Ava geometry originates in `ava041_geometry.py`, `ava041_head.py` and
`ava041_outfit.py`, orchestrated by `build_ava041.py`. The head uses analytic
profile/face fields; eyelids, lips, ears and freckles are original surface
patches. The swept hair and bun use original parameterized surfaces. Clothes,
hands and limbs use authored lofts/sweeps and Blender voxel unions followed by
controlled static decimation. Materials use original role colours, core PBR and
vertex colours. **No image textures, imported Ava mesh, MPFB, purchased asset,
downloaded material/HDRI, model service or AI image generation is used.**

Original project source is delivered to the repository owner. This change does
not add a new public licence grant for the project's original work.

The existing art reference pack is visual direction, not model evidence or
geometry input: [reference manifest](reference-manifest.md). The four versioned
PNGs remain unchanged. Their AI-generated illustration details are not exact
orthographic measurements. Brown eyes, brunette bun, freckles and the cafe
wardrobe are retained; provisional lettering/tattoos and stale backstory are
omitted. See [preflight](ART041_PREFLIGHT.md) for canon conflicts and read-only
game checks.

The tools reuse A03's proven CPU Cycles/AgX studio, fixed-camera, static-selection
GLB export, independent geometry validation, source reopen and reimport methods.
They do not reuse A03 geometry as an Ava base. Existing A03 files and releases
are never written.

The separately rendered comparison character is the unchanged approved static
**A03 v0.3**, a previously modified Blender Studio Snow v4 derivative:

- **Snow Rig (CC) Blender Foundation | studio.blender.org**
- [Original Snow v4](https://studio.blender.org/characters/snow/v4/)
- [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)
- [Approved A03 release](https://github.com/bobo91/life-sim-art/releases/tag/male-neutral-a03-v0.3)
- Source commit `3ae0723b1c450d41ab42f83875164af495949fee`.
- Original review ZIP SHA256 `3ae53894ae1aef5c909a82d1c3d60b3f153005ca8dee0b11cfb646b2b09da6fc`.
- Comparison Blender SHA256 `dcd7681255f49fa704844492b0ffc6964e434ccb4ae59aaba7788b0af56ffd90`.

A03's earlier changes covered Willow Creek identity, hair, materials and static
simplification. ART-041 adds comparison rendering only. Retain this notice with
comparison imagery; no Blender Foundation endorsement is implied. The approved
male-only source exception is not extended to Ava. Neither Snow source binaries
nor its rig/UI code are redistributed in the Ava artifact.

Blender is the installed 4.5.14 LTS build; no add-on or source asset scripts are
enabled. The independent binary validator remains the existing project code.
Every final source/config/render/model file is identified by SHA256 in the
evidence or artifact index.
