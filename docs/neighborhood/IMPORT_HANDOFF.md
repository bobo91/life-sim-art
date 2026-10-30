# First Neighborhood Environment — art-to-game handoff

This is a proposed import/layout contract for the first Willow Creek block.
It contains original project meshes and unchanged references from PR #34–#37.
Those PRs were checked before production; their exact commit IDs, open/merged
state and source/config hashes are recorded in
[`neighborhood-reference-locks.json`](../../configs/neighborhood-reference-locks.json).
The new branch does not require a checkout of an unmerged art branch. Original
PRs keep their own approval and merge decisions.

The authoritative scene definition is
[`neighborhood-layout.json`](../../configs/neighborhood-layout.json):
`instances` records stable `instanceId`, `assetId`, `positionSourceXYZ`,
`rotationZDegrees`, positive `uniformScale`, `group`, `static` and optional
`futureInteraction` / `entranceId`. `entrances`, `routes`, `walkableSurfaces`
and `buildingFootprints` provide the corresponding spatial proposals.
Some explicit poses, such as the reused upturned crate, also specify
`rotationXDegrees`; preserve that rotation rather than assuming every pose is yaw.
`assetCatalog` maps each stable asset ID to its relative GLB path and kind.
Every placement also records `positionGlTFXYZ` and an XYZW glTF rotation
quaternion, alongside its original authoring transform. The delivered
`scene/layout.json` enriches the catalogue with the actual model SHA256 values;
resolve catalogue paths against its parent build directory (one level above
`scene`), rather than guessing from object names or local bootstrap paths.
[`neighborhood-assets.json`](../../configs/neighborhood-assets.json) records the
bounded new inventory, seeds, palettes, authored bounds and export budgets.
The current working rectangle is **36 x 36 m**, source X=-18..18 / Y=-18..18.

The environment is an assembly of separately reusable buildings, props,
vegetation and street modules. A review scene is supplied for inspection;
**do not treat it as one indivisible runtime mesh**. There is no game code,
Unity scene modification, automatic merge or external asset purchase.

## Coordinate and placement contract

All dimensions are metres. Authoring/layout coordinates use **Blender X right,
Y back, Z up**, with the default asset front facing **-Y**. The glTF exporter
converts source `(x, y, z)` to right-handed glTF `(x, z, -y)` with +Y up.
`SourceXYZ` fields refer to the authoring frame; glTF bounds/dimensions refer
to the exported frame. Do not swap the axes a second time after import.

Unity uses a different handedness. **The importer and its exact conversion are
still undecided.** Claude should select and test that importer first, then use
the versioned placement transforms/sidecar data. Do not guess a mirror axis or
apply the source positions directly to Unity Transform fields. Validate with
an asymmetric object and the doorway's forward direction before populating
the whole scene. Imported mesh dimensions must remain in metres with unit root
scale. Uniform positive scale and source-Z rotations belong to scene instances.
For a source-Z angle theta, the corresponding glTF quaternion is
`(0, sin(theta/2), 0, cos(theta/2))` in XYZW order. This is a right-handed glTF
pose, not a final Unity quaternion; apply the selected importer's conversion.

Building modules retain the connection anchors proposed in PR #37; approved
props retain their original pivots. An origin need not equal the centre of a
mesh's bounds. Apply the recorded matrix/transform to the whole asset root,
including its child hierarchy, and preserve any importer conversion transform.
Do not overwrite an imported quaternion pose with Euler fields.

## Ground, route and entry points

The residential road spans source Y=-3..3, with sidewalks on Y=-5..-3 and
Y=3..5. Grass top is Z=0, road top Z=0.02, and sidewalk/walkway top Z=0.12.
Walter and the smaller neighbor retain finished floors at Z=0.60; their
existing three steps use 0.20 m risers. The café's finished floor is Z=0.12;
the terrace tiles top out at Z=0.11, creating a 10 mm threshold difference.
The source layout and imported geometry, rather than a generic ground plane,
determine these walking levels.

The current principal building roots are Walter `(-11, 8, 0)`, neighbor
`(2, 8, 0)`, and café `(10, -8, 0)`. The café turns 180 degrees around source Z
to face the street; the residential houses face the opposite sidewalk.
These are scene-instance placements, not changes to approved asset geometry.

Proposed Walter-to-café centerline, in source XYZ:

```text
(-11, 7.5, 0.60)  Walter entry
(-11, 5.1, 0.12)  stair/approach transition
(-11, 4.0, 0.12)  residential sidewalk
(-7,  4.0, 0.12)  crossing approach
(-7,  3.0, 0.028) nominal crossing/curb-ramp transition
(-7,  0.0, 0.028) carriageway marking top
(-7, -3.0, 0.028) nominal crossing/curb-ramp transition
(-7, -4.0, 0.12)  crossing exit
(10, -4.0, 0.12)  café sidewalk
(10, -7.5,0.12)   café entry
```

This is a proposed NPC route, **not a baked NavMesh or controller path**.
The crossing is the only declared route segment through the carriageway;
future traffic/priority rules remain game-owned. Test pedestrian capsule
clearance, actual stair traversal and curb-ramp transitions in Unity. Ramp
modules lower the sidewalk toward the road at this crossing; waypoint heights
remain a proposal and must be projected against the imported walkable geometry.
The ramp top is approximately Z=0.10333 at its centre (source world Y=+/-4),
while the nearby level sidewalk is Z=0.12. Asphalt is Z=0.02; raised painted
crossing bars are Z=0.028. Consequently this nominal route is not an exact
foot-contact curve or a completed stair/ramp traversal solution.
The art
layout reserves space for walking; no runtime navigation claim is made.

