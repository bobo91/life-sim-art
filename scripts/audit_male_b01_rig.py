"""Read-only Snow rig data audit. Never executes source Text blocks or saves source."""
import argparse,collections,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Matrix
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);src=Path(a.source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);assert not any(out.iterdir()),'Audit output must be empty'
hash_before=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.context.preferences.use_preferences_save=False
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False)
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
def mat(m):return [list(r) for r in m]
def drivers(owner,label):
 ad=getattr(owner,'animation_data',None);result=[]
 if not ad:return result
 for f in ad.drivers:
  d=f.driver;variables=[]
  for v in d.variables:
   targets=[]
   for t in v.targets:
    ident=t.id;path=getattr(t,'data_path','');ok=bool(ident);error=None
    if ident and path:
     try:ident.path_resolve(path)
     except Exception as e:ok=False;error=str(e)
    bone=getattr(t,'bone_target','')
    if ident and bone and (ident.type!='ARMATURE' or bone not in ident.data.bones):ok=False;error='missing bone'
    targets.append({'id':ident.name if ident else None,'dataPath':path,'bone':bone,'resolvable':ok,'error':error})
   variables.append({'name':v.name,'type':v.type,'targets':targets})
  result.append({'owner':label,'path':f.data_path,'arrayIndex':f.array_index,'type':d.type,'expression':d.expression,'isValid':f.is_valid,'variables':variables})
 return result
rigs=[];all_drivers=[]
for o in bpy.data.objects:
 all_drivers+=drivers(o,o.name)
 if o.type!='ARMATURE':continue
 bones=[]
 for b in o.data.bones:
  pb=o.pose.bones[b.name];deformparent=b.parent
  while deformparent and not deformparent.use_deform:deformparent=deformparent.parent
  delta=b.matrix_local.inverted()@pb.matrix;loc,quat,scale=delta.decompose()
  cons=[]
  for c in pb.constraints:
   target=getattr(c,'target',None);sub=getattr(c,'subtarget','')
   cons.append({'name':c.name,'type':c.type,'mute':c.mute,'influence':c.influence,'target':target.name if target else None,'subtarget':sub,'targetBoneValid':None if not sub else bool(target and target.type=='ARMATURE' and sub in target.data.bones),'isValid':c.is_valid})
  bones.append({'name':b.name,'parent':b.parent.name if b.parent else None,'nearestDeformParent':deformparent.name if deformparent else None,'deform':b.use_deform,'head':list(b.head_local),'tail':list(b.tail_local),'length':b.length,'bboneSegments':b.bbone_segments,'inheritScale':b.inherit_scale,'restMatrix':mat(b.matrix_local),'poseMatrix':mat(pb.matrix),'matrixBasis':mat(pb.matrix_basis),'poseRestDeltaTranslation':loc.length,'poseRestDeltaAngleDegrees':math.degrees(quat.angle),'poseRestScale':list(scale),'constraints':cons})
 all_drivers+=drivers(o.data,o.name+'.data')
 rigs.append({'name':o.name,'matrixWorld':mat(o.matrix_world),'posePosition':o.data.pose_position,'boneCount':len(bones),'deformBoneCount':sum(b['deform'] for b in bones),'bones':bones})
meshes=[]
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith('GEO'):continue
 groups={g.index:g.name for g in o.vertex_groups};bone_names={b['name'] for arm in rigs for b in arm['bones'] if b['deform']};weight_sums=[];influences=[];used=collections.Counter()
 for v in o.data.vertices:
  valid=[g for g in v.groups if groups[g.group] in bone_names and g.weight>1e-8];weight_sums.append(sum(g.weight for g in valid));influences.append(len(valid))
  for g in valid:used[groups[g.group]]+=1
 mods=[]
 for m in o.modifiers:
  mods.append({'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render,'object':getattr(m,'object',None).name if getattr(m,'object',None) else None,'preserveVolume':getattr(m,'use_deform_preserve_volume',None),'vertexGroup':getattr(m,'vertex_group',None),'levels':getattr(m,'levels',None),'renderLevels':getattr(m,'render_levels',None)})
 keys=o.data.shape_keys;kv=[{'name':k.name,'value':k.value,'relative':k.relative_key.name if k.relative_key else None} for k in keys.key_blocks] if keys else []
 if keys:all_drivers+=drivers(keys,o.name+'.shape_keys')
 meshes.append({'name':o.name,'vertices':len(o.data.vertices),'parent':o.parent.name if o.parent else None,'parentType':o.parent_type,'parentBone':o.parent_bone,'matrixWorld':mat(o.matrix_world),'groups':list(groups.values()),'usedDeformGroups':dict(used),'maxInfluences':max(influences,default=0),'unweightedVertices':sum(w<1e-6 for w in weight_sums),'nonNormalizedVertices':sum(w>1e-6 and abs(w-1)>1e-4 for w in weight_sums),'weightSumRange':[min(weight_sums,default=0),max(weight_sums,default=0)],'modifiers':mods,'shapeKeys':kv})
report={'source':str(src),'sourceSha256':hash_before,'sourceUnchanged':hashlib.sha256(src.read_bytes()).hexdigest()==hash_before,'blender':bpy.app.version_string,'autoExecutionDisabled':True,'autoexecFail':bpy.app.autoexec_fail,'autoexecFailMessage':bpy.app.autoexec_fail_message,'frame':s.frame_current,'rigs':rigs,'meshes':meshes,'drivers':all_drivers,'driverCount':len(all_drivers),'invalidDrivers':sum(not d['isValid'] for d in all_drivers),'unresolvableTargets':sum(not t['resolvable'] for d in all_drivers for v in d['variables'] for t in v['targets']),'sourceActions':[{'name':x.name,'frameRange':list(x.frame_range)} for x in bpy.data.actions],'textBlocks':[{'name':t.name,'useModule':t.use_module,'lineCount':len(t.lines)} for t in bpy.data.texts],'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file),'source':im.source} for im in bpy.data.images]}
(out/'rig-audit.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
summary={'sourceUnchanged':report['sourceUnchanged'],'rigs':[{'name':r['name'],'bones':r['boneCount'],'deformBones':r['deformBoneCount'],'deformBboneSegments':{b['name']:b['bboneSegments'] for b in r['bones'] if b['deform'] and b['bboneSegments']>1},'nonRestDeformBoneCount':sum(b['deform'] and (b['poseRestDeltaTranslation']>1e-5 or b['poseRestDeltaAngleDegrees']>.01 or max(abs(x-1) for x in b['poseRestScale'])>1e-5) for b in r['bones'])} for r in rigs],'driverCount':report['driverCount'],'invalidDrivers':report['invalidDrivers'],'unresolvableTargets':report['unresolvableTargets'],'sourceActions':report['sourceActions'],'meshes':[{'name':m['name'],'vertices':m['vertices'],'maxInfluences':m['maxInfluences'],'unweightedVertices':m['unweightedVertices'],'nonNormalizedVertices':m['nonNormalizedVertices'],'modifiers':m['modifiers']} for m in meshes]}
(out/'summary.json').write_bytes((json.dumps(summary,indent=2)+'\n').encode())
print(json.dumps(summary),flush=True)
