"""One source-pinned static male quality prototype. No source rig/scripts delivered."""
import argparse,hashlib,json,math,shutil,struct,sys,time
from pathlib import Path
import bpy,bmesh
from mathutils import Vector,Matrix

parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--config',required=True);parser.add_argument('--textures',required=True);parser.add_argument('--out',required=True);parser.add_argument('--views',default='all')
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);source=Path(a.source).resolve();cfg=json.loads(Path(a.config).read_text());tex=Path(a.textures).resolve();out=Path(a.out).resolve()
if out.exists():raise FileExistsError('Preserve earlier proposal: output must be fresh')
assert hashlib.sha256(source.read_bytes()).hexdigest()==cfg['sourceBlendSha256']
out.mkdir(parents=True);(out/'textures').mkdir();(out/'renders').mkdir();start=time.time()
bpy.context.preferences.use_preferences_save=False
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
scene=bpy.context.scene;scene.frame_set(1);rig=bpy.data.objects['RIG-Snow'];head=bpy.data.objects['GEO-snow-head']
# Use only two existing artist correctives and existing lid presentation controls.
old_key_values={k.name:k.value for k in head.data.shape_keys.key_blocks}
head.data.shape_keys.animation_data_clear()
for name,value in cfg['existingArtistCorrectives'].items():head.data.shape_keys.key_blocks[name].value=value
pose_changes=[]
for side in ['L','R']:
 bone=rig.pose.bones['MSTR-Eyelid_Upper.'+side];old=list(bone.matrix.translation);bone.matrix=Matrix.Translation(Vector((0,0,cfg['upperLidWorldOffsetZ'])))@bone.matrix
 pose_changes.append({'bone':bone.name,'before':old,'after':list(bone.matrix.translation)})
 if cfg.get('mouthCornerWorldOffsetZ',0):
  corner=rig.pose.bones['ACT-Lips_Corner.'+side];old=list(corner.matrix.translation);corner.matrix=Matrix.Translation(Vector((0,0,cfg['mouthCornerWorldOffsetZ'])))@corner.matrix;pose_changes.append({'bone':corner.name,'before':old,'after':list(corner.matrix.translation)})
# Source T-rest pose stays intact. Subdivision choice is an explicit static budget decision.
for o in scene.objects:
 if o.type=='MESH' and o.name.startswith('GEO'):
  for m in o.modifiers:
   if m.type=='SUBSURF':m.levels=cfg['surfaceSubdivision'];m.render_levels=cfg['surfaceSubdivision']
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
source_names=['GEO-snow-body','GEO-snow-head','GEO-snow-eyes','GEO-snow-eyebrows','GEO-snow-hair_base','GEO-snow-shirt','GEO-snow-pants','GEO-snow-shoes_base','GEO-snow-shoes_bottom','GEO-snow-shoes_parts']
collection=bpy.data.collections.new('WC_StaticMale');scene.collection.children.link(collection);asset=[];source_slots={};hair_components=[];loose_cleanup=[]
for name in source_names:
 o=bpy.data.objects[name];ev=o.evaluated_get(deps);mesh=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps);mesh.transform(o.matrix_world)
 label=name.removeprefix('GEO-snow-');obj=bpy.data.objects.new('M01_'+label,mesh);collection.objects.link(obj);obj['wc_asset_id']=cfg['assetId'];obj['source_object']=name;asset.append(obj)
 source_slots[obj.name]=[s.material.name if s.material else None for s in o.material_slots]
 if name=='GEO-snow-hair_base':
  assert len(mesh.vertices)==3418,'Hair topology changed from inspected source'
  adj=[set() for _ in mesh.vertices]
  for e in mesh.edges:i,j=e.vertices;adj[i].add(j);adj[j].add(i)
  left=set(range(len(adj)))
  while left:
   i=min(left);seen={i};queue=[i];left.remove(i)
   for v in queue:
    for j in adj[v]:
     if j not in seen:seen.add(j);queue.append(j);left.discard(j)
   hair_components.append(sorted(seen))
  bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();remove=set(i for n in cfg['hair']['removeSourceComponents'] for i in hair_components[n]);bmesh.ops.delete(bm,geom=[bm.verts[i] for i in sorted(remove)],context='VERTS');bm.to_mesh(mesh);bm.free()
  for v in mesh.vertices:
   weight=max(0,min(1,(v.co.z-1.68)/.13));v.co.z=1.68+(v.co.z-1.68)*(1-(1-cfg['hair']['frontCrownScaleZ'])*weight);v.co.x+=cfg['hair']['sweepMetersX']*weight
 if name=='GEO-snow-eyebrows':
  for v in mesh.vertices:v.co.z+=cfg['browInnerRaiseMeters']*max(0,1-abs(v.co.x)/.07)
 bm=bmesh.new();bm.from_mesh(mesh);loose=[v for v in bm.verts if not v.link_faces];before_faces=len(bm.faces);removed=len(loose)
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 assert len(bm.faces)==before_faces,'Loose cleanup must never remove a surface face'
 bm.to_mesh(mesh);bm.free();loose_cleanup.append({'mesh':obj.name,'unreferencedVerticesRemoved':removed,'surfaceFacesRemoved':0})
 render_uv=next((u.name for u in mesh.uv_layers if u.active_render),None)
 if render_uv:
  for layer in list(mesh.uv_layers):
   if layer.name!=render_uv:mesh.uv_layers.remove(layer)
  mesh.uv_layers.active_index=0
 for p in mesh.polygons:p.use_smooth=True
