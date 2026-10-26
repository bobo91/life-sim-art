"""Bounded module/layout contracts; no Blender installation required.

These tests inspect the authored inventory and capture the actual wall
builder's closed-prism calls. Render/GLB geometry checks remain the separate
Blender production validation, rather than being implied by this suite.
"""

import importlib.util
import json
import math
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = {
    'bld_wall_solid_200_001', 'bld_wall_window_200_001',
    'bld_wall_door_200_001', 'bld_corner_trim_001',
    'bld_floor_200_001', 'bld_foundation_200_001',
    'bld_porch_200_001', 'bld_porch_steps_001', 'bld_porch_post_001',
    'bld_roof_half_200_001', 'bld_roof_ridge_200_001',
    'bld_gable_end_600_001', 'bld_gable_trim_600_001',
    'bld_porch_canopy_200_001', 'bld_window_110_001', 'bld_door_100_001',
}


class CapturedPrisms:
    """Capture bounds, not a substitute mesh generator or validator."""
    def __init__(self):
        self.parts = []

    def loft(self, name, loops, *_args, **_kwargs):
        points = [point for loop in loops for point in loop]
        self.parts.append((name, [min(p[k] for p in points) for k in range(3)],
                           [max(p[k] for p in points) for k in range(3)]))


def capture_box(g, name, width, depth, zmin, zmax, _material,
                center=(0, 0), **_kwargs):
    g.parts.append((name, [center[0] - width / 2, center[1] - depth / 2, zmin],
                   [center[0] + width / 2, center[1] + depth / 2, zmax]))


