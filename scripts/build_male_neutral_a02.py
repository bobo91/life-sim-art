"""A02 geometry-first static visual iteration; reuses immutable A01 scene/export contract."""
import argparse,hashlib,json,math,shutil,struct,sys,time
from pathlib import Path
import bpy,bmesh
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from male_a02_form import deform,skin_point,bell
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--config',required=True);p.add_argument('--textures',required=True);p.add_argument('--out',required=True);p.add_argument('--views',default='all');p.add_argument('--clay-comparison',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
source=Path(a.source).resolve();cfg=json.loads(Path(a.config).read_text());tex=Path(a.textures).resolve();out=Path(a.out).resolve();assert hashlib.sha256(source.read_bytes()).hexdigest()==cfg['sourceA01BlendSha256'];assert not out.exists(),'Use fresh output, preserve earlier results'
out.mkdir(parents=True);(out/'textures').mkdir();(out/'renders').mkdir();start=time.time();bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
scene=bpy.context.scene;asset=[o for o in scene.objects if o.type=='MESH' and o.get('wc_asset_id')==cfg['assetId']];root=bpy.data.objects['CHR_PlayerMale_A01'];root['iteration']='A02';root['modifications']='Geometry-first oval face, smaller ears/nose/lips/eyes, new swept quiff; static only';c=cfg['identityEdit']
def metrics(o):
 me=o.data;me.calc_loop_triangles();ps=[o.matrix_world@v.co for v in me.vertices];d=hashlib.sha256()
 for v in ps:d.update(struct.pack('<3f',*v))
 for t in me.loop_triangles:d.update(struct.pack('<3I',*t.vertices))
 return {'name':o.name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'boundsWorld':{'min':[min(v[k] for v in ps) for k in range(3)],'max':[max(v[k] for v in ps) for k in range(3)]},'geometrySha256':d.hexdigest(),'materials':[m.name for m in me.materials]}
before={o.name:metrics(o) for o in asset};head=bpy.data.objects['M01_head'];head_before=[tuple(v.co) for v in head.data.vertices];head_faces=[tuple(p.vertices) for p in head.data.polygons];head_uv=[tuple(v.uv) for v in head.data.uv_layers.active.data]
changes=[]
for obj in asset:
 if obj.name not in ['M01_head','M01_eyes','M01_eyebrows','M01_hair_base']:continue
 for v in obj.data.vertices:
  old=v.co.copy()
  if obj.name=='M01_eyes':
   side=1 if old.x>0 else -1;cx=side*.043442;cy=-.0458;cz=1.5813;s=c['eyeUniformScale'];v.co=(cx*c['eyeCenterWidthScale']+(old.x-cx)*s,cy+(old.y-cy)*s,cz+(old.z-cz)*s)
  elif obj.name=='M01_head':v.co=skin_point(old,c)
  else:
   v.co=deform(old,c)
   if obj.name=='M01_eyebrows':v.co.z=1.616+(v.co.z-1.616)*c['browThicknessScale']+.0018*bell(abs(old.x),.050,.024)-.0005*bell(abs(old.x),.076,.012)
 if obj.data.has_custom_normals:obj.data.normals_split_custom_set([(0,0,0)]*len(obj.data.loops))
 obj.data.update();changes.append(obj.name)
# Retain only the authored scalp cap; replace every retained braided crown with original broad swept forms.
hair=bpy.data.objects['M01_hair_base'];bm=bmesh.new();bm.from_mesh(hair.data);bm.verts.ensure_lookup_table();seen={bm.verts[0]};q=[bm.verts[0]]
for v in q:
 for e in v.link_edges:
  j=e.other_vert(v)
  if j not in seen:seen.add(j);q.append(j)
cap_vertices=len(seen);bmesh.ops.delete(bm,geom=[v for v in list(bm.verts) if v not in seen],context='VERTS')
paths=[
 [(-.047,-.087,1.677,.044,.015),(-.037,-.050,1.711,.046,.019),(-.010,-.012,1.731,.047,.018),(.027,.037,1.730,.034,.016),(.056,.102,1.697,.014,.009),(.054,.123,1.678,.003,.002)],
 [(-.003,-.083,1.677,.032,.014),(.006,-.053,1.706,.034,.016),(.032,-.010,1.724,.030,.015),(.059,.038,1.718,.023,.012),(.080,.096,1.676,.004,.003)],
 [(.035,-.075,1.674,.028,.014),(.049,-.050,1.701,.027,.014),(.070,-.008,1.716,.023,.014),(.087,.045,1.691,.018,.010),(.084,.099,1.659,.003,.002)]]
def cat(path,t):
 t=max(0,min(len(path)-1-1e-7,t));i=int(t);u=t-i;v=[path[max(0,min(len(path)-1,j))] for j in [i-1,i,i+1,i+2]]
 return [0.5*((2*v[1][k])+(-v[0][k]+v[2][k])*u+(2*v[0][k]-5*v[1][k]+4*v[2][k]-v[3][k])*u*u+(-v[0][k]+3*v[1][k]-3*v[2][k]+v[3][k])*u*u*u) for k in range(5)]
