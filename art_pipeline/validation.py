"""Independent, dependency-free validation of the delivered glTF 2.0 bundle.

Positions are measured after the active glTF scene's transforms, in meters and
the exported +Y-up frame. Blender's source -Y forward becomes glTF +Z forward.
Semantic forward cannot be inferred from arbitrary geometry; bundle provenance
records that convention and winding/normal checks detect inverted geometry.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import struct
import zlib


DIMENSION_TOLERANCE = 0.01
PIVOT_TOLERANCE = 0.01
_IDENTITY = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0,
             0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
_COMPONENTS = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2),
               5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
_WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
           "MAT2": 4, "MAT3": 9, "MAT4": 16}


def _fail(message):
    raise ValueError(message)


def _integer(value, label, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail(f"{label} must be an integer >= {minimum}")
    return value


def _numbers(values, count, label):
    if not isinstance(values, (list, tuple)) or len(values) != count:
        _fail(f"{label} must have {count} components")
    try:
        if any(isinstance(v, bool) or not isinstance(v, (int, float))
               or not math.isfinite(v) for v in values):
            _fail(f"{label} contains a nonfinite or nonnumeric value")
        return tuple(float(v) for v in values)
    except OverflowError:
        _fail(f"{label} contains a value outside finite floating-point range")


def _entry(items, index, label):
    _integer(index, label)
    if not isinstance(items, list) or index >= len(items):
        _fail(f"{label} is out of range")
    entry = items[index]
    if not isinstance(entry, dict):
        _fail(f"{label} must reference an object")
    return entry


def _json(data, label):
    def reject_constant(value):
        _fail(f"{label} contains nonfinite JSON constant {value}")
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                _fail(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result
    try:
        result = json.loads(data, parse_constant=reject_constant,
                            object_pairs_hook=unique_keys)
    except (UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"{label} is not valid UTF-8 JSON: {exc}")
    if not isinstance(result, dict):
        _fail(f"{label} must be an object")
    def check_finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            _fail(f"{label} contains a nonfinite numeric value")
        if isinstance(value, dict):
            for nested in value.values():
                check_finite(nested)
        elif isinstance(value, list):
            for nested in value:
                check_finite(nested)
    check_finite(result)
    return result


def _read_glb(path):
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        _fail(f"Cannot read GLB file: {exc}")
    if len(raw) < 12:
        _fail("GLB header is truncated")
    magic, version, length = struct.unpack_from("<4sII", raw)
    if magic != b"glTF" or version != 2:
        _fail("Expected a GLB 2.0 header")
    if length != len(raw):
        _fail("GLB declared length does not match file length")
    cursor, document, binary = 12, None, None
    while cursor < length:
        if cursor + 8 > length:
            _fail("GLB chunk header is truncated")
        size, kind = struct.unpack_from("<I4s", raw, cursor)
        cursor += 8
        if size % 4 or cursor + size > length:
            _fail("GLB chunk has invalid alignment or exceeds file bounds")
        payload = raw[cursor:cursor + size]
        if document is None and kind != b"JSON":
            _fail("GLB JSON must be the first chunk")
        if kind == b"JSON":
            if document is not None:
                _fail("GLB contains duplicate JSON chunks")
            document = _json(payload, "GLB JSON")
        elif kind == b"BIN\x00":
            if binary is not None:
                _fail("GLB contains duplicate binary chunks")
            binary = payload
        cursor += size
    if document is None or binary is None:
        _fail("GLB requires JSON and binary chunks")
    if not isinstance(document.get("asset"), dict) or document["asset"].get("version") != "2.0":
        _fail("glTF asset.version must be 2.0")
    for key in ("accessors", "bufferViews", "images", "materials", "meshes", "nodes", "scenes"):
        if key in document and not isinstance(document[key], list):
            _fail(f"glTF {key} must be an array")
    if document.get("extensionsRequired"):
        _fail("Required glTF extensions are unsupported by this validator")
    buffers = document.get("buffers")
    if not isinstance(buffers, list) or len(buffers) != 1:
        _fail("GLB must contain exactly one embedded buffer")
    buffer = _entry(buffers, 0, "buffer")
    if "uri" in buffer:
        _fail("External or URI buffers are not permitted")
    declared = _integer(buffer.get("byteLength"), "buffer.byteLength", 1)
    if declared > len(binary) or len(binary) - declared > 3:
        _fail("Binary chunk and buffer.byteLength disagree")
    for index, view in enumerate(document.get("bufferViews", [])):
        if not isinstance(view, dict):
            _fail("bufferView must be an object")
        if _integer(view.get("buffer", 0), "bufferView.buffer") != 0:
            _fail("bufferView references an invalid buffer")
        start = _integer(view.get("byteOffset", 0), "bufferView.byteOffset")
        size = _integer(view.get("byteLength"), "bufferView.byteLength", 1)
        if start + size > declared:
            _fail(f"bufferView {index} exceeds buffer bounds")
        if "byteStride" in view:
            stride = _integer(view["byteStride"], "bufferView.byteStride", 4)
            if stride > 252 or stride % 4:
                _fail("bufferView.byteStride must be 4..252 and divisible by 4")
    for image in document.get("images", []):
        if not isinstance(image, dict):
            _fail("image must be an object")
        if "uri" in image:
            # Embedded data URIs are self-contained, never fetched from disk/network.
            if not isinstance(image["uri"], str) or not image["uri"].startswith("data:image/"):
                _fail("External images are not permitted")
        elif "bufferView" in image:
            _entry(document.get("bufferViews"), image["bufferView"], "image.bufferView")
        else:
            _fail("image has no embedded data")
    return raw, document, binary[:declared]


def _accessor(document, binary, index, expected_type, component_types, allow_normalized=False):
    accessor = _entry(document.get("accessors"), index, "accessor")
    if "sparse" in accessor:
        _fail("Sparse accessors are unsupported; export dense geometry")
    if accessor.get("type") != expected_type:
        _fail(f"accessor must have type {expected_type}")
    component = _integer(accessor.get("componentType"), "accessor.componentType")
    if component not in component_types:
        _fail("accessor has an invalid componentType")
    if not isinstance(accessor.get("normalized", False), bool):
        _fail("accessor.normalized must be boolean")
    if accessor.get("normalized", False) and not allow_normalized:
        _fail("POSITION, NORMAL, and index accessors cannot be normalized")
    if accessor.get("normalized", False) and component not in {5120, 5121, 5122, 5123}:
        _fail("Only byte and short accessors may be normalized")
    count = _integer(accessor.get("count"), "accessor.count", 1)
    view = _entry(document.get("bufferViews"), accessor.get("bufferView"), "accessor.bufferView")
    fmt, component_size = _COMPONENTS[component]
    width = _WIDTHS[expected_type]
    item_size = component_size * width
    stride = view.get("byteStride", item_size)
    offset = _integer(accessor.get("byteOffset", 0), "accessor.byteOffset")
    absolute = view.get("byteOffset", 0) + offset
    if offset % component_size or absolute % component_size:
        _fail("accessor offset is not aligned to its component size")
    if stride < item_size or stride % component_size:
        _fail("accessor stride is too small or misaligned")
    if offset + (count - 1) * stride + item_size > view["byteLength"]:
        _fail("accessor exceeds bufferView bounds")
    values = [struct.unpack_from("<" + fmt * width, binary, absolute + i * stride)
              for i in range(count)]
    if any(not math.isfinite(value) for row in values for value in row):
        _fail("accessor contains nonfinite coordinates or normals")
    for bound, operation in (("min", min), ("max", max)):
        if bound in accessor:
            declared = _numbers(accessor[bound], width, f"accessor.{bound}")
            actual = tuple(operation(row[k] for row in values) for k in range(width))
            if any(not math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-6)
                   for a, b in zip(declared, actual)):
                _fail(f"accessor.{bound} does not match its actual data")
    return values, accessor


def _multiply(a, b):
    return tuple(sum(a[k * 4 + row] * b[column * 4 + k] for k in range(4))
                 for column in range(4) for row in range(4))


def _transform(node):
    if "matrix" in node:
        if any(key in node for key in ("translation", "rotation", "scale")):
            _fail("node cannot combine matrix and TRS transforms")
        matrix = _numbers(node["matrix"], 16, "node.matrix")
        if any(abs(matrix[i]) > 1e-7 for i in (3, 7, 11)) or abs(matrix[15] - 1) > 1e-7:
            _fail("node.matrix must be affine")
        return matrix
    translation = _numbers(node.get("translation", [0, 0, 0]), 3, "node.translation")
    scale = _numbers(node.get("scale", [1, 1, 1]), 3, "node.scale")
    x, y, z, w = _numbers(node.get("rotation", [0, 0, 0, 1]), 4, "node.rotation")
    if abs(x*x + y*y + z*z + w*w - 1) > 1e-4:
        _fail("node.rotation quaternion must be normalized")
    rotation = (1 - 2*(y*y + z*z), 2*(x*y + z*w), 2*(x*z - y*w), 0,
                2*(x*y - z*w), 1 - 2*(x*x + z*z), 2*(y*z + x*w), 0,
                2*(x*z + y*w), 2*(y*z - x*w), 1 - 2*(x*x + y*y), 0,
                0, 0, 0, 1)
    matrix = list(rotation)
    for column in range(3):
        for row in range(3):
            matrix[column * 4 + row] *= scale[column]
    matrix[12:15] = translation
    return tuple(matrix)


def _point(matrix, point):
    return tuple(sum(matrix[column * 4 + row] * point[column] for column in range(3))
                 + matrix[12 + row] for row in range(3))


def _normal_matrix(matrix):
    a, b, c = matrix[0], matrix[4], matrix[8]
    d, e, f = matrix[1], matrix[5], matrix[9]
    g, h, i = matrix[2], matrix[6], matrix[10]
    cofactors = ((e*i-f*h, f*g-d*i, d*h-e*g),
                 (c*h-b*i, a*i-c*g, b*g-a*h),
                 (b*f-c*e, c*d-a*f, a*e-b*d))
    determinant = a * cofactors[0][0] + b * cofactors[0][1] + c * cofactors[0][2]
    if determinant <= 1e-12:
        _fail("Node transform is singular or reverses handedness")
    return tuple(tuple(value / determinant for value in row) for row in cofactors)


def _normal(matrix, normal):
    transformed = tuple(sum(row[k] * normal[k] for k in range(3)) for row in matrix)
    length = math.sqrt(sum(value * value for value in transformed))
    if not math.isfinite(length) or length < 1e-12:
        _fail("Transformed normal has zero length or is nonfinite")
    return tuple(value / length for value in transformed)


def validate_glb(path, expected_dimensions, max_triangles, expected_materials=None):
    """Validate exported, indexed triangle geometry; return JSON-safe actual metrics.

    ``expected_dimensions`` is exported glTF/Unity X,Y,Z, not Blender X,Y,Z.
    Dimensions and bottom-center pivot must agree within 0.01 meters.
    No Blender installation, renderer, or third-party package is required.
    """
    expected = _numbers(expected_dimensions, 3, "expected_dimensions")
    if any(value <= 0 for value in expected):
        _fail("expected_dimensions must be positive")
    _integer(max_triangles, "max_triangles", 1)
    raw, document, binary = _read_glb(path)
    # Check even unused/optional accessors so invalid UV/color or hidden data
    # cannot evade the validator merely by omitting a reference to it.
    for index, accessor in enumerate(document.get("accessors", [])):
        if (not isinstance(accessor, dict) or not isinstance(accessor.get("type"), str)
                or accessor["type"] not in _WIDTHS):
            _fail("accessor has an invalid type")
        if accessor["type"].startswith("MAT") and accessor.get("componentType") != 5126:
            _fail("Non-float matrix accessors are unsupported")
        _accessor(document, binary, index, accessor["type"], set(_COMPONENTS), allow_normalized=True)
    materials = document.get("materials", [])
    if not isinstance(materials, list) or not materials:
        _fail("Model must contain authored materials")
    names = []
    for material in materials:
        if not isinstance(material, dict) or not isinstance(material.get("name"), str) or not material["name"]:
            _fail("Every material requires a nonempty name")
        names.append(material["name"])
        pbr = material.get("pbrMetallicRoughness", {})
        if not isinstance(pbr, dict):
            _fail("Material pbrMetallicRoughness must be an object")
        for label, value, count in (("baseColorFactor", pbr.get("baseColorFactor", [1, 1, 1, 1]), 4),
                                    ("metallicFactor", [pbr.get("metallicFactor", 1)], 1),
                                    ("roughnessFactor", [pbr.get("roughnessFactor", 1)], 1),
                                    ("emissiveFactor", material.get("emissiveFactor", [0, 0, 0]), 3)):
            factors = _numbers(value, count, "material." + label)
            if any(not 0 <= factor <= 1 for factor in factors):
                _fail(f"Material {label} must be in [0,1]")
        if material.get("alphaMode", "OPAQUE") not in ("OPAQUE", "MASK", "BLEND"):
            _fail("Material alphaMode is invalid")
        if not isinstance(material.get("doubleSided", False), bool):
            _fail("Material doubleSided must be boolean")
    if len(set(names)) != len(names):
        _fail("Material names must be unique")
    if expected_materials is not None:
        if (not isinstance(expected_materials, (list, tuple))
                or any(not isinstance(name, str) for name in expected_materials)):
            _fail("expected_materials must be a list of material names")
        if sorted(names) != sorted(expected_materials):
            _fail("Material names do not match expected_materials")
    nodes = document.get("nodes", [])
    scene = _entry(document.get("scenes"), document.get("scene", 0), "scene")
    roots = scene.get("nodes", [])
    if not isinstance(roots, list) or not roots:
        _fail("Active scene contains no nodes")
    visited, points, triangles, vertices, mesh_count, used_materials = set(), [], 0, 0, 0, set()

    def visit(index, parent):
        nonlocal triangles, vertices, mesh_count
        node = _entry(nodes, index, "node")
        if index in visited:
            _fail("Scene has a node cycle or a node with multiple parents")
        visited.add(index)
        if "skin" in node or "weights" in node:
            _fail("This static-asset validator does not support skinning or morph weights")
        world = _multiply(parent, _transform(node))
        normal_matrix = _normal_matrix(world)
        if "mesh" in node:
            mesh_count += 1
            mesh = _entry(document.get("meshes"), node["mesh"], "node.mesh")
            primitives = mesh.get("primitives", [])
            if not isinstance(primitives, list) or not primitives:
                _fail("Mesh has no primitives")
            for primitive in primitives:
                if not isinstance(primitive, dict):
                    _fail("Mesh primitive must be an object")
                if _integer(primitive.get("mode", 4), "primitive.mode") != 4:
                    _fail("Only triangle primitives are allowed")
                if primitive.get("targets"):
                    _fail("Morph targets are unsupported for static assets")
                attributes = primitive.get("attributes", {})
                if not isinstance(attributes, dict) or "POSITION" not in attributes or "NORMAL" not in attributes:
                    _fail("Each primitive requires POSITION and NORMAL attributes")
                positions, position_accessor = _accessor(document, binary, attributes["POSITION"], "VEC3", {5126})
                if "min" not in position_accessor or "max" not in position_accessor:
                    _fail("POSITION accessor requires min and max bounds")
                normals, _ = _accessor(document, binary, attributes["NORMAL"], "VEC3", {5126})
                if len(positions) != len(normals):
                    _fail("POSITION and NORMAL counts disagree")
                for normal in normals:
                    if abs(math.sqrt(sum(v*v for v in normal)) - 1) > 0.01:
                        _fail("Vertex normal is not normalized")
                material = primitive.get("material")
                _entry(materials, material, "primitive.material")
                used_materials.add(material)
                indices, _ = _accessor(document, binary, primitive.get("indices"), "SCALAR", {5121, 5123, 5125})
                indices = [row[0] for row in indices]
                if len(indices) % 3:
                    _fail("Triangle index count must be divisible by three")
                if max(indices) >= len(positions):
                    _fail("Triangle index is out of range")
                transformed = [_point(world, position) for position in positions]
                if any(not math.isfinite(v) for point in transformed for v in point):
                    _fail("World coordinates contain nonfinite values")
                transformed_normals = [_normal(normal_matrix, normal) for normal in normals]
                referenced = set(indices)
                points.extend(transformed[index] for index in referenced)
                vertices += len(positions)
                for offset in range(0, len(indices), 3):
                    ia, ib, ic = indices[offset:offset + 3]
                    a, b, c = transformed[ia], transformed[ib], transformed[ic]
                    ab = tuple(b[k] - a[k] for k in range(3))
                    ac = tuple(c[k] - a[k] for k in range(3))
                    cross = (ab[1]*ac[2] - ab[2]*ac[1], ab[2]*ac[0] - ab[0]*ac[2],
                             ab[0]*ac[1] - ab[1]*ac[0])
                    area_squared = sum(value*value for value in cross)
                    edge_product = sum(v*v for v in ab) * sum(v*v for v in ac)
                    if edge_product == 0 or area_squared <= max(1e-24, edge_product * 1e-12):
                        _fail("Mesh contains a degenerate triangle")
                    average = tuple(sum(transformed_normals[index][k] for index in (ia, ib, ic))
                                    for k in range(3))
                    if sum(cross[k] * average[k] for k in range(3)) <= 0:
                        _fail("Triangle winding disagrees with its vertex normals")
                triangles += len(indices) // 3
        children = node.get("children", [])
        if not isinstance(children, list):
            _fail("node.children must be a list")
        for child in children:
            visit(child, world)

    for root in roots:
        visit(root, _IDENTITY)
    if not points or not triangles:
        _fail("Active scene contains no triangle geometry")
    if triangles > max_triangles:
        _fail(f"Triangle budget exceeded: {triangles} > {max_triangles}")
    minimum = [min(point[k] for point in points) for k in range(3)]
    maximum = [max(point[k] for point in points) for k in range(3)]
    dimensions = [maximum[k] - minimum[k] for k in range(3)]
    if any(abs(dimensions[k] - expected[k]) > DIMENSION_TOLERANCE for k in range(3)):
        _fail(f"World dimensions {dimensions} disagree with expected {list(expected)}")
    pivot_error = [abs((minimum[0] + maximum[0]) / 2), abs(minimum[1]),
                   abs((minimum[2] + maximum[2]) / 2)]
    if max(pivot_error) > PIVOT_TOLERANCE:
        _fail("World bounds do not have a bottom-center pivot (minY=0, centerXZ=0)")
    if used_materials != set(range(len(materials))):
        _fail("Model contains unused materials")
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "triangles": triangles, "vertices": vertices, "meshInstances": mesh_count,
            "materials": names, "materialCount": len(materials),
            "bounds": {"min": minimum, "max": maximum}, "dimensionsMeters": dimensions,
            "pivotErrorMeters": pivot_error, "windingNormalsConsistent": True,
            "coordinateSystem": {"up": "+Y", "forward": "+Z", "units": "meters"}}


def _bundle_file(directory, value, label):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        _fail(f"{label} must be a relative file path")
    path = (directory / value).resolve()
    try:
        path.relative_to(directory)
    except ValueError:
        _fail(f"{label} escapes the bundle directory")
    if not path.is_file():
        _fail(f"{label} does not exist: {value}")
    return path


def _sha(path, expected, label):
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        _fail(f"{label}.sha256 must be a lowercase SHA256 digest")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        _fail(f"{label} SHA256 mismatch")
    return actual


def _png(path):
    """Check PNG framing, chunk CRCs, dimensions and a complete compressed stream."""
    raw = path.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        _fail("Preview is not a PNG")
    cursor, width, height, compressed, ended = 8, None, None, bytearray(), False
    while cursor < len(raw):
        if cursor + 12 > len(raw):
            _fail("PNG chunk is truncated")
        length = struct.unpack_from(">I", raw, cursor)[0]
        kind = raw[cursor + 4:cursor + 8]
        end = cursor + 12 + length
        if end > len(raw):
            _fail("PNG chunk exceeds file bounds")
        payload = raw[cursor + 8:cursor + 8 + length]
        crc = struct.unpack_from(">I", raw, cursor + 8 + length)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            _fail("PNG chunk CRC mismatch")
        if width is None:
            if kind != b"IHDR" or length != 13:
                _fail("PNG must begin with a valid IHDR")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if not 16 <= width <= 8192 or not 16 <= height <= 8192:
                _fail("Preview PNG dimensions must be 16..8192 pixels")
            if depth != 8 or color not in (2, 6) or compression or filtering or interlace:
                _fail("Preview PNG must be noninterlaced 8-bit RGB or RGBA")
        elif kind == b"IHDR":
            _fail("PNG contains duplicate IHDR")
        if kind == b"IDAT":
            compressed.extend(payload)
        if kind == b"IEND":
            if length or end != len(raw):
                _fail("Invalid PNG IEND or trailing bytes")
            ended = True
            break
        cursor = end
    if not ended or not compressed:
        _fail("PNG is missing image data or IEND")
    channels = 3 if color == 2 else 4
    expected_size = height * (1 + width * channels)
    try:
        decoder = zlib.decompressobj()
        pixels = decoder.decompress(compressed, expected_size + 1)
    except zlib.error as exc:
        _fail(f"PNG image stream is corrupt: {exc}")
    if len(pixels) != expected_size or not decoder.eof or decoder.unused_data:
        _fail("PNG decompressed image size is invalid")
    stride = 1 + width * channels
    if any(pixels[offset] > 4 for offset in range(0, len(pixels), stride)):
        _fail("PNG contains an invalid scanline filter")
    return {"width": width, "height": height, "bytes": len(raw)}


def validate_bundle(directory):
    """Validate the reproducibility manifest, embedded GLB and rendered previews."""
    directory = Path(directory).resolve()
    try:
        raw_manifest = (directory / "manifest.json").read_bytes()
    except OSError as exc:
        _fail(f"Cannot read manifest.json: {exc}")
    manifest = _json(raw_manifest, "manifest.json")
    if manifest.get("schemaVersion") != "1.0":
        _fail("Unsupported manifest schemaVersion")
    for key in ("assetId", "requestId", "version", "category", "command"):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            _fail(f"manifest.{key} must be a nonempty string")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", manifest["assetId"]):
        _fail("manifest.assetId must be a stable lowercase identifier")
    _integer(manifest.get("seed"), "manifest.seed")
    if manifest.get("units") != "meters" or manifest.get("pivot") != "bottom-center":
        _fail("Manifest must declare meter units and bottom-center pivot")
    axes = {"sourceUp": "+Z", "sourceForward": "-Y", "exportUp": "+Y", "exportForward": "+Z"}
    if manifest.get("axes") != axes:
        _fail("Manifest axes must declare Blender +Z/-Y to glTF +Y/+Z")
    if not isinstance(manifest.get("sourceCommit"), str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", manifest["sourceCommit"]):
        _fail("manifest.sourceCommit must contain a Git commit SHA")
    if not isinstance(manifest.get("sourceDigest"), str) or not re.fullmatch(r"[0-9a-f]{64}", manifest["sourceDigest"]):
        _fail("manifest.sourceDigest must contain a SHA256 digest")
    if not isinstance(manifest.get("sourceDirty"), bool):
        _fail("manifest.sourceDirty must be boolean")
    config = manifest.get("config")
    if not isinstance(config, dict):
        _fail("manifest.config must be an object")
    config_digest = hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":"),
                                            ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
    if manifest.get("configSHA256") != config_digest:
        _fail("Manifest configSHA256 disagrees with canonical config JSON")
    # The committed generator config is the authority for identity and budgets.
    # Hash agreement alone would permit a contradictory but self-consistent manifest.
    from .config import validate_config
    validate_config(config)
    for key in ("assetId", "version", "requestId", "category", "seed", "dimensionsMeters", "maxTriangles"):
        if manifest.get(key) != config[key]:
            _fail(f"manifest.{key} disagrees with the embedded config")
    provenance = manifest.get("provenance", {})
    if (not isinstance(provenance, dict) or provenance.get("method") != "procedural-blender-python"
            or provenance.get("thirdPartyAssets") != [] or not provenance.get("generator")):
        _fail("Manifest must declare original procedural generation with no third-party assets")
    tooling = manifest.get("tooling", {})
    if not isinstance(tooling, dict) or any(not tooling.get(key) for key in ("blender", "python", "engine", "device")):
        _fail("Manifest must record Blender, Python, render engine and device")
    if tooling["blender"] != config["blenderVersion"]:
        _fail("Manifest Blender version disagrees with the embedded config")
    model = manifest.get("model", {})
    if not isinstance(model, dict):
        _fail("manifest.model must be an object")
    model_path = _bundle_file(directory, model.get("file"), "model.file")
    if model.get("file") != manifest["assetId"] + ".glb":
        _fail("Manifest model.file must equal assetId + '.glb'")
    if model_path.suffix.lower() != ".glb":
        _fail("Model must have a .glb extension")
    _sha(model_path, model.get("sha256"), "model")
    if (not isinstance(manifest.get("materials"), list) or not manifest["materials"]
            or any(not isinstance(name, str) or not name for name in manifest["materials"])):
        _fail("Manifest materials must list the expected authored material names")
    if sorted(manifest["materials"]) != sorted(config["palette"]):
        _fail("Manifest materials disagree with the embedded config palette")
    geometry = validate_glb(model_path, manifest.get("dimensionsMeters"),
                            manifest.get("maxTriangles"), manifest.get("materials"))
    if model.get("bytes") != geometry["bytes"]:
        _fail("Manifest model.bytes disagrees with the file")
    recorded = manifest.get("geometry")
    if not isinstance(recorded, dict):
        _fail("Manifest must record geometry validation metrics")
    # Compare the complete independent result so stale bounds/counts cannot survive.
    if recorded != geometry:
        _fail("Manifest geometry metrics disagree with independently validated GLB")
    previews = manifest.get("previews", {})
    if not isinstance(previews, dict):
        _fail("manifest.previews must be an object")
    preview_metrics = {}
    for view in ("front", "isometric"):
        info = previews.get(view)
        if not isinstance(info, dict):
            _fail(f"Missing {view} preview")
        if info.get("file") != view + ".png":
            _fail(f"Preview {view} file must be '{view}.png'")
        preview_path = _bundle_file(directory, info.get("file"), f"previews.{view}.file")
        if preview_path.suffix.lower() != ".png":
            _fail("Previews must have a .png extension")
        _sha(preview_path, info.get("sha256"), f"previews.{view}")
        preview_metrics[view] = _png(preview_path)
        if any(preview_metrics[view][key] != config["preview"]["resolution"] for key in ("width", "height")):
            _fail(f"Preview {view} resolution disagrees with the embedded config")
        for dimension in ("width", "height"):
            if dimension in info and info[dimension] != preview_metrics[view][dimension]:
                _fail(f"Preview {view} {dimension} disagrees with manifest")
    return {"assetId": manifest["assetId"], "geometry": geometry, "previews": preview_metrics,
            "valid": True}
