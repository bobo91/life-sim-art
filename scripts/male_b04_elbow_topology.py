"""B04 one local elbow-loop recovery using preserved A03-high density as guide.
Existing neutral surface is partitioned, not sculpted; only local skin weights change.
"""
import math,json,hashlib,struct
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def _smooth(t):
 t=max(0.0,min(1.0,t));return t*t*(3-2*t)
def _quantile(values,q):
 x=(len(values)-1)*q;i=int(x);j=min(i+1,len(values)-1);return values[i]*(j-x)+values[j]*(x-i) if i!=j else values[i]
def _mesh_snapshot(obj):
 me=obj.data;me.calc_loop_triangles();return {'points':[v.co.copy() for v in me.vertices],'triangles':[tuple(t.vertices) for t in me.loop_triangles],'triangleUvs':[[tuple(me.uv_layers.active.data[i].uv) for i in t.loops] for t in me.loop_triangles],'uv':[[tuple(u.uv) for u in layer.data] for layer in me.uv_layers],'materials':[m.name for m in me.materials],'weights':[{g.group:g.weight for g in v.groups} for v in me.vertices]}
def recover(body,rig,high_reference,config):
 """Partition only elbow faces with high-guided cross sections; return measured deltas.
 high_reference is a list of neutral A03-high M01_body coordinates.
 """
 import bmesh
 assert body.name=='M01_body' and body.data.shape_keys is None and len(rig.data.bones)==58
 old=_mesh_snapshot(body);oldpoints=old['points'];tree=BVHTree.FromPolygons(oldpoints,old['triangles'],all_triangles=True)
 names={g.name:g.index for g in body.vertex_groups};zones={};width=config['weightHalfWidthMeters'];radius=config['radialLimitMeters'];guidewidth=config['guideHalfWidthMeters']
 for side in ['L','R']:
  a='UpperArm.'+side;b='LowerArm.'+side;s='B02_Elbow.'+side;c=rig.data.bones[b].head_local.copy();axis=(c-rig.data.bones[a].head_local).normalized();longs=[]
  for p in high_reference:
   delta=Vector(p)-c;long=delta.dot(axis);rad=(delta-axis*long).length
   if abs(long)<=guidewidth and rad<radius:longs.append(long)
  longs.sort();assert len(longs)>70
  levels=[round(_quantile(longs,q)/config['guideSnapMeters'])*config['guideSnapMeters'] for q in config['guideQuantiles']]+[0.0];levels=sorted(set(levels))
  assert len(levels)==7 and all(abs(x)<guidewidth for x in levels),levels
  zones[side]={'center':c,'axis':axis,'levels':levels,'highGuideVertices':len(longs),'groups':(names[a],names[b],names[s])}
 bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();original=list(bm.verts);deform=bm.verts.layers.deform.verify();added_by_side={}
 for side,z in zones.items():
  before=len(bm.verts)
  for level in z['levels']:
   # Selection includes every face crossing the arm tube at this local plane.
   faces=[]
   for f in bm.faces:
    ds=[v.co-z['center'] for v in f.verts];longs=[d.dot(z['axis']) for d in ds]
    if min(longs)>level+1e-7 or max(longs)<level-1e-7:continue
    if not all((d-z['axis']*d.dot(z['axis'])).length<radius for d in ds):continue
    if not any(abs(x)<config['localFaceHalfWidthMeters'] for x in longs):continue
    faces.append(f)
   edges={ed for f in faces for ed in f.edges};verts={v for f in faces for v in f.verts};assert len(faces)>3,(side,level,len(faces))
   bmesh.ops.bisect_plane(bm,geom=faces+list(edges)+list(verts),dist=1e-7,plane_co=z['center']+z['axis']*level,plane_no=z['axis'],clear_inner=False,clear_outer=False,use_snap_center=False)
  added_by_side[side]=len(bm.verts)-before
 # Split resulting coplanar quads deterministically; no neutral coordinate relaxation.
 ngons=[f for f in bm.faces if len(f.verts)>3]
 bmesh.ops.triangulate(bm,faces=ngons,quad_method='BEAUTY',ngon_method='BEAUTY')
 weight_changes={};newset=set(bm.verts)-set(original);old_weight_changes=0
 for side,z in zones.items():
  ia,ib,isp=z['groups'];count=0;newcount=0
  for v in bm.verts:
   d=v.co-z['center'];long=d.dot(z['axis']);rad=(d-z['axis']*long).length
   if abs(long)>=width or rad>=radius:continue
   w=v[deform];mass=w.get(ia,0)+w.get(ib,0)+w.get(isp,0)
   if mass<.8:continue
   oldw=dict(w)
   # Proximal->half-angle->distal avoids direct mixing of full-hinge rotations.
   q=min(1.0,abs(long)/width)
   target={ia:mass*q if long<0 else 0.0,ib:mass*q if long>=0 else 0.0,isp:mass*(1-q)}
   edgeblend=_smooth((width-abs(long))/config['weightBoundaryFadeMeters'])
   for g in [ia,ib,isp]:w[g]=oldw.get(g,0)*(1-edgeblend)+target[g]*edgeblend
   # Existing non-elbow group memberships are retained. Normalize only this local set.
   total=sum(w.values());assert total>1e-6
   for g in list(w.keys()):
    value=w[g]/total
    if value<1e-8:del w[g]
    else:w[g]=value
   assert len(w)<=4,(side,len(w))
   if any(abs(w.get(g,0)-oldw.get(g,0))>1e-7 for g in set(w.keys())|set(oldw)):
    count+=1
    if v in newset:newcount+=1
    else:old_weight_changes+=1
  weight_changes[side]={'localVerticesReweighted':count,'newVerticesReweighted':newcount}
 # Existing points are kept byte-for-byte in neutral; no whole-arm or boundary drift.
 assert all((v.co-oldpoints[i]).length==0 for i,v in enumerate(original))
 bm.verts.index_update();bm.faces.index_update();mapping={i:v.index for i,v in enumerate(original)};newids=sorted(v.index for v in newset)
 source_ids=set(original)
 outside_weights_exact=True
 for i,v in enumerate(original):
  inside=any(abs((v.co-z['center']).dot(z['axis']))<width and ((v.co-z['center'])-z['axis']*(v.co-z['center']).dot(z['axis'])).length<radius for z in zones.values())
  if not inside:
   assert dict(v[deform])==old['weights'][i],('outside weights',i)
 bm.to_mesh(body.data);bm.free();body.data.update();body.data.calc_loop_triangles();newpoints=[v.co.copy() for v in body.data.vertices]
 max_new_error=max((tree.find_nearest(newpoints[i])[3] for i in newids),default=0.0);assert max_new_error<config['maxNeutralSurfaceErrorMeters'],max_new_error
 assert len(body.data.materials)==len(old['materials']) and [m.name for m in body.data.materials]==old['materials']
 assert all(len(p.vertices)==3 and p.area>1e-12 for p in body.data.polygons)
 # Preserve every old triangle fully outside both local face bands, modulo index mapping.
 afterfaces={tuple(sorted(p.vertices)) for p in body.data.polygons};outside_faces=0
 for tri in old['triangles']:
  local=False
  for z in zones.values():
   ds=[oldpoints[i]-z['center'] for i in tri]
   if any(abs(d.dot(z['axis']))<config['localFaceHalfWidthMeters'] and (d-z['axis']*d.dot(z['axis'])).length<radius for d in ds):local=True
  if not local:assert tuple(sorted(mapping[i] for i in tri)) in afterfaces;outside_faces+=1
 # Surface/UV interpolation check for all new loops against their original source triangles.
 uv_error=0.0
 if body.data.uv_layers:
  from mathutils.geometry import barycentric_transform
  original_uv=old['triangleUvs']
  for poly in body.data.polygons:
   for li in poly.loop_indices:
    vi=body.data.loops[li].vertex_index
    if vi not in newids:continue
    point=newpoints[vi];got=body.data.uv_layers.active.data[li].uv;errors=[]
    # A new corner may lie exactly on an old UV seam. Compare against each
    # geometrically valid source chart, using true loop_triangle UV ordering.
    for near,normal,ti,dist in tree.find_nearest_range(point,1e-6):
     tri=old['triangles'][ti];uvs=original_uv[ti];want=barycentric_transform(near,*[oldpoints[i] for i in tri],*[Vector((uv[0],uv[1],0)) for uv in uvs]);errors.append(math.hypot(got.x-want.x,got.y-want.y))
    assert errors
    uv_error=max(uv_error,min(errors))
  assert uv_error<1e-5,uv_error
 return {'schema':'male-b04-local-topology-1','method':'Seven A03-high quantile-guided cross-section cuts per elbow, exact old neutral surface, local three-joint skin field','verticesBefore':len(oldpoints),'verticesAfter':len(newpoints),'verticesAdded':len(newpoints)-len(oldpoints),'trianglesBefore':len(old['triangles']),'trianglesAfter':len(body.data.loop_triangles),'trianglesAdded':len(body.data.loop_triangles)-len(old['triangles']),'addedBySide':added_by_side,'newVertexIds':newids,'oldVertexIndexMap':mapping,'oldNeutralPointsExact':True,'outsideLocalWeightsExact':outside_weights_exact,'outsideFacesPreserved':outside_faces,'maxNewVertexNeutralSurfaceErrorMeters':max_new_error,'newLoopUvDiagnosticMaxDifference':uv_error,'weights':weight_changes,'oldVerticesLocallyReweighted':old_weight_changes,'uvValidationMethod':'True source loop_triangle ordering and all valid sourcecharts within1micron','guide':{s:{'center':list(z['center']),'axis':list(z['axis']),'levelsMeters':z['levels'],'highGuideVertices':z['highGuideVertices']} for s,z in zones.items()},'bones':len(rig.data.bones),'newMorphs':False,'limits':'Longitudinal sampling recovery only; low neutral circumferential outline retained. Visual gate must judge remaining facets/notches, both sides.'}

