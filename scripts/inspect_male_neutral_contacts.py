import bpy,bmesh,json,argparse,sys
from mathutils.bvhtree import BVHTree
from mathutils import Vector
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--blend',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(Path(a.blend).resolve()),load_ui=False,use_scripts=False)
head=bpy.data.objects['M01_head'];eyes=bpy.data.objects['M01_eyes'];hair=bpy.data.objects['M01_hair_base']
def tree(o):
 m=o.data;return BVHTree.FromPolygons([o.matrix_world@v.co for v in m.vertices],[p.vertices[:] for p in m.polygons],all_triangles=False)
eye_tree=tree(eyes);head_tree=tree(head);bm=bmesh.new();bm.from_mesh(head.data);bm.verts.ensure_lookup_table();adj={}
for e in bm.edges:
 if len(e.link_faces)==1:
  i,j=[v.index for v in e.verts];adj.setdefault(i,set()).add(j);adj.setdefault(j,set()).add(i)
left=set(adj);loops=[]
while left:
 i=min(left);left.remove(i);queue=[i];seen={i}
 for v in queue:
  for j in adj[v]:
   if j not in seen:seen.add(j);left.discard(j);queue.append(j)
 pts=[head.matrix_world@head.data.vertices[i].co for i in sorted(seen)];center=sum(pts,Vector())/len(pts);dist=[eye_tree.find_nearest(p)[3] for p in pts]
 loops.append({'vertices':len(pts),'centerWorld':list(center),'boundsMin':[min(p[k] for p in pts) for k in range(3)],'boundsMax':[max(p[k] for p in pts) for k in range(3)],'nearestEyeSurfaceDistanceMeters':{'min':min(dist),'max':max(dist),'mean':sum(dist)/len(dist)}})
bm.free();pairs=head_tree.overlap(eye_tree);hair_pairs=head_tree.overlap(tree(hair))
x={'schema':'male-neutral-a01-static-contact-diagnostics-1','headBoundaryComponents':loops,'headEyeIntersectingTrianglePairs':len(pairs),'headHairIntersectingTrianglePairs':len(hair_pairs),'interpretation':'Diagnostic only, not blanket penetration failures: socket rims and hair roots intentionally overlap skin. Boundary groups need anatomical classification; distances are to nearest eye surface, not signed clearance. No animation/deformation contact guarantee.'}
Path(a.out).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8');print(json.dumps(x))
