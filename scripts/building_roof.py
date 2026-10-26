"""Original fixed-grid roof modules for the Walter modular building proof.

Coordinates are authored connection anchors, not bounding-box centres.  The
main house has a 6 m span, a 1.8 m roof rise and 2 m longitudinal bays.  Each
piece is closed; the broad stepped courses are deliberately visible at game
distance without adding individual tile geometry or external textures.
"""
import math

from building_geometry import G, box, finish


def _xz_prism(g, name, profile, ymin, ymax, material):
    """Extrude a simple X/Z polygon between two Y planes."""
    g.loft(name, [[(x, y, z) for x, z in profile] for y in (ymin, ymax)], material)


def _yz_prism(g, name, profile, xmin, xmax, material):
    """Extrude a simple Y/Z polygon between two X planes."""
    g.loft(name, [[(x, y, z) for y, z in profile] for x in (xmin, xmax)], material)


def _round_vent(g, centre_z, backing_material, trim_material):
    """Opaque decorative vent: closed backing, closed ring and broad louvers."""
    count = 16
    outer, inner = .24, .18
    circle = [(math.cos(i * math.tau / count), math.sin(i * math.tau / count))
              for i in range(count)]
    _xz_prism(g, 'vent_dark_backing',
              [(x * .185, centre_z + z * .185) for x, z in circle],
              -.143, -.082, backing_material)
    # A true annular prism, with no coincident opaque disk on its front.
    rings = [[(x * radius, y, centre_z + z * radius) for x, z in circle]
             for radius, y in ((outer, -.087), (outer, -.171),
                               (inner, -.171), (inner, -.087))]
    vertices = [p for ring in rings for p in ring]
    faces = []
    for ring in range(4):
        following = (ring + 1) % 4
        for i in range(count):
            j = (i + 1) % count
            faces.append((ring * count + i, ring * count + j,
                          following * count + j, following * count + i))
    g.part('vent_cream_surround', vertices, faces, trim_material)
    for i, dz in enumerate((-.12, -.04, .04, .12)):
        width = 2 * math.sqrt(inner * inner - dz * dz) + .012
        box(g, f'vent_louver_{i:02}', width, .026,
            centre_z + dz - .014, centre_z + dz + .014,
            trim_material, center=(0, -.156), bevel=.003)


def build_roof_half(config):
    """Positive-X half; mirror by rotating 180 degrees around the ridge axis.

    Origin is the ridge baseline at the bay centre.  Authored bounds are
    X 0..3.35, Y +/-1, Z -.35..1.808.  The other half is a Z rotation, not
    a negative scale.  Bay ends intentionally have no longitudinal overhang.
    """
    g = G()
    roof, trim, wood = 0, 1, 2
    top = lambda x: 1.8 - .6 * x
    _xz_prism(g, 'closed_pitched_roof_substrate',
              [(0, top(0)), (3.35, top(3.35)),
               (3.35, top(3.35) - .09), (0, top(0) - .09)],
              -1, 1, roof)
    for i in range(8):
        a, b = i * 3.35 / 8, (i + 1) * 3.35 / 8
        _xz_prism(g, f'broad_roof_course_{i:02}',
                  [(a, top(a) - .002), (b, top(b) - .002),
                   (b, top(b) + .018), (a, top(a) + .008)],
                  -1, 1, roof)
    # Fascia is inset from the roof end face so it cannot Z-fight with it.
    box(g, 'cream_eave_fascia', .075, 2, -.35, -.22, trim,
        center=(3.3075, 0), bevel=.004)
    box(g, 'warm_timber_soffit', .33, 2, -.345, -.325, wood,
        center=(3.145, 0), bevel=.002)
    return finish(config, g, ['roof', 'trim', 'wood'])


def build_roof_ridge(config):
    """Closed 2 m ridge cap; origin is the same ridge baseline as each half."""
    g = G()
    _xz_prism(g, 'single_closed_ridge_cap',
              [(-.13, 1.73), (-.13, 1.80), (0, 1.90),
               (.13, 1.80), (.13, 1.73), (0, 1.81)],
              -1, 1, 0)
    return finish(config, g, ['roof'])


