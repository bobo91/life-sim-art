"""Pure tests for ART-002 comparison controls; these do not launch Blender."""

import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest

from art_pipeline.config import load_config
from scripts.render_benchmark import (PALETTES, ROOT, compare_manifests, derive_configs,
                                      geometry_fingerprint, load_library, run_benchmark,
                                      validate_library)


def library_fixture():
    materials = load_config(ROOT / "configs/streetlamp.json")["palette"]
    library = {"schemaVersion": "1.0", "palettes": {
        name: {"description": name.replace("_", " "), "materials": copy.deepcopy(materials)}
        for name in PALETTES}}
    library["palettes"]["harbor_slate"]["materials"]["metal"]["color"] = "#405060"
    return library


def comparison_fixture():
    configs = derive_configs(load_config(ROOT / "configs/streetlamp.json"), library_fixture())
    geometry = {"triangles": 520, "vertices": 992, "meshInstances": 1,
                "bounds": {"min": [-.32, 0, -.32], "max": [.32, 3.2, .32]},
                "dimensionsMeters": [.64, 3.2, .64]}
    manifests = {name: {"config": copy.deepcopy(configs[name]),
                        "sourceCommit": "0"*40, "sourceDigest": "1"*64, "sourceDirty": False,
                        "tooling": {"blender": "4.5.14", "engine": "CYCLES", "device": "CPU"},
                        "geometry": copy.deepcopy(geometry), "model": {"sha256": str(index)*64},
                        "previews": {"front": {"sha256": str(index+2)*64},
                                     "isometric": {"sha256": str(index+4)*64}}}
                 for index, name in enumerate(PALETTES)}
    return configs, manifests, {name: "a"*64 for name in PALETTES}


def geometry_fixture():
    positions = [(-1, 0, 0), (1, 0, 0), (0, 1, 0)]
    normals = [(0, 0, 1)]*3
    binary = b"".join(struct.pack("<3f", *v) for v in positions + normals) + struct.pack("<3H", 0, 1, 2)
    document = {"asset": {"version": "2.0"}, "nodes": [{"mesh": 0, "name": "original"}],
                "meshes": [{"name": "mesh", "primitives": [
                    {"attributes": {"POSITION": 0, "NORMAL": 1}, "indices": 2, "material": 0}]}],
                "materials": [{"name": "paint", "pbrMetallicRoughness": {"baseColorFactor": [1, 0, 0, 1]}}],
                "buffers": [{"byteLength": len(binary)}],
                "bufferViews": [{"buffer": 0, "byteLength": 36},
                                {"buffer": 0, "byteOffset": 36, "byteLength": 36},
                                {"buffer": 0, "byteOffset": 72, "byteLength": 6}],
                "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
                               "min": [-1, 0, 0], "max": [1, 1, 0]},
                              {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
                              {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"}]}
    return document, binary


def write_glb(path, document, binary):
    encoded = json.dumps(document).encode()
    encoded += b" " * (-len(encoded) % 4)
    binary += b"\0" * (-len(binary) % 4)
    body = struct.pack("<I4s", len(encoded), b"JSON") + encoded
    body += struct.pack("<I4s", len(binary), b"BIN\0") + binary
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, len(body)+12) + body)


