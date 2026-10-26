"""Actual GLB regressions for authored anchors and untouched production bytes."""

import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from scripts.building_validation import validate_building_glb
from tests.test_validation import fixture, make_glb


def offset_fixture(offset=(2, -1, -3)):
    document, binary = fixture()
    positions = [struct.unpack_from("<3f", binary, position * 12) for position in range(12)]
    shifted = [tuple(point[k] + offset[k] for k in range(3)) for point in positions]
    binary = b"".join(struct.pack("<3f", *point) for point in shifted) + binary[144:]
    bounds = {bound: [operation(point[k] for point in shifted) for k in range(3)]
              for bound, operation in (("min", min), ("max", max))}
    document["accessors"][0].update(bounds)
    return document, binary, bounds


class BuildingValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "module.glb"
        self.document, self.binary, self.bounds = offset_fixture()

    def write(self):
        self.path.write_bytes(make_glb(self.document, self.binary))

    def validate(self, dimensions=(2, 2, 2), bounds=None, budget=4, materials=("paint",)):
        return validate_building_glb(self.path, dimensions, budget, materials,
                                     self.bounds if bounds is None else bounds)

    def test_offset_anchor_preserves_input_and_reports_original_metrics(self):
        self.write()
        original = self.path.read_bytes()
        metrics = self.validate()
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(metrics["sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(metrics["bytes"], len(original))
        self.assertEqual(metrics["bounds"], self.bounds)
        self.assertEqual(metrics["dimensionsMeters"], [2, 2, 2])
        self.assertEqual(metrics["triangles"], 4)
        self.assertEqual(metrics["pivotPolicy"], "authored-module-anchor")
        self.assertEqual(metrics["anchorBoundsErrorMeters"], [0, 0, 0])
        self.assertEqual(metrics["validationNormalization"]["translationMeters"], [-2, 1, 3])

    def test_configured_normalization_does_not_hide_wrong_source_origin(self):
        for shift in ((0.002, 0, 0), (0, 0.002, 0), (0, 0, 0.002), (0.1, 0, 0)):
            offset = tuple(base + change for base, change in zip((2, -1, -3), shift))
            self.document, self.binary, _actual = offset_fixture(offset)
            self.write()
            with self.subTest(shift=shift), self.assertRaisesRegex(ValueError, "bounds|pivot"):
                self.validate()

    def test_rejects_wrong_configured_bounds_and_dimensions(self):
        self.write()
        wrong_bounds = {"min": [value + 0.003 for value in self.bounds["min"]],
                        "max": [value + 0.003 for value in self.bounds["max"]]}
        with self.assertRaisesRegex(ValueError, "bounds|pivot"):
            self.validate(bounds=wrong_bounds)
        with self.assertRaisesRegex(ValueError, "expected_dimensions"):
            self.validate(dimensions=(2.003, 2, 2))

    def test_requires_exactly_one_identity_root(self):
        for change in ({"translation": [0.002, 0, 0]}, {"scale": [1.1, 1, 1]},
                       {"rotation": [0, 0, 1, 0]},
                       {"matrix": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0.002, 0, 0, 1]}):
            self.document, self.binary, _bounds = offset_fixture()
            self.document["nodes"][0].update(change)
            self.write()
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "root.*identity"):
                self.validate()
        self.document, self.binary, _bounds = offset_fixture()
        self.document["nodes"].append({"mesh": 0})
        self.document["scenes"][0]["nodes"] = [0, 1]
        self.write()
        with self.assertRaisesRegex(ValueError, "exactly one identity root"):
            self.validate()

    def test_empty_identity_root_with_child_hinge_transform_is_allowed(self):
        self.document["nodes"] = [{"name": "module-root", "children": [1]},
                                  {"name": "hinge", "translation": [0.5, 0, 0], "children": [2]},
                                  {"mesh": 0}]
        self.bounds = {bound: [point[0] + 0.5, point[1], point[2]]
                       for bound, point in self.bounds.items()}
        self.write()
        self.assertEqual(self.validate()["bounds"], self.bounds)

    def test_shared_geometry_material_and_budget_checks_still_run(self):
        self.write()
        with self.assertRaisesRegex(ValueError, "Triangle budget"):
            self.validate(budget=3)
        with self.assertRaisesRegex(ValueError, "Material names"):
            self.validate(materials=("unexpected",))
        self.binary = self.binary[:288] + struct.pack("<H", 100) + self.binary[290:]
        self.write()
        with self.assertRaisesRegex(ValueError, "index is out of range"):
            self.validate()

    def test_rejects_degenerate_bounds_and_conflicting_root_transform_forms(self):
        self.write()
        with self.assertRaisesRegex(ValueError, "positive extents"):
            self.validate(bounds={"min": [0, 0, 0], "max": [0, 2, 2]})
        self.document["nodes"][0].update(matrix=[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                                          translation=[0, 0, 0])
        self.write()
        with self.assertRaisesRegex(ValueError, "combine matrix and TRS"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