for path in paths:
 rings=[];centers=[]
 for n in range(19):
  t=n/18*(len(path)-1);data=cat(path,t);center=Vector(data[:3]);centers.append(center);tangent=Vector(cat(path,min(t+.005,len(path)-1-1e-6))[:3])-Vector(cat(path,max(t-.005,0))[:3]);tangent.normalize();side=Vector((tangent.y,-tangent.x,0)).normalized();up=side.cross(tangent).normalized()
  if up.z<0:up=-up
  ring=[]
  for j in range(12):
   angle=j*2*math.pi/12;pt=center+side*(max(.001,data[3])*math.cos(angle))+up*(max(.001,data[4])*math.sin(angle));ring.append(bm.verts.new(deform(pt,c)))
  rings.append(ring)
 for n in range(len(rings)-1):
  for j in range(12):bm.faces.new((rings[n][j],rings[n][(j+1)%12],rings[n+1][(j+1)%12],rings[n+1][j]))
 for index,reverse in [(0,True),(-1,False)]:
  center=bm.verts.new(deform(centers[index],c))
  for j in range(12):bm.faces.new((center,rings[index][(j+1)%12],rings[index][j]) if reverse else (center,rings[index][j],rings[index][(j+1)%12]))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(hair.data);bm.free()
for poly in hair.data.polygons:poly.use_smooth=True;poly.material_index=0
hair.data.update()
assert head_faces==[tuple(p.vertices) for p in head.data.polygons];assert head_uv==[tuple(v.uv) for v in head.data.uv_layers.active.data]
# Replace texture references, keep ordinary core dielectric PBR to avoid unsupported specular extension.
materials={m.name:m for o in asset for m in o.data.materials};loaded={}
for mat in materials.values():
 bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Specular IOR Level'].default_value=.5;bs.inputs['IOR'].default_value=1.5;bs.inputs['Coat Weight'].default_value=0;bs.inputs['Sheen Weight'].default_value=0;bs.inputs['Subsurface Weight'].default_value=0
 if 'skin' in mat.name:bs.inputs['Roughness'].default_value=cfg['materials']['lipRoughness'] if 'lip' in mat.name else cfg['materials']['skinRoughness']
 elif mat.name=='M01_hair':bs.inputs['Base Color'].default_value=(*cfg['hair']['baseColorLinear'],1);bs.inputs['Roughness'].default_value=cfg['hair']['roughness']
 elif mat.name=='M01_eyes':bs.inputs['Roughness'].default_value=cfg['materials']['eyeRoughness']
 elif mat.name=='M01_shirt':bs.inputs['Roughness'].default_value=cfg['materials']['shirtRoughness']
 for node in mat.node_tree.nodes:
  if node.type!='TEX_IMAGE' or not node.image:continue
  name=Path(node.image.filepath).name
  if name not in loaded:
   dest=out/'textures'/name;shutil.copy2(tex/name,dest);im=bpy.data.images.load(str(dest),check_existing=False);im.colorspace_settings.name=node.image.colorspace_settings.name;im.pack();loaded[name]=im
  node.image=loaded[name]
for im in list(bpy.data.images):
 if not im.users:bpy.data.images.remove(im)
items=[metrics(o) for o in asset];lo=[min(m['boundsWorld']['min'][k] for m in items) for k in range(3)];hi=[max(m['boundsWorld']['max'][k] for m in items) for k in range(3)]
unchanged=[o.name for o in asset if o.name not in changes]
for name in unchanged:assert before[name]['geometrySha256']==next(m['geometrySha256'] for m in items if m['name']==name)
# Sample field Jacobian on every head vertex: catches local foldovers, not all intersections.
dets=[];step=1e-5
for point in head_before:
 cols=[]
 for k in range(3):
  plus=list(point);minus=list(point);plus[k]+=step;minus[k]-=step;cols.append((Vector(skin_point(plus,c))-Vector(skin_point(minus,c)))/(2*step))
 dets.append(Matrix(cols).transposed().determinant())