def build_gable_end(config):
    """6 m triangular wall infill, exterior -Y; independent of hidden roof.

    Origin is the wall top at the gable centre.  Structural triangle is
    X +/-3, Z 0..1.8, Y +/- .09.  Trim projects to X +/-3.04 and Y -.171.
    The small round louver is opaque decoration, not a window or portal.
    """
    g = G()
    siding, trim, interior, roof = 0, 1, 2, 3
    vertices = [(-3, -.09, 0), (3, -.09, 0), (0, -.09, 1.8),
                (-3, .09, 0), (3, .09, 0), (0, .09, 1.8)]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1),
             (1, 4, 5, 2), (2, 5, 3, 0)]
    g.part('closed_gable_wall', vertices, faces,
           [siding, interior, interior, interior, interior])
    for i in range(8):
        lower, upper = i * .225, min((i + 1) * .225, 1.794)
        lower_half = 3 * (1 - lower / 1.8)
        upper_half = 3 * (1 - upper / 1.8)
        g.loft(f'gable_clapboard_{i:02}',
               [[(-lower_half, -.116, lower), (lower_half, -.116, lower),
                 (lower_half, -.082, lower), (-lower_half, -.082, lower)],
                [(-upper_half, -.104, upper), (upper_half, -.104, upper),
                 (upper_half, -.082, upper), (-upper_half, -.082, upper)]],
               siding)
    box(g, 'gable_belt_trim', 6.08, .06, 0, .055, trim,
        center=(0, -.113), bevel=.003)
    _round_vent(g, 1.15, roof, trim)
    return finish(config, g, ['siding', 'trim', 'interior', 'roof'])


def build_gable_trim(config):
    """Open-centred chevron bargeboard; always belongs to the roof group.

    Origin is the gable baseline centre; rear instance rotates 180 degrees.
    Bounds X +/-3.35, Y -.13...025, Z -.37..1.865.  No gable wall fill.
    """
    g = G()
    _xz_prism(g, 'cream_chevron_bargeboard',
              [(-3.35, -.37), (0, 1.64), (3.35, -.37),
               (3.35, -.17), (0, 1.84), (-3.35, -.17)],
              -.12, .02, 0)
    _xz_prism(g, 'dark_chevron_drip_edge',
              [(-3.35, -.17), (0, 1.84), (3.35, -.17),
               (3.35, -.145), (0, 1.865), (-3.35, -.145)],
              -.13, .025, 1)
    return finish(config, g, ['trim', 'roof'])


def build_porch_canopy(config):
    """2 m X bay of shed roof: wall Y0/Z0 to front Y-2.25/Z-.4.

    Install at world Z3.1; front support datum is world Z2.7.  Bounds are
    X +/-1, Y -2.25..0, Z -.53...008.  Ends along X butt between modules.
    """
    g = G()
    roof, trim, wood = 0, 1, 2
    top = lambda y: y * .4 / 2.25
    _yz_prism(g, 'closed_shed_roof_substrate',
              [(0, 0), (-2.25, -.4), (-2.25, -.47), (0, -.07)],
              -1, 1, roof)
    for i in range(6):
        a, b = -i * 2.25 / 6, -(i + 1) * 2.25 / 6
        _yz_prism(g, f'broad_canopy_course_{i:02}',
                  [(a, top(a) - .002), (b, top(b) - .002),
                   (b, top(b) + .018), (a, top(a) + .008)],
                  -1, 1, roof)
    box(g, 'canopy_front_cream_fascia', 2, .075, -.53, -.41, trim,
        center=(0, -2.2075), bevel=.004)
    box(g, 'canopy_front_timber_soffit', 2, .24, -.515, -.495, wood,
        center=(0, -2.08), bevel=.002)
    return finish(config, g, ['roof', 'trim', 'wood'])