# Remove all source objects and executable rig content from this independent scene.
for o in list(bpy.data.objects):
 if o not in asset:bpy.data.objects.remove(o,do_unlink=True)
for t in list(bpy.data.texts):bpy.data.texts.remove(t)
for arm in list(bpy.data.armatures):bpy.data.armatures.remove(arm)
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
for mat in list(bpy.data.materials):
 if mat.users==0:bpy.data.materials.remove(mat)
for obj in asset:
 if obj.animation_data:obj.animation_data_clear()
 indices=[p.material_index for p in obj.data.polygons]
 obj.data.materials.clear()
 for old in source_slots[obj.name]:obj.data.materials.append(None)
 for poly,index in zip(obj.data.polygons,indices):poly.material_index=index
 for layer in list(obj.data.color_attributes):obj.data.color_attributes.remove(layer)
# Stable vertex/face topology, frozen world positions, feet-centered metre contract.
pts=[v.co.copy() for o in asset for v in o.data.vertices];lo=Vector([min(v[k] for v in pts) for k in range(3)]);hi=Vector([max(v[k] for v in pts) for k in range(3)]);scale=cfg['heightMeters']/(hi.z-lo.z);offset=Vector(((lo.x+hi.x)*.5,(lo.y+hi.y)*.5,lo.z))
for o in asset:
 for v in o.data.vertices:v.co=(v.co-offset)*scale
 o.data.update()
root=bpy.data.objects.new('CHR_PlayerMale_A01',None);collection.objects.link(root);root['wc_asset_id']=cfg['assetId'];root['license']='CC-BY-4.0';root['source']='https://studio.blender.org/characters/snow/v4/';root['attribution']='Snow Rig (CC) Blender Foundation | studio.blender.org';root['phase']='A static prototype; no rig or animations'
for o in asset:o.parent=root
loaded={}
def image(name,noncolor=False):
 if name not in loaded:
  src=tex/name;dst=out/'textures'/name;shutil.copyfile(src,dst);loaded[name]=bpy.data.images.load(str(dst),check_existing=False)
  if noncolor:loaded[name].colorspace_settings.name='Non-Color'
 return loaded[name]
def pbr(name,color,base=None,tint=None,normal=None,rough=.6,roughmap=None):
 m=bpy.data.materials.new('M01_'+name);m.use_nodes=True;nodes=m.node_tree.nodes;links=m.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=0;bs.inputs['Specular IOR Level'].default_value=cfg['hair'].get('specularIorLevel',.5) if name=='hair' else cfg['materials'].get('shirtSpecularIorLevel',.5) if name=='shirt' else .5
 if name.startswith('skin'):bs.inputs['Subsurface Weight'].default_value=cfg['materials']['skinSubsurfaceWeight']
 if tint:
  base={'skin_darker':'skin_darker_diffuse_atlas.png','skin_upper_lip':'skin_upper_lip_diffuse_atlas.png','skin_lower_lip':'skin_lower_lip_diffuse_atlas.png','pants':'pants_tinted_diffuse.png'}[name];tint=None
 if base:
  t=nodes.new('ShaderNodeTexImage');t.image=image(base);socket=t.outputs['Color']
  if tint:
   mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*tint,1);links.new(socket,mix.inputs[1]);socket=mix.outputs[0]
  links.new(socket,bs.inputs['Base Color'])
 if roughmap:
  t=nodes.new('ShaderNodeTexImage');t.image=image(roughmap,True);links.new(t.outputs['Color'],bs.inputs['Roughness'])
 if normal:
  t=nodes.new('ShaderNodeTexImage');t.image=image(normal,True);n=nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.5;links.new(t.outputs['Color'],n.inputs['Color']);links.new(n.outputs['Normal'],bs.inputs['Normal'])
 return m
