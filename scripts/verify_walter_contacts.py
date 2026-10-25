"""Targeted saved-mesh regression checks for the actual porch construction faults."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]


def components(obj):
    mesh=obj.data;neighbors=[set() for _ in mesh.vertices]
    for edge in mesh.edges:
        a,b=edge.vertices;neighbors[a].add(b);neighbors[b].add(a)
    remaining=set(range(len(mesh.vertices)));groups=[]
    while remaining:
        first=min(remaining);remaining.remove(first);group={first};stack=[first]
        while stack:
            for n in neighbors[stack.pop()]:
                if n in remaining:remaining.remove(n);group.add(n);stack.append(n)
        groups.append(group)
    names=json.loads(obj['constructionParts'])
    if len(names)!=len(groups):raise ValueError('Construction-part/component mismatch')
    result=[]
    for name,group in zip(names,groups):
        indices=sorted(group);lookup={old:new for new,old in enumerate(indices)}
        points=[obj.matrix_world@mesh.vertices[i].co for i in indices]
        faces=[tuple(lookup[i] for i in p.vertices) for p in mesh.polygons if p.vertices[0] in group]
        result.append({'name':name,'points':points,'tree':BVHTree.FromPolygons(points,faces,all_triangles=True,epsilon=1e-6)})
    return result


def bounds(part,axis,which):return which(v[axis] for v in part['points'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);source=Path(args.input).resolve();source.relative_to(ROOT)
    if bpy.app.version!=(4,5,14) or not bpy.app.background or bpy.app.online_access:raise RuntimeError('Require pinned offline Blender')
    path=source/'construction-checks.json'
    if path.exists():raise FileExistsError('Preserve previous check')
    result={'schema':'walter-construction-checks-1','status':'passed','scope':'Actual saved meshes; targeted contacts only, no exhaustive interpenetration/navigation/physics test.',
            'checkerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    asset='prop_porch_rocking_chair_001';bpy.ops.wm.open_mainfile(filepath=str(source/asset/(asset+'.blend')),load_ui=False,use_scripts=False)
    parts=components(bpy.data.objects[asset]);supports=[p for p in parts if p['name']=='arm_front'];legs=[p for p in parts if p['name']=='splayed_leg']
    counts=[sum(len(p['tree'].overlap(leg['tree'])) for leg in legs) for p in supports]
    result['frontArmSupportToLegTriangleIntersections']=counts
    if len(counts)!=2 or any(n==0 for n in counts):raise ValueError('Rocker arm support does not intersect a leg')
    asset='prop_wooden_crate_001';bpy.ops.wm.open_mainfile(filepath=str(source/asset/(asset+'.blend')),load_ui=False,use_scripts=False)
    parts=components(bpy.data.objects[asset]);battens=[p for p in parts if p['name']=='corner_batten'];walls=[p for p in parts if 'wall_board' in p['name']]
    rim=max(bounds(p,2,max) for p in walls);clearances=[rim-bounds(p,2,max) for p in battens]
    result['crateBattenCapBelowRimMeters']=clearances
    if len(clearances)!=4 or min(clearances)<.005:raise ValueError('Crate cap is coplanar with rim')
    bpy.ops.wm.open_mainfile(filepath=str(source/'fence-joints.blend'),load_ui=False,use_scripts=False);bpy.context.view_layer.update()
    panels=[o for o in bpy.data.objects if o.type=='MESH' and o.get('assetId')=='prop_wooden_fence_001']
    posts=[o for o in bpy.data.objects if o.type=='MESH' and o.get('assetId')=='prop_fence_post_001']
    panel=min(panels,key=lambda o:o.location.x);post=min(posts,key=lambda o:abs(o.location.x-.75)+abs(o.location.y))
    rail=max(bounds(p,0,max) for p in components(panel) if p['name']=='rear_rail')
    face=min(bounds(p,0,min) for p in components(post) if p['name']=='post_shaft')
    result['actualStraightRailPostGapMeters']=face-rail
    if abs(face-rail)>.0002:raise ValueError('Actual fence mesh seam gap')
    bpy.ops.wm.open_mainfile(filepath=str(source/'porch-presentation.blend'),load_ui=False,use_scripts=False);bpy.context.view_layer.update()
    lamp=next(o for o in bpy.data.objects if o.type=='MESH' and o.get('assetId')=='prop_porch_lantern_001')
    wall=next(o for o in bpy.data.objects if o.name.startswith('TEMP_facade_fragment'))
    back=max((lamp.matrix_world@v.co).y for v in lamp.data.vertices);face=min((wall.matrix_world@v.co).y for v in wall.data.vertices)
    result['actualLanternWallGapMeters']=face-back
    if abs(face-back)>.0002:raise ValueError('Lantern wall mount is floating/penetrating')
    pot=next(o for o in bpy.data.objects if o.type=='MESH' and o.get('assetId')=='prop_flower_pot_002')
    crate=next(o for o in bpy.data.objects if o.type=='MESH' and o.get('assetId')=='prop_wooden_crate_001')
    bottom=min((pot.matrix_world@v.co).z for v in pot.data.vertices)
    mesh=crate.data;tree=BVHTree.FromPolygons([crate.matrix_world@v.co for v in mesh.vertices],
        [tuple(p.vertices) for p in mesh.polygons],all_triangles=True,epsilon=1e-7)
    from mathutils import Vector
    support=[]
    for dx in (-.045,.045):
        hit,normal,index,distance=tree.ray_cast(Vector((pot.location.x+dx,pot.location.y,bottom+.01)),Vector((0,0,-1)),.02)
        if hit is None:raise ValueError('Pot floats over an open crate')
        support.append(bottom-hit.z)
    result['smallPotCrateSupportGapMeters']=support
    if any(gap<-.0001 or gap>.001 for gap in support):raise ValueError('Pot/crate support clearance')
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('WALTER_CONTACT_CHECKS_PASSED',flush=True)


if __name__=='__main__':main()
