import copy
import json
import tempfile
import unittest
from pathlib import Path

from art_pipeline.config import canonical_json, load_config

ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "configs/streetlamp.json").read_text())

    def load(self, config):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            return load_config(path)

    def test_sample_valid(self):
        self.assertEqual(self.load(self.config), self.config)

    def test_canonical_hash_input_ignores_key_order(self):
        self.assertEqual(canonical_json({"a": 1, "b": 2}), canonical_json({"b": 2, "a": 1}))

    def test_reject_invalid_config(self):
        for key, value in (("seed", True), ("seed", -1), ("assetId", "../escape"),
                           ("dimensionsMeters", [1, float("nan"), 1]), ("dimensionsMeters", [1, 0, 1]),
                           ("maxTriangles", 0), ("blenderVersion", "latest"),
                           ("preview", {"resolution": 0, "samples": 32})):
            with self.subTest(key=key, value=value):
                config = copy.deepcopy(self.config)
                config[key] = value
                with self.assertRaises((ValueError, TypeError)):
                    self.load(config)

    def test_reject_unknown_key_and_unbounded_material(self):
        config = copy.deepcopy(self.config)
        config["import_mesh"] = "untrusted.glb"
        with self.assertRaises(ValueError):
            self.load(config)
        config = copy.deepcopy(self.config)
        config["palette"]["metal"]["roughness"] = 2
        with self.assertRaises(ValueError):
            self.load(config)


if __name__ == "__main__":
    unittest.main()
