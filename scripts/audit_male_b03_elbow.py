"""Read-only actual B02 elbow density/skinning audit for bounded B03 proof."""
import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
r=Path.cwd();src=r/'build/male-neutral-b02/delivery-001/character_b02.blend';import argparse
ap=argparse.ArgumentParser();ap.add_argument('--out',default='build/male-neutral-b03/mesh-audit-001');aa=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);out=r/aa.out;out.mkdir(parents=True,exist_ok=False);before=hashlib.sha256(src.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False);rig=bpy.data.objects['A03_B01_Rig'];body=bpy.data.objects['M01_body'];mesh=body.data;mesh.calc_loop_triangles();rig.animation_data.action=bpy.data.actions['run'];bpy.context.scene.frame_set(5,subframe=.5);bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=ev.to_mesh();posed.calc_loop_triangles();adj=[set() for v in mesh.vertices];edgefaces={e.key:[] for e in mesh.edges}
for e in mesh.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
for f in mesh.polygons:
 for key in f.edge_keys:edgefaces[tuple(sorted(key))].append(f.index)
res={'schema':'male-b03-readonly-elbow-mesh-audit-1','sourceSha256':before,'sourceUnchanged':True,'bones':len(rig.data.bones),'mesh':'M01_body','vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'polygonSizes':{str(n):sum(len(p.vertices)==n for p in mesh.polygons) for n in set(len(p.vertices) for p in mesh.polygons)},'rawCustomNormals':mesh.has_custom_normals,'evaluatedCustomNormals':posed.has_custom_normals,'modifiers':[{'type':m.type,'name':m.name,'preserveVolume':getattr(m,'use_deform_preserve_volume',None)} for m in body.modifiers],'runFrame':5.5,'elbows':{}}
for side in ['L','R']:
 upper=rig.data.bones['UpperArm.'+side];lower=rig.data.bones['LowerArm.'+side];center=lower.matrix_local.translation;axis=(center-upper.matrix_local.translation).normalized();normalaxis=lower.matrix_local.col[0].to_3d();ids=[];rows=[]
 for v in mesh.vertices:
  delta=v.co-center;long=delta.dot(axis);rad=(delta-axis*long).length
  if abs(long)<.09 and rad<.075:
   ids.append(v.index);w={body.vertex_groups[g.group].name:float(g.weight) for g in v.groups};rows.append({'vertex':v.index,'rest':list(v.co),'posed':list(posed.vertices[v.index].co),'longitudinalMm':long*1000,'radialMm':rad*1000,'valence':len(adj[v.index]),'weights':w})
 bins=[]
 for row in sorted(rows,key=lambda x:x['longitudinalMm']):
  if not bins or row['longitudinalMm']-bins[-1]['maximumMm']>2:bins.append({'minimumMm':row['longitudinalMm'],'maximumMm':row['longitudinalMm'],'vertices':[]})
  bins[-1]['maximumMm']=row['longitudinalMm'];bins[-1]['vertices'].append(row['vertex'])
 allsupport={v.index for v in mesh.vertices if any(body.vertex_groups[g.group].name=='B02_Elbow.'+side and g.weight>1e-6 for g in v.groups)}
 edges=[]
 for edge,fs in edgefaces.items():
  if len(fs)==2 and any(i in ids for i in edge):
   angle=math.degrees(posed.polygons[fs[0]].normal.angle(posed.polygons[fs[1]].normal));edges.append({'vertices':list(edge),'posedDihedralDegrees':angle,'faceSizes':[len(mesh.polygons[f].vertices) for f in fs]})
 straight=(rig.pose.bones['UpperArm.'+side].matrix@upper.matrix_local.inverted()@lower.matrix_local).to_quaternion();bent=rig.pose.bones['LowerArm.'+side].matrix.to_quaternion();bend=math.degrees(straight.rotation_difference(bent).angle)
 res['elbows'][side]={'center':list(center),'axis':list(axis),'within90mm':len(ids),'b02SupportAffected':len(allsupport),'longitudinalClusters2mmTolerance':[{'minimumMm':b['minimumMm'],'maximumMm':b['maximumMm'],'count':len(b['vertices'])} for b in bins],'maxSelectedDihedralDegrees':max(e['posedDihedralDegrees'] for e in edges),'runBendDegrees':bend,'vertexRows':rows,'largestPosedDihedralEdges':sorted(edges,key=lambda x:-x['posedDihedralDegrees'])[:20]}
ev.to_mesh_clear();assert hashlib.sha256(src.read_bytes()).hexdigest()==before;(out/'mesh-audit.json').write_bytes((json.dumps(res,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in res.items() if k!='elbows'},indent=2));print(json.dumps({s:{k:v for k,v in d.items() if k not in ['vertexRows','largestPosedDihedralEdges']} for s,d in res['elbows'].items()},indent=2))
