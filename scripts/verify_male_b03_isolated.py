"""Focused preservation checks for the stopped B03 isolated corrective proof."""
import argparse,bpy,json,hashlib,struct,sys
from pathlib import Path
from mathutils import Matrix
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r=Path.cwd();src=r/'build/male-neutral-b02/delivery-001/character_b02.blend';cand=r/a.candidate;out=r/a.out;assert not out.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 meshes={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or not o.name.startswith('M01_'):continue
  h=hashlib.sha256();o.data.calc_loop_triangles()
  for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
  for t in o.data.loop_triangles:h.update(struct.pack('<3I',*t.vertices))
  for uv in o.data.uv_layers:
   for v in uv.data:h.update(struct.pack('<2f',*v.uv))
  for poly in o.data.polygons:h.update(struct.pack('<I',poly.material_index))
  w=hashlib.sha256()
  for v in o.data.vertices:
   for g in v.groups:w.update(o.vertex_groups[g.group].name.encode());w.update(struct.pack('<f',g.weight))
  materials=[]
  for m in o.data.materials:
   nodes=[]
   if m.node_tree:
    for n in m.node_tree.nodes:
     if n.type=='BSDF_PRINCIPLED':nodes.append([n.name,[(i.name,list(i.default_value) if hasattr(i.default_value,'__iter__') else i.default_value) for i in n.inputs if i.name in ['Base Color','Metallic','Roughness','Specular IOR Level']]])
     elif n.type=='TEX_IMAGE' and n.image:nodes.append([n.name,n.image.name,sha_data(n.image.packed_file.data) if n.image.packed_file else n.image.filepath])
   materials.append([m.name,nodes])
  meshes[o.name]={'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'rawGeometryUvMatIndices':h.hexdigest(),'weights':w.hexdigest(),'materials':materials}
 rig=bpy.data.objects['A03_B01_Rig'];bones={b.name:{'parent':b.parent.name if b.parent else None,'rest':[[float(x) for x in row] for row in b.matrix_local]} for b in rig.data.bones};actions={}
 for ac in bpy.data.actions:
  rows=[]
  for fc in ac.fcurves:rows.append([fc.data_path,fc.array_index,[(tuple(k.co),k.interpolation) for k in fc.keyframe_points]])
  actions[ac.name]=sha_data(json.dumps(rows,sort_keys=True).encode())
 return {'meshes':meshes,'bones':bones,'actions':actions,'texts':len(bpy.data.texts)}
def sha_data(b):return hashlib.sha256(b).hexdigest()
srchash=sha(src);bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False);before=snapshot();bpy.ops.wm.open_mainfile(filepath=str(cand),load_ui=False,use_scripts=False);after=snapshot();assert before==after,'Source mesh/UV/material/skin/rig/action data changed'
body=bpy.data.objects['M01_body'];keys=body.data.shape_keys.key_blocks;assert len(keys)==3;basis=keys['Basis'];assert all((v.co-basis.data[v.index].co).length==0 for v in body.data.vertices);local={}
for side in ['L','R']:
 key=keys['B03_ElbowCorrective.'+side];ids=[i for i,v in enumerate(key.data) if (v.co-basis.data[i].co).length>1e-8];local[side]={'verticesChanged':len(ids),'maxRestDeltaMeters':max((key.data[i].co-basis.data[i].co).length for i in ids)}
# Actual zero values restore the evaluated neutral surface after save/reopen.
for key in list(keys)[1:]:key.value=0
rig=bpy.data.objects['A03_B01_Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();err=max((v.co-mesh.vertices[i].co).length for i,v in enumerate(body.data.vertices));ev.to_mesh_clear();assert err<1e-5
assert sha(src)==srchash and len(rig.data.bones)==58
# Confirm the second render pass changed diagnostic poses, not the candidate shape.
def morph_sig():
 h=hashlib.sha256()
 for key in bpy.data.objects['M01_body'].data.shape_keys.key_blocks:
  h.update(key.name.encode())
  for v in key.data:h.update(struct.pack('<3f',*v.co))
 return h.hexdigest()
key_names=list(keys.keys());final_sig=morph_sig();initial=r/'build/male-neutral-b03/shape-probe-001/candidate.blend';bpy.ops.wm.open_mainfile(filepath=str(initial),load_ui=False,use_scripts=False);same_shape=final_sig==morph_sig();assert same_shape
result={'schema':'male-b03-focused-preservation-1','sourceSha256':srchash,'candidateReopened':True,'oneCandidateShapeIdenticalAcrossDiagnosticPasses':same_shape,'morphCoordinatesSha256':final_sig,'allTenRawMeshesUvMaterialsWeightsBonesAndFourActionsIdenticalToB02':True,'assetTriangles':sum(m['triangles'] for m in after['meshes'].values()),'bones':58,'shapeKeys':key_names,'neutralBasisExactlyPreserved':True,'evaluatedNeutralMaxFloatErrorMeters':err,'localMorphs':local,'sourceUnchanged':True,'noGLBOrUnityRun':True,'limits':'Preservation and zero-state checks only; visible gate failed, no morph export/runtime/footcontact rerun claimed.'};out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result),flush=True)
