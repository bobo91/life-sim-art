"""Controlled A03 static-derivative optimization; facial/hair meshes are untouched.
No bind, rig, shape-key or animation compatibility is implied by Decimate.
The preserved high-quality source remains the authoring/reference source.
"""
import argparse,hashlib,json,math,struct,sys,time
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

DEFAULT_RECIPE = {
 'M01_body':{'ratio':.84,'protectHandsBeyondX':.68,'protectUvSeams':True},
 'M01_shirt':{'ratio':.73,'protectUvSeams':True},
 'M01_pants':{'ratio':.65,'protectUvSeams':True},
 'M01_shoes_base':{'ratio':.25,'protectUvSeams':True},
 'M01_shoes_bottom':{'ratio':.20,'protectUvSeams':True},
 'M01_shoes_parts':{'ratio':.24,'protectUvSeams':True},
}
PROTECTED_MESHES = {'M01_head','M01_eyes','M01_eyebrows','M01_hair_base'}

def snapshot(obj):
 me=obj.data;me.calc_loop_triangles();points=[tuple(obj.matrix_world@v.co) for v in me.vertices];triangles=[tuple(t.vertices) for t in me.loop_triangles];digest=hashlib.sha256()
 for p in points:digest.update(struct.pack('<3f',*p))
 for t in triangles:digest.update(struct.pack('<3I',*t))
 return {'points':points,'triangles':triangles,'vertices':len(points),'triangleCount':len(triangles),'geometrySha256':digest.hexdigest(),'bounds':{'min':[min(p[k] for p in points) for k in range(3)],'max':[max(p[k] for p in points) for k in range(3)]},'materials':[m.name if m else None for m in me.materials]}

def protected_vertices(obj,settings):
 me=obj.data;edge_faces={e.index:[] for e in me.edges};uv=me.uv_layers.active;edge_uv={}
 for p in me.polygons:
  for li in p.loop_indices:
   loop=me.loops[li];edge_faces[loop.edge_index].append(p.index)
   if uv:
    nxt=li+1 if li+1<p.loop_start+p.loop_total else p.loop_start
    record=tuple(sorted(((loop.vertex_index,tuple(uv.data[li].uv)),(me.loops[nxt].vertex_index,tuple(uv.data[nxt].uv)))))
    edge_uv.setdefault(loop.edge_index,[]).append(record)
 ids=set();counts={'boundaryEdges':0,'materialEdges':0,'uvSeamEdges':0,'sharpEdges':0}
 for e in me.edges:
  fs=edge_faces[e.index];boundary=len(fs)==1;material=len({me.polygons[i].material_index for i in fs})>1
  charts=edge_uv.get(e.index,[]);uv_seam=len(charts)==2 and any(abs(a-b)>1e-6 for pair_a,pair_b in zip(charts[0],charts[1]) for a,b in zip(pair_a[1],pair_b[1]))
  sharp=bool(e.use_edge_sharp)
  counts['boundaryEdges']+=boundary;counts['materialEdges']+=material;counts['uvSeamEdges']+=uv_seam;counts['sharpEdges']+=sharp
  if boundary or material or sharp or (settings.get('protectUvSeams',True) and (uv_seam or e.use_seam)):ids.update(e.vertices)
 hands={v.index for v in me.vertices if settings.get('protectHandsBeyondX') and abs((obj.matrix_world@v.co).x)>settings['protectHandsBeyondX']}
 ids.update(hands);return ids,hands,counts

def distribution(values):
 v=sorted(values)
 if not v:return {'samples':0,'max':0,'p95':0,'rms':0}
 return {'samples':len(v),'max':v[-1],'p95':v[min(len(v)-1,int(.95*(len(v)-1)))],'p99':v[min(len(v)-1,int(.99*(len(v)-1)))],'rms':math.sqrt(sum(x*x for x in v)/len(v))}

