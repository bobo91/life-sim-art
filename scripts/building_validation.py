"""Validate authored building anchors without changing the shared prop validator.

Building modules deliberately use anchors such as a wall's left edge or a roof
ridge. A temporary GLB receives a parent translation calculated from CONFIGURED
export-space bounds, allowing the existing geometry validator to run unchanged.
The delivered GLB is never rewritten, and its original bounds are checked to
1 mm. Calculating that translation from measured bounds would conceal errors.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import tempfile

from art_pipeline.validation import (
    _IDENTITY, _entry, _numbers, _read_glb, _transform, validate_glb,
)


ANCHOR_TOLERANCE_METERS = 0.001


def _normalized_copy(raw, document, translation):
    """Replace only JSON; retain every other GLB chunk byte-for-byte."""
    scene = _entry(document.get("scenes"), document.get("scene", 0), "scene")
    nodes = document["nodes"]
    root = len(nodes)
    nodes.append({"name": "__validation_configured_anchor__",
                  "translation": list(translation), "children": scene["nodes"][:]})
    scene["nodes"] = [root]
    encoded = json.dumps(document, separators=(",", ":"), allow_nan=False).encode("utf-8")
    encoded += b" " * (-len(encoded) % 4)
    chunks = [struct.pack("<I4s", len(encoded), b"JSON") + encoded]
    cursor = 12
    while cursor < len(raw):
        length, kind = struct.unpack_from("<I4s", raw, cursor)
        end = cursor + 8 + length
        if kind != b"JSON":
            chunks.append(raw[cursor:end])
        cursor = end
    body = b"".join(chunks)
    return struct.pack("<4sII", b"glTF", 2, len(body) + 12) + body


def _identity_root(document):
    scene = _entry(document.get("scenes"), document.get("scene", 0), "scene")
    roots = scene.get("nodes", [])
    if not isinstance(roots, list) or len(roots) != 1:
        raise ValueError("Building active scene must have exactly one identity root")
    root = _entry(document.get("nodes"), roots[0], "building root")
    # Reuse parsing rules, including rejection of a matrix combined with TRS.
    matrix = _transform(root)
    if any(abs(a - b) > 1e-7 for a, b in zip(matrix, _IDENTITY)):
        raise ValueError("Building root transform must be identity")
    # Do not allow nonidentity TRS that happen to cancel each other out.
    for key, expected in (("translation", (0, 0, 0)), ("scale", (1, 1, 1))):
        if key in root and any(abs(a - b) > 1e-7
                               for a, b in zip(_numbers(root[key], 3, key), expected)):
            raise ValueError("Building root transform must be identity")
    if "rotation" in root:
        rotation = _numbers(root["rotation"], 4, "rotation")
        if max(abs(value) for value in rotation[:3]) > 1e-7 or abs(abs(rotation[3]) - 1) > 1e-7:
            raise ValueError("Building root transform must be identity")


def validate_building_glb(path, expected_dimensions, max_triangles,
                          expected_materials, expected_bounds):
    """Return actual production metrics for a static, authored-anchor module.

    ``expected_dimensions`` and ``expected_bounds={"min": [...], "max": [...]}``
    are in exported glTF/Unity X/Y/Z meters. Bounds must be independently recorded
    in the module config, not derived from the file being validated. Child
    transforms and empty door/hinge hierarchies are allowed; the sole scene root
    itself must be identity. Shared validation still checks all mesh data,
    winding/normals, indices, dimensions, materials and triangle budgets.
    """
    dimensions = _numbers(expected_dimensions, 3, "expected_dimensions")
    if any(value <= 0 for value in dimensions):
        raise ValueError("expected_dimensions must be positive")
    if not isinstance(expected_bounds, dict):
        raise ValueError("expected_bounds must contain min and max vectors")
    minimum = _numbers(expected_bounds.get("min"), 3, "expected_bounds.min")
    maximum = _numbers(expected_bounds.get("max"), 3, "expected_bounds.max")
    span = [maximum[k] - minimum[k] for k in range(3)]
    if any(value <= 0 for value in span):
        raise ValueError("expected_bounds must have positive extents")
    if any(abs(span[k] - dimensions[k]) > ANCHOR_TOLERANCE_METERS for k in range(3)):
        raise ValueError("expected_dimensions disagree with configured expected_bounds")

    raw, document, _binary = _read_glb(path)
    _identity_root(document)
    translation = [-(minimum[0] + maximum[0]) / 2, -minimum[1],
                   -(minimum[2] + maximum[2]) / 2]
    with tempfile.TemporaryDirectory(prefix="willow-building-validation-") as directory:
        temporary = Path(directory) / "normalized.glb"
        temporary.write_bytes(_normalized_copy(raw, document, translation))
        metrics = validate_glb(temporary, dimensions, max_triangles, expected_materials)

    original_bounds = {bound: [value - translation[k] for k, value in enumerate(metrics["bounds"][bound])]
                       for bound in ("min", "max")}
    errors = [max(abs(original_bounds["min"][k] - minimum[k]),
                  abs(original_bounds["max"][k] - maximum[k])) for k in range(3)]
    if max(errors) > ANCHOR_TOLERANCE_METERS:
        raise ValueError("Original building bounds disagree with configured authored anchor by more than 1 mm")
    metrics["sha256"] = hashlib.sha256(raw).hexdigest()
    metrics["bytes"] = len(raw)
    metrics["bounds"] = original_bounds
    metrics["pivotPolicy"] = "authored-module-anchor"
    metrics["normalizedPivotErrorMeters"] = metrics.pop("pivotErrorMeters")
    metrics["anchorBoundsErrorMeters"] = errors
    metrics["validationNormalization"] = {
        "method": "configured-bounds-to-bottom-center",
        "translationMeters": translation,
        "productionBytesModified": False,
    }
    return metrics
