# PR34: portable contact sheets and import readiness

2026-10-25. Owner decision: mailbox and bare cafe table are visually approved
for First Playable Day; no further aesthetic changes are needed. Merge remains
pending the final report and explicit Unity import-contract confirmation in
game issue53. Claude currently has no credits; PR34 and the
[handoff checklist](CLAUDE_IMPORT_HANDOFF.md) preserve the work for later review.
No other prop production before that contract gate is cleared.

## P2 change and evidence

The compositor no longer requires a Windows system font. `--font` permits an
explicit font; automatic selection tries available Arial/DejaVu/Liberation,
then Pillow's size-aware embedded font. Pillow >=10.1 is required, with the
tested12.3.0 pinned in CI. An invalid explicit font reports an error. Existing
output directories are refused to preserve the original review images.

The dedicated verification command runs the compositor with automatic and
forced embedded fonts. It checks actual GLB SHA256 against the reviewed
manifest, exact production source hashes, unchanged input/evidence files,
four hero panels, eight unscaled crops and the full game-camera frame.
Local execution passed on both font paths; the automatic Arial path reproduces
both original comparison PNGs byte-for-byte. Linux execution is verified by
the PR workflow and its separate contact-sheet artifact, not inferred from
this local result. Check the PR's latest CI result for its actual status.

No geometry, camera, material, raw render or original comparison PNG changed.
Original comparison hashes:

- `quality-sheet.png`: `f8be98583976b41c165c976e2788bd2915b5991ceddb523332d9b208d2c7b1cd`
- `game-camera-comparison.png`: `56662888024f57b2a14831a016e7351305a8988965f2d9826bb7d64875a8c697`

## Game coordination remains explicit

[Follow-up in game53](https://github.com/bobo91/life-sim-game/issues/53#issuecomment-6394353758)
requests importer/version, actual Unity import, measured bounds and identity
scale, bottom-center pivot/+Z forward, URP material verification and exact
game-owned collision envelopes. No acknowledgement is inferred from posting it.

Remote main remains pinned to863906b5. In the separately reviewed, unmerged
GAME-038 branch9a85db5, mailbox placeholder dimensions(0.50,1.30,0.40)m differ
from the approved art proof(0.36,1.43,0.62)m. Do not scale-fit the mesh to that
old envelope. Collider dimensions/shape must be deliberately chosen by Claude.
A solid box over the table's full bounds blocks the space underneath its top;
that is a gameplay decision, not an automatic art export property.

The branch has an explicit mailbox action prompt independent of the flag:
“F / A Check the mailbox”, then “Read the letter again”. Its action range2.2m
differs from issue51's prompt-from5m wording;5m currently means a HUD marker.
Claude must reconcile and verify this in the standalone player. The flag is
decorative/contextual and cannot be the sole interaction signal.

The isolated [Unity evidence](../../evidence/first-playable-props-unity/README.md)
preserves the earlier restricted-license and partial Null-graphics attempts.
The later [graphics validation004](../../evidence/first-playable-props-unity/graphics-004/unity-game-lighting-report.json)
passed in an isolated copy of the actual game scene from commit9a85db5, using
its real URP lighting. Materials, normals, bounds, scale/pivot/orientation,
save/reopen and candidate-collider physics checks passed. Original Bootstrap
scene bytes and approved GLB bytes remain unchanged. Three Canvas components
were disabled only in the validation copy to remove UI rectangles from the
comparison views; no aesthetic or mesh change was made.

This is an EditMode graphics/import pass, without PlayMode or UI verification.
It does not accept the proposed importer contract, gameplay colliders, routes,
table placement or prompt behavior on Claude's behalf. No original game code,
game package or integration is changed here. Explicit confirmation is still
required in #53; silence while Claude lacks credits is not acceptance.
No automatic merge. Counter/chair/tin remain on hold until the Unity contract
is ready, then may proceed in the same visual style without a new long design
study.