mc=cfg['materials'];skin_tints={'snow.skin':None,'snow.skin_darker':(.65,.58,.54),'snow.skin_upper_lip':(.90,.71,.68),'snow.skin_lower_lip':(.96,.80,.76)}
materials={}
for old,tint in skin_tints.items():materials[old]=pbr(old.replace('snow.',''),(.5,.3,.22),'skin_diffuse_atlas.png',tint=tint,rough=mc['skinRoughness'])
materials['snow.hair']=pbr('hair',cfg['hair']['baseColorLinear'],rough=cfg['hair']['roughness'])
materials['snow.eyes']=pbr('eyes',(1,1,1),'eyes_diffuse.png',normal='eyes_normal.png',rough=mc['eyeRoughness'])
materials['snow.shirt']=pbr('shirt',mc['shirtBaseColorLinear'],normal='shirt_normal.png',rough=mc['shirtRoughness'])
materials['snow.pants']=pbr('pants',(.12,.2,.28),'pants_diffuse.png',tint=mc['pantsTint'],normal='pants_normal.png',roughmap='pants_roughness.png')
materials['snow.shoe']=pbr('canvas_shoes',(.6,.55,.45),'shoes_diffuse.png',normal='shoes_normal.png',roughmap='shoes_roughness.png')
atlas=json.loads((tex/'atlas-mapping.json').read_text())
for o in asset:
 slots=source_slots[o.name]
 for i,name in enumerate(slots):o.data.materials[i]=materials[name]
 if all(n and n.startswith('snow.skin') for n in slots):
  uv=o.data.uv_layers.active
  for poly in o.data.polygons:
   values=[uv.data[i].uv.copy() for i in poly.loop_indices];u=sum(v.x for v in values)/len(values);v=sum(v.y for v in values)/len(values);tile=1001+math.floor(u+1e-7)+10*math.floor(v+1e-7)
   if str(tile) not in atlas['tiles']:raise ValueError('Unmapped skin UV tile '+str(tile))
   mapping=atlas['tiles'][str(tile)]
   for i in poly.loop_indices:
    old=uv.data[i].uv.copy();uv.data[i].uv=((old.x-mapping['source_uv_origin'][0])*mapping['scale'][0]+mapping['offset'][0],(old.y-mapping['source_uv_origin'][1])*mapping['scale'][1]+mapping['offset'][1])
# Purge unused source datablocks; only new PBR images/materials survive in delivery.
for m in list(bpy.data.materials):
 if m not in materials.values():bpy.data.materials.remove(m)
for im in list(bpy.data.images):
 if im not in loaded.values():bpy.data.images.remove(im)
for me in list(bpy.data.meshes):
 if me.users==0:bpy.data.meshes.remove(me)
for im in loaded.values():im.pack()
def metrics(o):
 me=o.data;me.calc_loop_triangles();pts=[o.matrix_world@v.co for v in me.vertices];digest=hashlib.sha256()
 for v in pts:digest.update(struct.pack('<3f',*v))
 for t in me.loop_triangles:digest.update(struct.pack('<3I',*t.vertices))
 return {'name':o.name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'boundsWorld':{'min':[min(v[k] for v in pts) for k in range(3)],'max':[max(v[k] for v in pts) for k in range(3)]},'geometrySha256':digest.hexdigest(),'materials':[m.name for m in me.materials]}
