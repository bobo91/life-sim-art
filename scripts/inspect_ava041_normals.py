"""Locate exported triangles failing the independent winding/normal guard.

Read-only GLB binary diagnostic. This does not change winding, normals, topology,
the validator or its threshold. The reported dot is the same unnormalized
cross-product/average-normal dot used by art_pipeline.validation.validate_glb.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from art_pipeline.validation import (_read_glb, _accessor, _IDENTITY, _multiply,
    _transform, _point, _normal_matrix, _normal)


def inspect(path):
    raw, document, binary = _read_glb(path)
    records = []
    nodes = document.get("nodes", [])
    scene = document["scenes"][document.get("scene", 0)]

    def visit(index, parent):
        node = nodes[index]
        world = _multiply(parent, _transform(node))
        normal_matrix = _normal_matrix(world)
        if "mesh" in node:
            mesh = document["meshes"][node["mesh"]]
            for primitive_index, primitive in enumerate(mesh["primitives"]):
                attributes = primitive["attributes"]
                positions, _ = _accessor(document, binary, attributes["POSITION"], "VEC3", {5126})
                normals, _ = _accessor(document, binary, attributes["NORMAL"], "VEC3", {5126})
                indices, _ = _accessor(document, binary, primitive["indices"], "SCALAR", {5121, 5123, 5125})
                positions = [_point(world, p) for p in positions]
                normals = [_normal(normal_matrix, n) for n in normals]
                indices = [value[0] for value in indices]
                bad, smallest = [], None
                for offset in range(0, len(indices), 3):
                    ids = indices[offset:offset+3]
                    a, b, c = [positions[i] for i in ids]
                    ab = [b[k]-a[k] for k in range(3)]
                    ac = [c[k]-a[k] for k in range(3)]
                    cross = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
                    average = [sum(normals[i][k] for i in ids) for k in range(3)]
                    dot = sum(cross[k]*average[k] for k in range(3))
                    if smallest is None or dot < smallest:
                        smallest = dot
                    if dot <= 0:
                        area = math.sqrt(sum(x*x for x in cross)) / 2
                        normal_length = math.sqrt(sum(x*x for x in average))
                        bad.append({"triangleIndex": offset//3, "indices": ids,
                            "dot": dot, "areaM2": area,
                            "orientationCosine": dot/(2*area*normal_length) if area and normal_length else None,
                            "positionsGltfXYZ": [positions[i] for i in ids],
                            "positionsBlenderXYZ": [(positions[i][0], -positions[i][2], positions[i][1]) for i in ids],
                            "normalsGltfXYZ": [normals[i] for i in ids]})
                records.append({"node": node.get("name"), "mesh": mesh.get("name"),
                    "meshIndex": node["mesh"], "primitive": primitive_index,
                    "triangles": len(indices)//3, "minimumDot": smallest,
                    "offendingTriangleCount": len(bad), "offendingTriangles": bad})
        for child in node.get("children", []):
            visit(child, world)

    for index in scene["nodes"]:
        visit(index, _IDENTITY)
    return {"schema": "ava041-readonly-normal-diagnostic-1",
        "glbSha256": hashlib.sha256(raw).hexdigest(),
        "triangles": sum(record["triangles"] for record in records),
        "offendingTriangles": sum(record["offendingTriangleCount"] for record in records),
        "primitives": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb")
    parser.add_argument("--out")
    args = parser.parse_args()
    report = inspect(Path(args.glb))
    if args.out:
        output = Path(args.out)
        if output.exists():
            raise FileExistsError("Fresh diagnostic path required")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"glbSha256": report["glbSha256"], "triangles": report["triangles"],
        "offendingTriangles": report["offendingTriangles"],
        "offendingPrimitives": [{k: v for k,v in record.items() if k != "offendingTriangles"}
                               | {"firstOffendingTriangle": record["offendingTriangles"][0]}
                               for record in report["primitives"] if record["offendingTriangleCount"]]}, indent=2))


if __name__ == "__main__":
    main()