class LibraryTests(unittest.TestCase):
    def test_library_requires_real_material_variants_and_valid_pbr_specs(self):
        library = library_fixture()
        self.assertEqual(validate_library(library), library)
        mutations = (
            lambda d: d.update(schemaVersion="2.0"),
            lambda d: d["palettes"].pop("harbor_slate"),
            lambda d: d["palettes"]["civic_sage"].update(description=" "),
            lambda d: d["palettes"]["civic_sage"]["materials"].pop("metal"),
            lambda d: d["palettes"]["civic_sage"]["materials"]["metal"].update(color="red"),
            lambda d: d["palettes"]["civic_sage"]["materials"]["metal"].update(roughness=float("nan")),
            lambda d: d["palettes"]["civic_sage"]["materials"]["metal"].update(metallic=True),
            lambda d: d["palettes"]["civic_sage"]["materials"]["metal"].update(metallic=1.1),
            lambda d: d["palettes"]["civic_sage"]["materials"]["metal"].update(roughness=.65),
            lambda d: d["palettes"]["harbor_slate"].update(materials=d["palettes"]["civic_sage"]["materials"]),
        )
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(library)
            mutate(bad)
            with self.subTest(mutation=index):
                with self.assertRaises(ValueError):
                    validate_library(bad)

    def test_file_loader_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "library.json"
            path.write_text('{"schemaVersion":"1.0","schemaVersion":"1.0"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load_library(path)

    def test_derived_configs_preserve_geometry_and_isolate_callers(self):
        base = load_config(ROOT / "configs/streetlamp.json")
        library = library_fixture()
        original_base, original_library = copy.deepcopy(base), copy.deepcopy(library)
        configs = derive_configs(base, library)
        for name, config in configs.items():
            self.assertEqual(config["assetId"], "prop_streetlamp_benchmark_" + name)
            self.assertEqual(config["requestId"], "ART-002")
            self.assertEqual(config["version"], "0.1.0")
            self.assertEqual(config["preview"], {"resolution": 640, "samples": 64})
            for key in ("seed", "dimensionsMeters", "maxTriangles", "blenderVersion", "generator"):
                self.assertEqual(config[key], base[key])
        configs["civic_sage"]["palette"]["metal"]["color"] = "#FFFFFF"
        configs["civic_sage"]["dimensionsMeters"][0] = 100
        self.assertEqual(base, original_base)
        self.assertEqual(library, original_library)

    def test_reference_seed_is_explicit(self):
        base = load_config(ROOT / "configs/streetlamp.json")
        base["seed"] += 1
        with self.assertRaisesRegex(ValueError, "1701"):
            derive_configs(base, library_fixture())


class ComparisonTests(unittest.TestCase):
    def test_matching_geometry_and_different_actual_outputs_pass(self):
        configs, manifests, hashes = comparison_fixture()
        result = compare_manifests(manifests, configs, hashes)
        self.assertTrue(result["sameGeometry"])
        self.assertEqual(result["geometrySHA256"], "a"*64)
        self.assertEqual(result["controls"]["preview"]["samples"], 64)

    def test_rejects_uncontrolled_source_tools_and_geometry(self):
        mutations = (
            (lambda m: m.update(sourceCommit="2"*40), "sourceCommit"),
            (lambda m: m.update(sourceDigest="2"*64), "sourceDigest"),
            (lambda m: m["tooling"].update(blender="4.5.13"), "tooling"),
            (lambda m: m["geometry"].update(triangles=521), "triangles"),
            (lambda m: m["geometry"]["bounds"]["max"].__setitem__(1, 3.201), "bounds"),
        )
        for mutate, message in mutations:
            configs, manifests, hashes = comparison_fixture()
            mutate(manifests["harbor_slate"])
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    compare_manifests(manifests, configs, hashes)

    def test_rejects_actual_config_disagreement_and_controlled_seed_changes(self):
        configs, manifests, hashes = comparison_fixture()
        manifests["harbor_slate"]["config"]["seed"] += 1
        with self.assertRaisesRegex(ValueError, "requested palette"):
            compare_manifests(manifests, configs, hashes)
        configs["harbor_slate"]["seed"] += 1
        with self.assertRaisesRegex(ValueError, "controls differ"):
            compare_manifests(manifests, configs, hashes)

    def test_same_bounds_and_counts_do_not_hide_different_vertices(self):
        configs, manifests, hashes = comparison_fixture()
        hashes["harbor_slate"] = "b"*64
        with self.assertRaisesRegex(ValueError, "positions, normals or topology"):
            compare_manifests(manifests, configs, hashes)

    def test_requires_actual_glb_and_render_differences(self):
        for output in ("model", "front", "isometric"):
            configs, manifests, hashes = comparison_fixture()
            a, b = (manifests[name] for name in PALETTES)
            if output == "model":
                b["model"] = copy.deepcopy(a["model"])
            else:
                b["previews"][output] = copy.deepcopy(a["previews"][output])
            with self.subTest(output=output):
                with self.assertRaisesRegex(ValueError, "different GLB|identical"):
                    compare_manifests(manifests, configs, hashes)

    def test_existing_output_is_retained_before_any_input_or_blender_access(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            marker = output / "keep.txt"
            marker.write_text("previous work", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "new or empty"):
                run_benchmark(output, blender="missing", library_path="missing.json")
            self.assertEqual(marker.read_text(encoding="utf-8"), "previous work")


class GeometryFingerprintTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "fixture.glb"

    def fingerprint(self, document, binary):
        write_glb(self.path, document, binary)
        return geometry_fingerprint(self.path)

    def test_ignores_names_and_pbr_but_detects_position_normal_and_index_changes(self):
        document, binary = geometry_fixture()
        baseline = self.fingerprint(document, binary)
        document["nodes"][0]["name"] = "renamed"
        document["meshes"][0]["name"] = "another name"
        document["materials"][0]["pbrMetallicRoughness"]["baseColorFactor"] = [0, 0, 1, 1]
        self.assertEqual(self.fingerprint(document, binary), baseline)
        document["accessors"][0]["min"][0] = -.75
        self.assertNotEqual(self.fingerprint(document, struct.pack("<f", -.75)+binary[4:]), baseline)
        document, binary = geometry_fixture()
        changed_normal = binary[:36] + struct.pack("<3f", 0, 1, 0) + binary[48:]
        self.assertNotEqual(self.fingerprint(document, changed_normal), baseline)
        self.assertNotEqual(self.fingerprint(document, binary[:72]+struct.pack("<3H", 0, 2, 1)), baseline)

    def test_digest_uses_decoded_indices_instead_of_storage_width(self):
        document, binary = geometry_fixture()
        baseline = self.fingerprint(document, binary)
        document["accessors"][2]["componentType"] = 5125
        document["bufferViews"][2]["byteLength"] = 12
        document["buffers"][0]["byteLength"] = 84
        self.assertEqual(self.fingerprint(document, binary[:72]+struct.pack("<3I", 0, 1, 2)), baseline)

    def test_refuses_transformed_geometry_outside_baked_benchmark_scope(self):
        document, binary = geometry_fixture()
        document["nodes"][0]["translation"] = [0, 1, 0]
        with self.assertRaisesRegex(ValueError, "identity-transform"):
            self.fingerprint(document, binary)


if __name__ == "__main__":
    unittest.main()
