"""Adversarial tests exercise actual GLB bytes, not mocked Blender results."""

import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from art_pipeline.validation import validate_bundle, validate_glb


def make_glb(document=None, binary=None):
    if document is None:
        document, binary = fixture()
    encoded = json.dumps(document, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    binary += b"\0" * (-len(binary) % 4)
    body = struct.pack("<I4s", len(encoded), b"JSON") + encoded
    body += struct.pack("<I4s", len(binary), b"BIN\0") + binary
    return struct.pack("<4sII", b"glTF", 2, len(body) + 12) + body


def fixture():
    a, b, c, d = (-1, 0, -1), (1, 0, -1), (0, 0, 1), (0, 2, 0)
    positions, normals = [], []
    for face in ((a, b, c), (a, d, b), (b, d, c), (c, d, a)):
        u = [face[1][k] - face[0][k] for k in range(3)]
        v = [face[2][k] - face[0][k] for k in range(3)]
        normal = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        length = math.sqrt(sum(x*x for x in normal))
        normals.extend([tuple(x/length for x in normal)] * 3)
        positions.extend(face)
    packed_positions = b"".join(struct.pack("<3f", *value) for value in positions)
    packed_normals = b"".join(struct.pack("<3f", *value) for value in normals)
    packed_indices = struct.pack("<12H", *range(12))
    binary = packed_positions + packed_normals + packed_indices
    document = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}],
                "nodes": [{"mesh": 0}], "meshes": [{"primitives": [
                    {"attributes": {"POSITION": 0, "NORMAL": 1}, "indices": 2, "material": 0}]}],
                "materials": [{"name": "paint"}], "buffers": [{"byteLength": len(binary)}],
                "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 144},
                                {"buffer": 0, "byteOffset": 144, "byteLength": 144},
                                {"buffer": 0, "byteOffset": 288, "byteLength": 24}],
                "accessors": [{"bufferView": 0, "componentType": 5126, "count": 12, "type": "VEC3",
                               "min": [-1, 0, -1], "max": [1, 2, 1]},
                              {"bufferView": 1, "componentType": 5126, "count": 12, "type": "VEC3"},
                              {"bufferView": 2, "componentType": 5123, "count": 12, "type": "SCALAR"}]}
    return document, binary


def make_png(width=16, height=16):
    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    pixels = (b"\0" + b"\x80\xc0\x40\xff" * width) * height
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")


class GlbValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "test.glb"

    def write(self, document=None, binary=None):
        self.path.write_bytes(make_glb(document, binary))
        return self.path

    def validate(self, dimensions=(2, 2, 2), budget=4, materials=("paint",)):
        return validate_glb(self.path, dimensions, budget, materials)

    def assert_bad(self, document, binary, message):
        self.write(document, binary)
        with self.assertRaisesRegex(ValueError, message):
            self.validate()

    def test_valid_metrics_use_actual_geometry_and_hash(self):
        self.write()
        result = self.validate()
        self.assertEqual(result["triangles"], 4)
        self.assertEqual(result["vertices"], 12)
        self.assertEqual(result["dimensionsMeters"], [2, 2, 2])
        self.assertEqual(result["bounds"], {"min": [-1, 0, -1], "max": [1, 2, 1]})
        self.assertEqual(result["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertTrue(result["windingNormalsConsistent"])
        json.dumps(result, allow_nan=False)

    def test_rejects_truncated_and_malformed_container(self):
        original = make_glb()
        broken = (b"", original[:11], original[:-1], original + b"junk",
                  b"bad!" + original[4:], original[:4] + struct.pack("<I", 1) + original[8:],
                  original[:12] + struct.pack("<I", 0xfffffffc) + original[16:])
        for raw in broken:
            with self.subTest(length=len(raw), prefix=raw[:8]):
                self.path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    self.validate()

    def test_rejects_malformed_json_types_as_valueerror(self):
        for key in ("asset", "accessors", "bufferViews", "materials", "meshes", "nodes", "scenes", "images"):
            document, binary = fixture()
            document[key] = [] if key == "asset" else "malformed"
            with self.subTest(key=key):
                self.assert_bad(document, binary, "array|asset.version")

    def test_missing_glb_is_valueerror(self):
        with self.assertRaisesRegex(ValueError, "Cannot read"):
            self.validate()

    def test_rejects_malformed_accessor_component_types(self):
        for key, value in (("type", []), ("componentType", []), ("componentType", 5126.0)):
            document, binary = fixture()
            document["accessors"][0][key] = value
            with self.subTest(key=key, value=value):
                self.assert_bad(document, binary, "type|integer")

    def test_checks_unused_accessor_bounds_and_data(self):
        document, binary = fixture()
        document["accessors"].append({"bufferView": 0, "componentType": 5126,
                                      "count": 99, "type": "VEC2"})
        self.assert_bad(document, binary, "bounds")

    def test_rejects_invalid_material_factors(self):
        for key, value in (("baseColorFactor", [1, 1, 2, 1]),
                           ("roughnessFactor", -0.1), ("metallicFactor", 1.1)):
            document, binary = fixture()
            document["materials"][0]["pbrMetallicRoughness"] = {key: value}
            with self.subTest(key=key):
                self.assert_bad(document, binary, r"Material .*\[0,1\]")

    def test_rejects_accessor_or_buffer_view_overrun(self):
        for mutation in (lambda d: d["bufferViews"][0].update(byteLength=1000),
                         lambda d: d["accessors"][0].update(count=13),
                         lambda d: d["accessors"][0].update(byteOffset=2),
                         lambda d: d["bufferViews"][0].update(byteStride=8),
                         lambda d: d["buffers"][0].update(byteLength=1)):
            document, binary = fixture()
            mutation(document)
            with self.subTest(document=document):
                self.assert_bad(document, binary, "bounds|aligned|stride|byteLength")

    def test_rejects_false_declared_position_bounds(self):
        document, binary = fixture()
        document["accessors"][0]["max"][0] = 0.5
        self.assert_bad(document, binary, "actual data")

    def test_rejects_bad_index_even_when_accessor_bounds_are_absent(self):
        document, binary = fixture()
        binary = binary[:288] + struct.pack("<H", 100) + binary[290:]
        self.assert_bad(document, binary, "index is out of range")

    def test_rejects_nonfinite_positions_and_normals(self):
        for location in (0, 144):
            for value in (float("nan"), float("inf"), float("-inf")):
                document, binary = fixture()
                binary = binary[:location] + struct.pack("<f", value) + binary[location + 4:]
                with self.subTest(location=location, value=value):
                    self.assert_bad(document, binary, "nonfinite")

    def test_rejects_degenerate_triangles(self):
        document, binary = fixture()
        binary = binary[:288] + struct.pack("<3H", 0, 0, 2) + binary[294:]
        self.assert_bad(document, binary, "degenerate")

    def test_rejects_reversed_winding(self):
        document, binary = fixture()
        binary = binary[:288] + struct.pack("<3H", 0, 2, 1) + binary[294:]
        self.assert_bad(document, binary, "winding")

    def test_rejects_missing_normals_and_authored_material(self):
        for mutation in (lambda p: p["attributes"].pop("NORMAL"),
                         lambda p: p.pop("material"),
                         lambda p: p.update(material=3)):
            document, binary = fixture()
            mutation(document["meshes"][0]["primitives"][0])
            self.assert_bad(document, binary, "NORMAL|material")

    def test_rejects_nonttriangle_empty_mesh_and_sparse_accessor(self):
        for mutate, message in ((lambda d: d["meshes"][0]["primitives"][0].update(mode=1), "triangle"),
                                (lambda d: d["meshes"][0].update(primitives=[]), "no primitives"),
                                (lambda d: d["accessors"][0].update(sparse={}), "Sparse")):
            document, binary = fixture()
            mutate(document)
            self.assert_bad(document, binary, message)

    def test_rejects_external_resources(self):
        for mutate in (lambda d: d["buffers"][0].update(uri="file:///secret.bin"),
                       lambda d: d.update(images=[{"uri": "https://example.com/texture.png"}])):
            document, binary = fixture()
            mutate(document)
            self.assert_bad(document, binary, "External")

    def test_rejects_dimension_material_budget_and_pivot_mismatches(self):
        self.write()
        for arguments, message in ((([1, 2, 2], 4, ["paint"]), "dimensions"),
                                   (([2, 2, 2], 3, ["paint"]), "budget"),
                                   (([2, 2, 2], 4, ["other"]), "Material")):
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(ValueError, message):
                    self.validate(*arguments)
        document, binary = fixture()
        document["nodes"][0]["translation"] = [0, 0.2, 0]
        self.assert_bad(document, binary, "pivot")

    def test_applies_nested_column_major_matrix_and_trs(self):
        document, binary = fixture()
        document["nodes"] = [{"translation": [0.5, 0, 0], "children": [1]},
                             {"mesh": 0, "matrix": [2, 0, 0, 0, 0, 3, 0, 0,
                                                      0, 0, 4, 0, -0.5, 0, 0, 1]}]
        self.write(document, binary)
        metrics = self.validate([4, 6, 8])
        self.assertEqual(metrics["bounds"]["min"], [-2, 0, -4])
        self.assertEqual(metrics["bounds"]["max"], [2, 6, 4])

    def test_applies_quaternion_rotation(self):
        document, binary = fixture()
        document["nodes"][0].update(rotation=[0, math.sqrt(0.5), 0, math.sqrt(0.5)])
        self.write(document, binary)
        self.assertEqual(self.validate()["triangles"], 4)

    def test_rejects_mirrored_singular_and_cycle_transforms(self):
        for mutate, message in ((lambda d: d["nodes"][0].update(scale=[-1, 1, 1]), "handedness"),
                                (lambda d: d["nodes"][0].update(scale=[1, 0, 1]), "singular"),
                                (lambda d: d["nodes"][0].update(children=[0]), "cycle")):
            document, binary = fixture()
            mutate(document)
            self.assert_bad(document, binary, message)

    def test_supports_interleaved_vertex_accessors(self):
        document, original = fixture()
        interleaved = b"".join(original[i*12:i*12+12] + original[144+i*12:156+i*12]
                               for i in range(12))
        binary = interleaved + original[288:]
        document["bufferViews"] = [{"buffer": 0, "byteLength": 288, "byteStride": 24},
                                   {"buffer": 0, "byteOffset": 288, "byteLength": 24}]
        document["accessors"][1].update(bufferView=0, byteOffset=12)
        document["accessors"][2].update(bufferView=1)
        self.write(document, binary)
        self.assertEqual(self.validate()["triangles"], 4)

    def test_multiple_mesh_instances_are_counted(self):
        document, binary = fixture()
        document["nodes"] = [{"mesh": 0, "translation": [-1, 0, 0]},
                             {"mesh": 0, "translation": [1, 0, 0]}]
        document["scenes"][0]["nodes"] = [0, 1]
        self.write(document, binary)
        result = self.validate([4, 2, 2], 8)
        self.assertEqual(result["triangles"], 8)
        self.assertEqual(result["meshInstances"], 2)


class BundleValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        model = self.directory / "fixture.glb"
        document, binary = fixture()
        names = ["metal", "edge", "glass", "fastener"]
        document["nodes"][0]["scale"] = [1, 4, 1]
        document["materials"] = [{"name": name} for name in names]
        document["accessors"][2]["count"] = 3
        document["accessors"].extend(dict(document["accessors"][2], byteOffset=offset)
                                     for offset in (6, 12, 18))
        document["meshes"][0]["primitives"] = [
            {"attributes": {"POSITION": 0, "NORMAL": 1}, "indices": 2 + i, "material": i}
            for i in range(4)]
        model.write_bytes(make_glb(document, binary))
        for name in ("front", "isometric"):
            (self.directory / f"{name}.png").write_bytes(make_png(128, 128))
        config = {"schemaVersion": "1.0", "requestId": "ART-001", "assetId": "fixture",
                  "version": "0.1.0", "category": "test", "generator": "streetlamp", "seed": 123,
                  "dimensionsMeters": [2, 8, 2], "maxTriangles": 100, "blenderVersion": "4.5.14",
                  "palette": {name: {"color": "#808080", "roughness": 0.5, "metallic": 0.2}
                              for name in names}, "preview": {"resolution": 128, "samples": 1}}
        self.manifest = {
            "schemaVersion": "1.0", "requestId": "ART-001", "assetId": "fixture",
            "version": "0.1.0", "category": "test", "sourceCommit": "0"*40,
            "sourceDigest": "a"*64, "sourceDirty": False, "seed": 123, "config": config,
            "configSHA256": hashlib.sha256(json.dumps(config, sort_keys=True,
                                                       separators=(",", ":")).encode()).hexdigest(),
            "units": "meters", "axes": {"sourceUp": "+Z", "sourceForward": "-Y",
                                             "exportUp": "+Y", "exportForward": "+Z"},
            "pivot": "bottom-center", "dimensionsMeters": [2, 8, 2], "maxTriangles": 100,
            "model": {"file": "fixture.glb", "sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
                      "bytes": model.stat().st_size},
            "geometry": validate_glb(model, [2, 8, 2], 100), "materials": names,
            "previews": {name: {"file": f"{name}.png",
                                 "sha256": hashlib.sha256((self.directory / f"{name}.png").read_bytes()).hexdigest()}
                         for name in ("front", "isometric")},
            "provenance": {"method": "procedural-blender-python", "thirdPartyAssets": [],
                           "generator": "art_pipeline/blender_build.py"},
            "tooling": {"blender": "4.5.14", "python": "3.11", "engine": "CYCLES", "device": "CPU"},
            "command": "python -m art_pipeline build --seed 123"}

    def validate(self):
        (self.directory / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        return validate_bundle(self.directory)

    def test_valid_bundle_has_independent_geometry_and_preview_metrics(self):
        result = self.validate()
        self.assertTrue(result["valid"])
        self.assertEqual(result["assetId"], "fixture")
        self.assertEqual(result["previews"]["front"]["width"], 128)

    def test_rejects_tampered_glb_and_preview_checksums(self):
        for filename in ("fixture.glb", "front.png"):
            path = self.directory / filename
            original = path.read_bytes()
            path.write_bytes(original + b"tampered")
            with self.subTest(filename=filename):
                with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                    self.validate()
            path.write_bytes(original)

    def test_rejects_corrupt_png_even_with_updated_checksum(self):
        path = self.directory / "front.png"
        original = path.read_bytes()
        for raw in (b"not PNG", original[:-4], original[:40] + b"bad!" + original[44:]):
            path.write_bytes(raw)
            self.manifest["previews"]["front"]["sha256"] = hashlib.sha256(raw).hexdigest()
            with self.subTest(length=len(raw)):
                with self.assertRaisesRegex(ValueError, "PNG"):
                    self.validate()

    def test_rejects_stale_metrics_config_and_false_provenance(self):
        original = copy.deepcopy(self.manifest)
        mutations = ((lambda m: m["geometry"].update(triangles=100), "metrics"),
                     (lambda m: m["config"].update(dimensionsMeters=[3, 12, 3]), "configSHA256"),
                     (lambda m: m["provenance"].update(thirdPartyAssets=["asset-pack"]), "procedural"),
                     (lambda m: m["axes"].update(exportUp="+Z"), "axes"))
        for mutate, message in mutations:
            self.manifest = copy.deepcopy(original)
            mutate(self.manifest)
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    self.validate()

    def test_rejects_top_level_config_contradictions(self):
        original = copy.deepcopy(self.manifest)
        for key, value in (("assetId", "renamed"), ("version", "9.0.0"),
                           ("requestId", "ART-002"), ("category", "different"), ("seed", 999),
                           ("dimensionsMeters", [2, 8.001, 2]), ("maxTriangles", 999)):
            self.manifest = copy.deepcopy(original)
            self.manifest[key] = value
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "embedded config"):
                    self.validate()

    def test_rejects_tooling_version_and_preview_resolution_mismatches(self):
        self.manifest["tooling"]["blender"] = "4.5.13"
        with self.assertRaisesRegex(ValueError, "Blender version"):
            self.validate()
        self.manifest["tooling"]["blender"] = "4.5.14"
        path = self.directory / "front.png"
        path.write_bytes(make_png(256, 256))
        self.manifest["previews"]["front"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "resolution"):
            self.validate()

    def test_rejects_invalid_embedded_config_even_with_updated_hash(self):
        self.manifest["config"]["palette"]["metal"]["roughness"] = -1
        self.manifest["configSHA256"] = hashlib.sha256(json.dumps(
            self.manifest["config"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "Material values"):
            self.validate()

    def test_rejects_escaped_and_missing_files(self):
        self.manifest["model"]["file"] = "../fixture.glb"
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.validate()
        self.manifest["model"]["file"] = "missing.glb"
        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.validate()

    def test_requires_both_views(self):
        del self.manifest["previews"]["isometric"]
        with self.assertRaisesRegex(ValueError, "isometric"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