## Groups, visibility and future interaction

Keep the actual source roots and named layout groups: `building.*`,
`vegetation.*`, `road`, `road.markings`, `walkway`, `walkway.ramp`, `curb`,
`ground`, `green.pocket`, `street.*`, `walter.*`, `neighbor.*` and `cafe.*`.
Repeated objects should reference
the same source asset/prefab; variation comes from positive uniform scale,
rotation, configured palette and placement rather than new asset IDs.

Building hierarchies retain `moduleId` / `hideGroup` metadata from PR #37:
`roof`, `wall.south`, `wall.north`, `wall.east`, `wall.west`, `corner.*`,
`floor`, `foundation` and `porch`. Roof includes its trims and canopies.
Window/door inserts follow their wall, corner trims follow adjoining walls,
and mounted lanterns must follow their supporting wall. Hiding a roof must
not remove floors or exterior walls. The supplied previews demonstrate art
groups, **not a runtime camera-occlusion system**.

The door leaf remains separate from its frame at the authored hinge. Opening
directions, interaction prompts, triggers and state changes are future game
work. The mailbox must have an interaction prompt independent of its small
flag. Café tables reuse the same base asset for bare/set presentation.

Roads, sidewalks, vegetation and architectural shell meshes are proposed static
objects. A whole building root tagged for future door interaction must not make
every shell mesh dynamic: preserve its independent leaf and children.
Doors, mailbox, café quest objects and other explicitly tagged props
are candidates for future interaction; the tags do not implement behavior.
Do not infer interactability from object names or visual detail alone.

## Collision proposals and known limits

Use simple ground/walkway boxes and compound wall boxes that leave real doors
clear. Do not add one house-wide solid BoxCollider. Door leaves need separate
future colliders; window/door frames must not fill their passage with a box.
Use trunk-only vegetation envelopes where needed, leaving foliage decorative.
Sidewalk clearance should follow the declared walkable surfaces, building
footprints and actual prop envelopes. Small plants, awnings, sign lettering and decorative trim
do not need pedestrian collision. Collision layers, navigation bake, curb ramps
and street crossings need game-side confirmation.

The café has tall shopfront glazing, a striped awning and the temporary name
**Juniper Cafe**. The name is a configurable label, not a finalized business
identity. Its sign uses original geometric lettering without a purchased or
operating-system font. The neighborhood street name is likewise temporary.
The same storefront/awning/sign modules wrap the café's street-facing corner;
there is no separate corner storefront kit. The two domestic buildings retain
their earlier geometry and differ in layout, proportions and configured colour.

Offline clearance checks screen the actual table, chair, mailbox, bench and
lamp configuration envelopes with instance rotation/scale against the reserved
route. They also include the crate, both flower pots, watering can, rocking
chair, fence sections and fence posts. Where an existing body-only proposal is
descriptive rather than numeric, the full configured mesh envelope is used as
a conservative containing box. The upturned crate's X180 rotation is included
in the projected footprint. Parasol checks use the numeric weighted-base box,
so elevated shade may overhang; the lamp mesh envelope conservatively contains
its base. Low shrub envelopes and tree-root envelopes are also screened.
Regression cases deliberately restore the former table and crate/pot
obstructions to confirm that the checks reject them. This is a placement guard,
not a complete collision simulation or proof about every future interactive object.

Glazing is opaque PBR for the present review. Interiors are empty shells with
space reserved for a café counter; there is no furnished interior or upper
floor. Lighting is Blender review lighting. Unity importer/version, URP shader
mapping, appearance under game lighting, runtime hiding, interaction and
navigation are **not verified by renders or GLB roundtrips**.

## Reproduction and ownership

Use the PR's deterministic scripts/configurations and pinned Blender 4.5.14.
From the repository root, with Pillow 12.3.0 installed:

```text
python -m unittest discover -s tests -v
python scripts/run_neighborhood.py --blender <Blender4.5.14> --output build/neighborhood/review-001
python scripts/compose_neighborhood.py --input build/neighborhood/review-001 --output build/neighborhood/review-001/review
python scripts/package_neighborhood.py --input build/neighborhood/review-001 --output build/artifacts/neighborhood-v0.1.0-review.1.zip
```

Use fresh output paths; the scripts preserve earlier runs. The Linux workflow
runs this same sequence on a clean checkout with the checksum-pinned official
Blender archive. To rename the temporary business/street mesh labels, edit the
corresponding sign asset's `cafeName` / `streetName` configuration and regenerate;
keep the layout display names and review-only top-down captions consistent.
The asset package supplies separate GLBs, editable Blender files, per-asset
manifests, actual preview renders, layout data and source hashes. Refer to the
PR quality report for the commands/tests actually run and verified artifact
link; this contract does not claim unperformed Unity tests.

Preserve the existing project source snapshots and reference locks. Do not
silently substitute a later open-PR revision. If importer behavior requires a
contract change, record that decision with the game repository before shipping.