def _main():
 import bpy,sys,argparse
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--config',default='configs/male-neutral-b04-elbow.json');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r=Path.cwd();out=r/a.out;out.mkdir(parents=True,exist_ok=True);cfg=json.loads((r/a.config).read_text(encoding='utf-8'));src=r/cfg['source'];high=r/cfg['highReference'];srcsha=hashlib.sha256(src.read_bytes()).hexdigest();hisha=hashlib.sha256(high.read_bytes()).hexdigest();assert srcsha==cfg['sourceSha256'];assert not (out/'candidate.blend').exists()
 bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(high),load_ui=False,use_scripts=False);hp=[tuple(v.co) for v in bpy.data.objects['M01_body'].data.vertices];bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False);rig=bpy.data.objects['A03_B01_Rig'];body=bpy.data.objects['M01_body'];result=recover(body,rig,hp,cfg);result.update(sourceSha256=srcsha,highReferenceSha256=hisha,config=cfg);bpy.ops.wm.save_as_mainfile(filepath=str(out/'candidate.blend'));assert hashlib.sha256(src.read_bytes()).hexdigest()==srcsha and hashlib.sha256(high.read_bytes()).hexdigest()==hisha;(out/'report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items() if k not in ['oldVertexIndexMap','newVertexIds','config']},indent=2),flush=True)
if __name__=='__main__':_main()
