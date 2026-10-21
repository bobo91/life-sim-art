"""Exporter orientation checks for our asymmetric streetlamp benchmark."""
from .validation import _accessor, _read_glb


def streetlamp_frame(path, config):
    _, document, binary = _read_glb(path)
    # The generated single mesh is baked in the exported frame. Reject displaced
    # origins even when a compensating vertex translation preserves world bounds.
    nodes = document["nodes"]
    if (len(nodes) != 1 or nodes[0].get("mesh") != 0 or
            any(key in nodes[0] for key in ("matrix", "translation", "rotation", "scale", "children"))):
        raise ValueError("Streetlamp export must have a single identity-transform mesh at the origin")
    positions = []
    for primitive in document["meshes"][0]["primitives"]:
        points, _ = _accessor(document, binary, primitive["attributes"]["POSITION"], "VEC3", {5126})
        positions.extend(points)
    height = config["dimensionsMeters"][1]
    shaft = [point for point in positions if height*.50/3.2 <= point[1] <= height*.70/3.2]
    if not shaft:
        raise ValueError("Streetlamp service plate orientation probe is missing")
    minimum = min(point[2] for point in shaft)
    maximum = max(point[2] for point in shaft)
    if minimum <= .08*config["dimensionsMeters"][2]/.64:
        raise ValueError("Streetlamp service plate must face exported +Z")
    return {"sourceAxis":"-Y", "exportAxis":"+Z", "feature":"service plate on front of shaft",
            "servicePlateMinZMeters":minimum, "servicePlateMaxZMeters":maximum, "identityMeshOrigin":True}
