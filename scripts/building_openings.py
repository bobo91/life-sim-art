"""Original reusable cottage window and hinged exterior door geometry.

Source coordinates are X right, Y back and Z up; the exterior faces -Y.
Both module roots use the centre of the wall opening at its bottom as their
anchor.  The window sill consequently extends 70 mm below its root.  These
are authored connection anchors, not bounding-box-centre pivots.
"""

import json

import bpy

from building_geometry import G, beam, box, finish


def build_window(config):
    """One opaque four-pane mesh for the 1.10 x 1.25 m wall opening."""
    g = G()
    trim, glass, wood = 0, 1, 2

    # Broad cream casings and a projecting two-step sill remain legible from
    # the normal game camera. Butt joints avoid coincident front surfaces.
    for sign, label in ((-1, 'left'), (1, 'right')):
        box(g, label + '_outer_casing', .07, .13, 0, 1.25, trim,
            center=(sign * .585, -.085), bevel=.007)
    box(g, 'outer_head_casing', 1.24, .145, 1.25, 1.32, trim,
        center=(0, -.085), bevel=.007)
    box(g, 'sill_lower_apron', 1.18, .105, -.07, -.035, trim,
        center=(0, -.04), bevel=.004)
    box(g, 'projecting_sill', 1.24, .20, -.035, 0, trim,
        center=(0, -.06), bevel=.005)

    # The timber sash fits inside the wall opening and is recessed behind
    # the casing. Four separately bounded panes use opaque PBR material.
    for sign, label in ((-1, 'left'), (1, 'right')):
        box(g, label + '_sash_stile', .052, .052, .01, 1.24, wood,
            center=(sign * .514, .025), bevel=.004)
    box(g, 'sash_bottom_rail', .976, .052, .01, .06, wood,
        center=(0, .025), bevel=.004)
    box(g, 'sash_top_rail', .976, .052, 1.19, 1.24, wood,
        center=(0, .025), bevel=.004)
    box(g, 'central_mullion', .028, .032, .06, 1.19, trim,
        center=(0, -.016), bevel=.003)
    for sign, label in ((-1, 'left'), (1, 'right')):
        box(g, label + '_cross_muntin', .474, .032, .611, .639, trim,
            center=(sign * .251, -.016), bevel=.003)
        for bottom, top, level in ((.064, .607, 'lower'),
                                   (.643, 1.186, 'upper')):
            box(g, label + '_' + level + '_opaque_glass', .466, .012,
                bottom, top, glass, center=(sign * .251, .029), bevel=.001)

    obj = finish(config, g, ('trim', 'glass', 'wood'))
    obj['moduleAnchor'] = 'wall-opening-bottom-centre'
    obj['sourceFront'] = '-Y'
    obj['sourceWallOpeningMeters'] = [1.10, 1.25]
    obj['sourceWallOpeningBoundsXYZ'] = json.dumps(
        [[-.55, -.075, 0], [.55, .075, 1.25]])
    obj['sourceExpectedBoundsXYZ'] = json.dumps(
        [[-.62, -.16, -.07], [.62, .051, 1.32]])
    obj['anchorPolicy'] = 'Explicit modular opening anchor; sill extends below local Z=0'
    obj['glassPolicy'] = 'Opaque muted glass; no transmission, transparency or interior dependency'
    return obj


def _component_config(config, component):
    result = dict(config)
    result['assetId'] = config['assetId'] + '__' + component
    return result


def build_door(config):
    """Root + separate frame/leaf meshes; static closed pose, no animation.

    Clear frame passage is 0.99 m wide x 2.135 m high above a 15 mm
    threshold. The leaf is authored around a real vertical hinge so a game
    importer can rotate it later without rebuilding its geometry.
    """
    frame_geo = G()
    for sign, label in ((-1, 'left'), (1, 'right')):
        box(frame_geo, label + '_structural_jamb', .053, .16, 0, 2.15, 0,
            center=(sign * .5215, 0), bevel=.005)
        box(frame_geo, label + '_exterior_casing', .072, .085, 0, 2.20, 0,
            center=(sign * .584, -.085), bevel=.006)
    box(frame_geo, 'structural_head_jamb', 1.096, .16, 2.15, 2.20, 0,
        bevel=.005)
    box(frame_geo, 'exterior_head_casing', 1.24, .09, 2.20, 2.30, 0,
        center=(0, -.085), bevel=.007)
    box(frame_geo, 'low_threshold', 1.10, .21, 0, .015, 0,
        center=(0, -.025), bevel=.002)
    frame = finish(_component_config(config, 'frame'), frame_geo, ('trim',))

    # Leaf coordinates are relative to the lower hinge, not its centre.
    # Only two leaf materials plus the frame trim: three materials overall.
    leaf_geo = G()
    door, metal = 0, 1
    box(leaf_geo, 'solid_door_leaf', .96, .045, 0, 2.12, door,
        center=(.48, -.0275), bevel=.006)
    for bottom, top, label in ((.17, .85, 'lower'), (1.02, 1.92, 'upper')):
        box(leaf_geo, label + '_raised_panel', .73, .025, bottom, top, door,
            center=(.48, -.058), bevel=.009)
    box(leaf_geo, 'brass_handle_backplate', .044, .012, 1.04, 1.20, metal,
        center=(.89, -.054), bevel=.004)
    beam(leaf_geo, 'brass_handle_stem', (.89, -.059, 1.11),
         (.89, -.093, 1.11), .018, metal)
    box(leaf_geo, 'broad_brass_lever', .10, .022, 1.10, 1.12, metal,
        center=(.85, -.099), bevel=.003)
    for bottom, top, label in ((.30, .40, 'lower'), (1.70, 1.80, 'upper')):
        leaf_geo.radial(label + '_hinge_knuckle',
                        [(bottom, .010), (bottom + .002, .012),
                         (top - .002, .012), (top, .010)], 10, metal)
    leaf = finish(_component_config(config, 'leaf'), leaf_geo, ('door', 'metal'))

    root = bpy.data.objects.new(config['assetId'], None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = .20
    for obj, component in ((frame, 'frame'), (leaf, 'door_leaf')):
        obj.parent = root
        obj['assetId'] = config['assetId']
        obj['component'] = component
    leaf.location = (-.48, 0, .015)
    leaf['sourceHingeAxis'] = '+Z'
    leaf['exportedHingeAxis'] = '+Y'
    leaf['sourceLeafBodyBoundsXYZ'] = json.dumps(
        [[0, -.05, 0], [.96, -.005, 2.12]])
    frame['sourceDoorClearBoundsXZ'] = [-.495, .495, .015, 2.15]
    root['assetId'] = config['assetId']
    root['seed'] = config['seed']
    root['provenance'] = 'Original procedural project geometry/materials; no external mesh/texture'
    root['moduleAnchor'] = 'wall-opening-bottom-centre'
    root['sourceFront'] = '-Y'
    root['sourceWallOpeningMeters'] = [1.10, 2.20]
    root['sourceDoorClearBoundsXZ'] = [-.495, .495, .015, 2.15]
    root['sourceDoorHingeXYZ'] = [-.48, 0, .015]
    root['sourceHingeAxis'] = '+Z'
    root['sourceExpectedBoundsXYZ'] = json.dumps(
        [[-.62, -.13, 0], [.62, .08, 2.30]])
    root['thresholdHeightMeters'] = .015
    root['doorPolicy'] = 'Static closed leaf; separate frame and hinge-origin leaf; no rig or animation'
    root['clearPassagePolicy'] = 'Hide or rotate leaf to reveal actual frame opening; no backing wall'
    return root