bpy.context.view_layer.update();items=[metrics(o) for o in asset];glo=[min(m['boundsWorld']['min'][k] for m in items) for k in range(3)];ghi=[max(m['boundsWorld']['max'][k] for m in items) for k in range(3)]
report={'assetId':cfg['assetId'],'phase':'A','sourceBlendSha256':cfg['sourceBlendSha256'],'blender':bpy.app.version_string,'meshes':items,'dimensionsMeters':[ghi[k]-glo[k] for k in range(3)],'boundsWorld':{'min':glo,'max':ghi},'triangles':sum(m['triangles'] for m in items),'materialCount':len(materials),'meshCount':len(asset),'rigsDelivered':0,'animationsDelivered':0,'embeddedTextScripts':len(bpy.data.texts),'looseGeometryCleanup':loose_cleanup,'hairComponentsBefore':len(hair_components),'hairComponentsRemoved':cfg['hair']['removeSourceComponents'],'existingLidControlPose':pose_changes,'existingCorrectives':cfg['existingArtistCorrectives'],'nativeHeadShapeKeyValuesBefore':old_key_values,'heightScaleApplied':scale,'sourceTposePreserved':True,'exportCleanup':'Polygon material indices preserved across slot replacement; unused source color attributes removed to avoid glTF vertex-color multiplication','uvSelection':'Source render-active UVMap retained; auxiliary edit-active tattoo_light_map removed','omittedInvisibleSourceParts':['internal teeth/gums/tongue','eye-dot overlay','corneal shell','rig/deformation helpers/widgets'],'limitation':'Static prototype. Source face family remains; no identity-range, skinning, animation or production Unity certification.'}
(out/'asset-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
# Export only the actual static character, never the presentation floor/lights/camera.
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in asset:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(out/(cfg['assetId']+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False)
# Neutral presentation, kept outside the exported selection.
h=cfg['heightMeters'];target=Vector((0,0,h*.50))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('WC_PresentationWorld');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.58,.61,.66,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35;scene.world=world
rc_light_multiplier=cfg['render'].get('lightPowerMultiplier',1)
for name,xyz,power,size in [('WC_Key',(-1.5,-2,2.2),500,.95),('WC_Fill',(1.8,-.7,1.3),180,1.25),('WC_Rim',(1,1.5,2),300,1)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power*h*h*rc_light_multiplier;data.shape='DISK';data.size=size*h;ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=target+Vector(xyz)*h;aim(ob,target)
bpy.ops.mesh.primitive_plane_add(size=200*h,location=(0,0,-.003));floor=bpy.context.object;floor.name='WC_PresentationFloor_NotAsset';fm=pbr('presentation_floor',(.56,.52,.45),rough=.9);floor.data.materials.append(fm)
cd=bpy.data.cameras.new('WC_ReviewCamera');camera=bpy.data.objects.new('WC_ReviewCamera',cd);scene.collection.objects.link(camera);scene.camera=camera
rc=cfg['render'];scene.render.engine=rc['engine'];scene.cycles.device=rc['device'];scene.cycles.samples=rc['samples'];scene.cycles.use_denoising=rc['denoise'];scene.cycles.seed=cfg['seed'];scene.render.threads_mode='FIXED';scene.render.threads=rc['threads'];scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.view_transform=rc['viewTransform'];scene.view_settings.exposure=rc['exposure'];scene.view_settings.gamma=1
views=[('front',0,'full'),('side',90,'full'),('back',180,'full'),('three_quarter',35,'full'),('face_front',0,'face'),('face_three_quarter',35,'face'),('near_third_person',35,'near'),('game_16m_front',0,'game'),('game_16m_back',180,'game')]
requested={v.strip() for v in a.views.split(',')};metaviews=[]
for name,az,kind in views:
 if a.views!='all' and name not in requested:continue
 ang=math.radians(az);focus=Vector((0,-.03 if kind=='face' else 0,h*(.88 if kind=='face' else .50)))
 if kind in {'full','face'}:
  cd.type='ORTHO';cd.sensor_fit='AUTO';cd.ortho_scale=h*(.31 if kind=='face' else 1.23);camera.location=focus+Vector((math.sin(ang)*h*3,-math.cos(ang)*h*3,0));scene.render.resolution_x,scene.render.resolution_y=rc['faceResolution' if kind=='face' else 'fullResolution']
 else:
  cd.type='PERSP';cd.sensor_fit='VERTICAL';cd.sensor_height=32;cd.lens=32/(2*math.tan(math.radians(40)/2));dist=16 if kind=='game' else 3.2;elev=math.radians(50 if kind=='game' else 15);camera.location=focus+Vector((dist*math.cos(elev)*math.sin(ang),-dist*math.cos(elev)*math.cos(ang),dist*math.sin(elev)));scene.render.resolution_x,scene.render.resolution_y=rc['gameResolution' if kind=='game' else 'fullResolution']
 aim(camera,focus);scene.render.filepath=str(out/'renders'/(name+'.png'));bpy.ops.render.render(write_still=True);after=[metrics(o)['geometrySha256'] for o in asset];assert after==[m['geometrySha256'] for m in items]
 metaviews.append({'view':name,'cameraType':cd.type,'location':list(camera.location),'focus':list(focus),'distanceMeters':(camera.location-focus).length,'verticalFovDegrees':math.degrees(cd.angle_y) if cd.type=='PERSP' else None,'orthoScale':cd.ortho_scale if cd.type=='ORTHO' else None,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'sameAssetGeometryVerified':True})
# Save the editable source with the review environment and no third-party executable text.
cd.type='ORTHO';cd.sensor_fit='AUTO';cd.ortho_scale=h*1.23;camera.location=target+Vector((h*1.72,-h*2.46,h*.04));aim(camera,target);scene.render.resolution_x,scene.render.resolution_y=rc['fullResolution']
bpy.ops.wm.save_as_mainfile(filepath=str(out/'character.blend'))
(out/'render-metadata.json').write_text(json.dumps({'views':metaviews,'renderConfig':rc,'seed':cfg['seed'],'imageRetouching':False,'elapsedBuildSeconds':time.time()-start},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'assetId':cfg['assetId'],'triangles':report['triangles'],'meshes':len(asset),'materials':len(materials),'renders':len(metaviews),'durationSeconds':time.time()-start}),flush=True)