def surface_errors(a,b):
 # Sample both vertex sets AND triangle centroids. Not a global Hausdorff bound.
 def one(source,target):
  tree=BVHTree.FromPolygons(target['points'],target['triangles'],all_triangles=True)
  points=[Vector(p) for p in source['points']]
  points.extend(sum((Vector(source['points'][i]) for i in t),Vector())/3 for t in source['triangles'])
  return distribution([tree.find_nearest(p)[3] for p in points])
 return {'sourceToOptimized':one(a,b),'optimizedToSource':one(b,a),'sampling':'Every vertex and triangle centroid, bidirectional Euclidean nearest surface; not full Hausdorff or screen-space proof.'}

def retained_positions(before,after,ids):
 kd=KDTree(len(after['points']))
 for i,p in enumerate(after['points']):kd.insert(p,i)
 kd.balance();dist=[kd.find(before['points'][i])[2] for i in sorted(ids)]
 return {'sourcePositions':len(ids),'withinTolerance':sum(d<=1e-7 for d in dist),'toleranceMeters':1e-7,'maxNearestVertexDistanceMeters':max(dist,default=0)}

def optimize(objects,recipe=None):
 """Mutate independent static objects, returning actual before/after diagnostics.
 Ratio is an attempted ceiling; protected seams/hands can stop reduction early.
 Every geometric boundary/material border and sharp edge is frozen. UV seams
 are frozen unless a particular recipe explicitly disables that protection.
 """
 recipe=DEFAULT_RECIPE if recipe is None else recipe.get('meshes',recipe)
 output={'schema':'male-a03-controlled-static-optimization-1','meshes':[],'preservedMeshes':[],'limitation':'Static simplification only. UV validity, sampled surface distances and frozen positions do not certify visible quality, contacts, rig weights or all intersections.'};total_before=0;total_after=0
 for obj in sorted(objects,key=lambda o:o.name):
  before=snapshot(obj);total_before+=before['triangleCount']
  if obj.name in PROTECTED_MESHES or obj.name not in recipe:
   output['preservedMeshes'].append({'name':obj.name,'geometrySha256':before['geometrySha256'],'triangles':before['triangleCount']});total_after+=before['triangleCount'];continue
  settings=recipe[obj.name];ratio=float(settings['ratio']);assert 0<ratio<=1
  normal_reference=obj.data
  assert not obj.modifiers,'Optimizer expects frozen static input, do not silently bake other modifier stacks'
  if obj.data.users>1:obj.data=obj.data.copy()
  ids,hands,edges=protected_vertices(obj,settings);old_groups=[g.name for g in obj.vertex_groups];group=obj.vertex_groups.new(name='A03_OptimizationProtection');group.add(sorted(ids),1.,'REPLACE')
  mod=obj.modifiers.new('A03_ControlledDecimate','DECIMATE');mod.decimate_type='COLLAPSE';mod.ratio=ratio;mod.use_collapse_triangulate=True;mod.vertex_group=group.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1.
  bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();evaluated=obj.evaluated_get(dg);new=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=dg);obj.modifiers.remove(mod);obj.data=new
  temporary=obj.vertex_groups.get('A03_OptimizationProtection')
  if temporary:obj.vertex_groups.remove(temporary)
  assert [g.name for g in obj.vertex_groups]==old_groups
  if new.has_custom_normals:new.normals_split_custom_set([(0,0,0)]*len(new.loops))
  for p in new.polygons:p.use_smooth=True
  new.update()
  normal_transfer=False;normal_fallbacks=0
  if settings.get('preserveReferenceNormals',False):
   # Static shoe shading only. Geometry is still the simplified mesh; do not
   # mistake normal transfer for restored lace volume or rig compatibility.
   geo_before_normals=snapshot(obj)['geometrySha256'];auto_normals=[v.vector.copy() for v in new.corner_normals]
   helper=bpy.data.objects.new('A03_ShoeNormalReference',normal_reference);bpy.context.scene.collection.objects.link(helper);helper.matrix_world=obj.matrix_world.copy();helper.hide_render=True
   new.normals_split_custom_set([(0,0,0)]*len(new.loops))
   transfer=obj.modifiers.new('A03_ShoeReferenceNormals','DATA_TRANSFER');transfer.object=helper;transfer.use_loop_data=True;transfer.data_types_loops={'CUSTOM_NORMAL'};transfer.loop_mapping='POLYINTERP_NEAREST';transfer.mix_mode='REPLACE';transfer.mix_factor=1
   bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();norm_mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg);obj.modifiers.remove(transfer);obj.data=norm_mesh;bpy.data.objects.remove(helper,do_unlink=True);new=norm_mesh;new.update();normal_transfer=new.has_custom_normals
   assert normal_transfer,'Reference split normals were not produced'
   # Nearest-surface transfer can select the opposite side of thin shoe parts.
   # Keep custom corner normals in the hemisphere of their own output face.
   fixed=[v.vector.copy() for v in new.corner_normals]
   for polygon in new.polygons:
    for loop_index in polygon.loop_indices:
     if fixed[loop_index].dot(polygon.normal)<0:
      normal_fallbacks+=1;fallback=auto_normals[loop_index]
      fixed[loop_index]=fallback if fallback.dot(polygon.normal)>0 else polygon.normal.copy()
   new.normals_split_custom_set(fixed);new.update()
   assert min(new.corner_normals[i].vector.dot(p.normal) for p in new.polygons for i in p.loop_indices)>-.001,'Reversed transferred shading normal remains'
   assert snapshot(obj)['geometrySha256']==geo_before_normals,'Normal transfer changed geometry'
  after=snapshot(obj);total_after+=after['triangleCount']
  bounds_delta=max(abs(before['bounds'][k][i]-after['bounds'][k][i]) for k in ['min','max'] for i in range(3));uv=new.uv_layers.active;finite_uv=bool(uv) and all(math.isfinite(x) for item in uv.data for x in item.uv)
  protected=retained_positions(before,after,ids);hand_result=retained_positions(before,after,hands)
  assert before['materials']==after['materials'],'Material slots changed'
  assert protected['withinTolerance']==len(ids),'Frozen boundary/UV/hand positions moved'
  output['meshes'].append({'name':obj.name,'requestedRatio':ratio,'before':{k:v for k,v in before.items() if k not in ['points','triangles']},'after':{k:v for k,v in after.items() if k not in ['points','triangles']},'protectedEdgeCounts':edges,'protectedPositions':protected,'protectedHands':hand_result,'referenceSplitNormalsTransferred':normal_transfer,'referenceNormalHemisphereFallbackCorners':normal_fallbacks,'uvFinite':finite_uv,'uvSeamsExplicitlyProtected':settings.get('protectUvSeams',True),'maxBoundsDeltaMeters':bounds_delta,'surfaceErrorMeters':surface_errors(before,after)})
 output.update(trianglesBefore=total_before,trianglesAfter=total_after,trianglesRemoved=total_before-total_after)
 return output

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--recipe');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);source=Path(a.source).resolve();out=Path(a.out).resolve();assert not out.exists(),'Fresh output required';out.mkdir(parents=True);source_sha=hashlib.sha256(source.read_bytes()).hexdigest();bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('wc_asset_id')=='chr_player_male_poc_001'];recipe=json.loads(Path(a.recipe).read_text()) if a.recipe else DEFAULT_RECIPE;start=time.time();report=optimize(objects,recipe);report.update(sourceSha256=source_sha,blender=bpy.app.version_string,seconds=time.time()-start,recipe=recipe)
 (out/'report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());bpy.ops.wm.save_as_mainfile(filepath=str(out/'optimized-probe.blend'));assert hashlib.sha256(source.read_bytes()).hexdigest()==source_sha;print(json.dumps({'trianglesBefore':report['trianglesBefore'],'trianglesAfter':report['trianglesAfter'],'meshes':[(m['name'],m['after']['triangleCount'],m['surfaceErrorMeters']['sourceToOptimized']['p95'],m['surfaceErrorMeters']['sourceToOptimized']['max']) for m in report['meshes']]}))
if __name__=='__main__':main()