def captured_wall(opening):
    """Run production wall() with only its geometry sink replaced."""
    geometry = types.ModuleType('building_geometry')
    geometry.G = CapturedPrisms
    geometry.box = capture_box
    geometry.beam = lambda *_args, **_kwargs: None
    geometry.finish = lambda _config, g, _roles: {'prisms': g.parts}
    spec = importlib.util.spec_from_file_location(
        '_modular_building_core_contract_test', ROOT / 'scripts/building_core.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'building_geometry': geometry}):
        spec.loader.exec_module(module)
    return module.wall({}, opening)


def intersects_volume(a_min, a_max, b_min, b_max):
    return all(min(a_max[k], b_max[k]) - max(a_min[k], b_min[k]) > 1e-8
               for k in range(3))


class ModularBuildingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / 'configs/modular-building.json').read_text(encoding='utf-8'))
        cls.assets = {asset['assetId']: asset for asset in cls.config['assets']}

    def test_bounded_unique_inventory_and_authored_bounds(self):
        self.assertEqual(len(self.config['assets']), 16)
        self.assertEqual(set(self.assets), EXPECTED_IDS)
        for asset_id, asset in self.assets.items():
            with self.subTest(asset=asset_id):
                self.assertEqual(asset['anchor'], 'authored-module-anchor')
                self.assertIsInstance(asset['seed'], int)
                self.assertGreater(asset['maxTriangles'], 0)
                minimum, maximum = (asset['expectedBounds'][key] for key in ('min', 'max'))
                dimensions = asset['dimensionsMeters']
                self.assertEqual([len(minimum), len(maximum), len(dimensions)], [3, 3, 3])
                self.assertTrue(all(math.isfinite(v) for v in minimum + maximum + dimensions))
                for low, high, span in zip(minimum, maximum, dimensions):
                    self.assertGreater(span, 0)
                    self.assertAlmostEqual(high - low, span, places=6)

    def test_grid_spans_and_walkable_floor_datum(self):
        config, assets = self.config, self.assets
        self.assertEqual(config['gridMeters'], 2)
        for asset_id in ('bld_wall_solid_200_001', 'bld_wall_window_200_001',
                         'bld_wall_door_200_001', 'bld_floor_200_001',
                         'bld_foundation_200_001', 'bld_porch_200_001',
                         'bld_porch_canopy_200_001'):
            self.assertEqual(assets[asset_id]['dimensionsMeters'][0], config['gridMeters'])
        for asset_id in ('bld_roof_half_200_001', 'bld_roof_ridge_200_001'):
            self.assertEqual(assets[asset_id]['dimensionsMeters'][2], config['gridMeters'])
        floor_thickness = assets['bld_floor_200_001']['dimensionsMeters'][1]
        foundation_height = assets['bld_foundation_200_001']['dimensionsMeters'][1]
        self.assertAlmostEqual(foundation_height + floor_thickness, config['floorLevelMeters'])
        self.assertAlmostEqual(assets['bld_porch_200_001']['dimensionsMeters'][1],
                               config['floorLevelMeters'])
        self.assertAlmostEqual(assets['bld_porch_steps_001']['dimensionsMeters'][1],
                               config['floorLevelMeters'])

    def test_layout_door_and_porch_align_on_reused_bays(self):
        grid = self.config['gridMeters']
        layouts = self.config['houses']
        self.assertEqual(set(layouts), {'walter', 'alternate'})
        self.assertNotEqual(layouts['walter'], layouts['alternate'])
        for name, house in layouts.items():
            with self.subTest(house=name):
                self.assertEqual(house['widthMeters'], self.config['roofSpanMeters'])
                self.assertEqual(house['widthMeters'] % grid, 0)
                self.assertEqual(house['lengthMeters'] % grid, 0)
                front = house['frontWallModules']
                self.assertEqual(len(front) * grid, house['widthMeters'])
                self.assertEqual(front.count('door'), 1)
                for kind in front:
                    self.assertIn('bld_wall_' + kind + '_200_001', self.assets)
                door_index = front.index('door')
                door_x = -house['widthMeters'] / 2 + grid / 2 + door_index * grid
                self.assertEqual(house['doorCenterX'], door_x)
                self.assertIn(door_x, house['porchCentersX'])
                valid_front_centres = {
                    -house['widthMeters'] / 2 + grid / 2 + i * grid
                    for i in range(len(front))}
                self.assertTrue(set(house['porchCentersX']) <= valid_front_centres)
                side_bay_count = house['lengthMeters'] // grid
                self.assertTrue(all(0 <= bay < side_bay_count
                                    for bay in house['sideWindowBays']))

    def test_doorway_is_real_hole_through_wall_geometry(self):
        wall = captured_wall((0, 2.20))
        clear_min, clear_max = [-.495, -.2, .015], [.495, .2, 2.135]
        for name, minimum, maximum in wall['prisms']:
            self.assertFalse(intersects_volume(minimum, maximum, clear_min, clear_max),
                             f'{name} obstructs the documented door-frame passage')

    def test_window_hole_and_cladding_meet_at_actual_sill_and_header(self):
        wall = captured_wall((.85, 2.10))
        for name, minimum, maximum in wall['prisms']:
            self.assertFalse(intersects_volume(minimum, maximum,
                                               [-.54, -.2, .85], [.54, .2, 2.10]),
                             f'{name} obstructs the window-wall hole')
        # These solid facade strips must retain siding even when the opening
        # intersects a course partway through its 200 mm height.
        for z in (.825, 2.15):
            covered = any(name.startswith('clapboard_')
                          and minimum[0] < 0 < maximum[0]
                          and minimum[1] < -.103 < maximum[1]
                          and minimum[2] < z < maximum[2]
                          for name, minimum, maximum in wall['prisms'])
            self.assertTrue(covered, f'Missing central facade siding at Z={z}')

    def test_collision_contract_keeps_openings_and_leaf_separate(self):
        # Proposals are a written art contract, not delivered Unity colliders.
        policy = self.config['collisionPolicy'].lower()
        self.assertIn('excluding openings', policy)
        self.assertIn('no house-wide solid boxcollider', policy)
        self.assertIn('door leaf separate', policy)
        self.assertFalse(self.config['gameRepositoryChanged'])
        self.assertFalse(self.config['mergeAuthorized'])

    def test_machine_readable_wall_collision_preserves_openings(self):
        for kind, bottom, top in (('door', 0, 2.20), ('window', .85, 2.10)):
            asset = self.assets['bld_wall_' + kind + '_200_001']
            proposal = asset['collisionProposal']
            self.assertEqual(proposal['type'], 'compound-boxes')
            boxes = proposal['boxes']
            self.assertTrue(boxes)
            for box_ in boxes:
                minimum, maximum = box_['minSourceXYZ'], box_['maxSourceXYZ']
                self.assertEqual([len(minimum), len(maximum)], [3, 3])
                self.assertTrue(all(math.isfinite(v) for v in minimum + maximum))
                self.assertTrue(all(minimum[k] < maximum[k] for k in range(3)))
                self.assertFalse(intersects_volume(minimum, maximum,
                                                   [-.55, -.10, bottom], [.55, .10, top]))
            # A vacuous empty/thin collision definition must not pass simply
            # because it leaves the doorway free: piers and lintel still block.
            probes = [(-.8, 0, 1), (.8, 0, 1), (0, 0, 2.5)]
            if bottom > 0:
                probes.append((0, 0, .4))
            for point in probes:
                self.assertTrue(any(all(box_['minSourceXYZ'][k] < point[k]
                                        < box_['maxSourceXYZ'][k] for k in range(3))
                                    for box_ in boxes))


if __name__ == '__main__':
    unittest.main()