assert min(dets)>0,'Head deformation locally inverted'
displacements=[(v.co-Vector(old)).length for v,old in zip(head.data.vertices,head_before)]
report={'assetId':cfg['assetId'],'iteration':'A02','phase':'A','blender':bpy.app.version_string,'sourceBlendSha256':cfg['sourceBlendSha256'],'sourceA01BlendSha256':cfg['sourceA01BlendSha256'],'meshes':items,'dimensionsMeters':[hi[k]-lo[k] for k in range(3)],'boundsWorld':{'min':lo,'max':hi},'triangles':sum(m['triangles'] for m in items),'materialCount':len(materials),'meshCount':len(asset),'rigsDelivered':0,'animationsDelivered':0,'embeddedTextScripts':len(bpy.data.texts),'headTopologyAndUvPreserved':True,'headFieldJacobianDeterminant':{'min':min(dets),'max':max(dets),'sampledVertices':len(dets)},'headDisplacementMeters':{'max':max(displacements),'mean':sum(displacements)/len(displacements)},'unchangedBodyClothesShoes':unchanged,'sourceHairCapVerticesRetained':cap_vertices,'authoredNewHairClumps':len(paths),'eyeTransform':'Uniform scale .91 around each globe center; coordinated compact affine socket transform, upper lid skin separately relaxed','limitation':'Static A01-frame deformation, NOT a verified bind/rig edit. Source 50-key head remains unchanged; future original Basis/key/weight/bone/lattice transport requires separate Phase B validation.'}
(out/'asset-report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());(out/'head-vertex-deltas.json').write_bytes((json.dumps({'frame':'A01 evaluated static metre frame; not original Snow Basis','delta':[list(v.co-Vector(old)) for v,old in zip(head.data.vertices,head_before)]})+'\n').encode())
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in asset:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(out/(cfg['assetId']+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False)
h=cfg['heightMeters'];camera=scene.camera;cd=camera.data;rc=cfg['render'];scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=rc['samples'];scene.cycles.use_denoising=True;scene.cycles.seed=cfg['seed'];scene.render.threads_mode='FIXED';scene.render.threads=rc['threads'];scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0;scene.view_settings.gamma=1
# Existing A01 world/area lights/floor are retained byte-for-byte in their settings.
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def render_views(prefix='',clay=False,only=None):
 meta=[]
 for name,az,kind in [('front',0,'full'),('side',90,'full'),('back',180,'full'),('three_quarter',35,'full'),('face_front',0,'face'),('face_three_quarter',35,'face'),('near_third_person',35,'near'),('game_16m_front',0,'game'),('game_16m_back',180,'game')]:
  if only and name not in only:continue
  if not only and a.views!='all' and name not in a.views.split(','):continue
  ang=math.radians(az);focus=Vector((0,-.03 if kind=='face' else 0,h*(.88 if kind=='face' else .50)))
  if kind in ['full','face']:
   cd.type='ORTHO';cd.sensor_fit='AUTO';cd.ortho_scale=h*(.31 if kind=='face' else 1.23);camera.location=focus+Vector((math.sin(ang)*h*3,-math.cos(ang)*h*3,0));scene.render.resolution_x,scene.render.resolution_y=rc['faceResolution' if kind=='face' else 'fullResolution']
  else:
   cd.type='PERSP';cd.sensor_fit='VERTICAL';cd.sensor_height=32;cd.lens=32/(2*math.tan(math.radians(40)/2));dist=16 if kind=='game' else 3.2;elev=math.radians(50 if kind=='game' else 15);camera.location=focus+Vector((dist*math.cos(elev)*math.sin(ang),-dist*math.cos(elev)*math.cos(ang),dist*math.sin(elev)));scene.render.resolution_x,scene.render.resolution_y=rc['gameResolution' if kind=='game' else 'fullResolution']
  aim(camera,focus);scene.render.filepath=str(out/'renders'/(prefix+name+'.png'));bpy.ops.render.render(write_still=True);meta.append({'view':prefix+name,'cameraType':cd.type,'location':list(camera.location),'focus':list(focus),'distanceMeters':(camera.location-focus).length,'orthoScale':cd.ortho_scale if cd.type=='ORTHO' else None,'verticalFovDegrees':math.degrees(cd.angle_y) if cd.type=='PERSP' else None,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'clay':clay})
 return meta
meta=render_views();assert [metrics(o)['geometrySha256'] for o in asset]==[m['geometrySha256'] for m in items];bpy.ops.wm.save_as_mainfile(filepath=str(out/'character.blend'))
if a.clay_comparison:
 def set_clay(objects):
  m=bpy.data.materials.new('WC_MatchedClay');m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.72
  for o in objects:
   for i in range(len(o.data.materials)):o.data.materials[i]=m
 set_clay(asset);meta+=render_views('A02_clay_',True,{'face_front','face_three_quarter'})
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False);scene=bpy.context.scene;camera=scene.camera;cd=camera.data;asset=[o for o in scene.objects if o.type=='MESH' and o.get('wc_asset_id')==cfg['assetId']];set_clay(asset);meta+=render_views('A01_clay_',True,{'face_front','face_three_quarter'})
(out/'render-metadata.json').write_bytes((json.dumps({'views':meta,'renderConfig':rc,'seed':cfg['seed'],'sameCameraAndLightsAsA01':True,'imageRetouching':False,'elapsedBuildSeconds':time.time()-start},indent=2)+'\n').encode());assert hashlib.sha256(source.read_bytes()).hexdigest()==cfg['sourceA01BlendSha256'];print(json.dumps({'triangles':report['triangles'],'headDisplacement':report['headDisplacementMeters'],'jacobianMin':min(dets),'renders':len(meta),'duration':time.time()-start}))
