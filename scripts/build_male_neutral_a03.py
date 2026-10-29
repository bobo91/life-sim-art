"""Focused A03 refinement and opt-in static optimization; immutable A02 input."""
import argparse,hashlib,json,math,shutil,struct,sys,time
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--config',required=True);p.add_argument('--out',required=True);p.add_argument('--views',default='all');p.add_argument('--optimize',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);source=Path(a.source).resolve();cfg=json.loads(Path(a.config).read_text());out=Path(a.out).resolve();assert not out.exists(),'Fresh output required';assert hashlib.sha256(source.read_bytes()).hexdigest()==cfg['sourceA02BlendSha256'];out.mkdir(parents=True);(out/'textures').mkdir();(out/'renders').mkdir();start=time.time();bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
scene=bpy.context.scene;asset=[o for o in scene.objects if o.type=='MESH' and o.get('wc_asset_id')==cfg['assetId']];root=bpy.data.objects['CHR_PlayerMale_A01'];root['iteration']='A03';root['scope']='Static refinement and controlled optimization only; no rig/animation';r=cfg['refinement']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def metrics(o):
 me=o.data;me.calc_loop_triangles();pts=[o.matrix_world@v.co for v in me.vertices];d=hashlib.sha256()
 for v in pts:d.update(struct.pack('<3f',*v))
 for t in me.loop_triangles:d.update(struct.pack('<3I',*t.vertices))
 return {'name':o.name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'boundsWorld':{'min':[min(v[k] for v in pts) for k in range(3)],'max':[max(v[k] for v in pts) for k in range(3)]},'geometrySha256':d.hexdigest(),'materials':[m.name for m in me.materials]}
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def bell(x,c,w):return math.exp(-((x-c)/w)**2)
def eye_field(point):
 x,y,z=point;v=Vector(point)
 for sign in [-1,1]:
  center=Vector((sign*.04083548,-.0458,1.5813));rad=(Vector(point)-center).length;w=1-smooth(.034,.054,rad);v+=(center+(Vector(point)-center)*r['eyeScaleRelativeA02']-Vector(point))*w
 return v
before={o.name:metrics(o) for o in asset};head=bpy.data.objects['M01_head'];head_faces=[tuple(p.vertices) for p in head.data.polygons];head_uv=[tuple(u.uv) for u in head.data.uv_layers.active.data];head_original=[v.co.copy() for v in head.data.vertices];old_poly_normals=[p.normal.copy() for p in head.data.polygons]
for obj in asset:
 if obj.name not in ['M01_head','M01_eyes','M01_eyebrows']:continue
 for v in obj.data.vertices:
  old=v.co.copy()
  if obj.name=='M01_eyes':
   center=Vector(((1 if old.x>0 else -1)*.04083548,-.0458,1.5813));v.co=center+(old-center)*r['eyeScaleRelativeA02']
  else:v.co=eye_field(old)
  if obj.name=='M01_head':
   for sign in [-1,1]:v.co.z+=r['lowerLidRaiseMeters']*bell(old.x,sign*.04083548,.027)*bell(old.z,1.570,.009)*bell(old.y,-.069,.020)*(1-smooth(1.578,1.585,old.z))
   v.co.y+=r['chinProjectionBackMeters']*bell(old.x,0,.034)*bell(old.z,1.435,.018)*(1-smooth(-.04,.02,old.y))
  elif obj.name=='M01_eyebrows':v.co.z-=.0003*bell(abs(old.x),.048,.025)
 obj.data.update()
def local_smooth(obj,iterations,factor,max_shift,mask):
 mesh=obj.data;start=[v.co.copy() for v in mesh.vertices];adj=[set() for v in start]
 for e in mesh.edges:i,j=e.vertices;adj[i].add(j);adj[j].add(i)
 for _ in range(iterations):
  old=[v.co.copy() for v in mesh.vertices]
  for i,v in enumerate(mesh.vertices):
   if not adj[i]:continue
   w=mask(start[i]);avg=sum((old[j] for j in sorted(adj[i])),Vector())/len(adj[i]);new=old[i]+(avg-old[i])*factor*w;delta=new-start[i]
   if delta.length>max_shift:new=start[i]+delta.normalized()*max_shift
   v.co=new
 mesh.update()
local_smooth(head,r['jawSmoothIterations'],r['jawSmoothFactor'],r['jawMaximumShiftMeters'],lambda p:smooth(1.400,1.423,p.z)*(1-smooth(1.465,1.482,p.z))*(1-smooth(.02,.07,p.y)))
local_smooth(bpy.data.objects['M01_eyebrows'],1,r['browSmoothFactor'],r['browMaximumShiftMeters'],lambda p:1)
# Existing side-swept hairstyle, subtle asymmetric cross-sections and rounded front caps.
hair=bpy.data.objects['M01_hair_base'];adj=[set() for v in hair.data.vertices]
for e in hair.data.edges:i,j=e.vertices;adj[i].add(j);adj[j].add(i)
left=set(range(len(adj)));groups=[]
while left:
 i=min(left);left.remove(i);q=[i];seen={i}
 for i in q:
  for j in adj[i]:
   if j not in seen:seen.add(j);left.discard(j);q.append(j)
 groups.append(sorted(seen))
assert [len(g) for g in groups]==[547,230,230,230],'Source hair component topology changed';front_info=[]
for k,ids in enumerate(groups[1:]):
 caps=[i for i in ids if len(adj[i])==12];assert len(caps)==2;front=min(caps,key=lambda i:hair.data.vertices[i].co.y);ring_set=adj[front];first=min(ring_set);ring=[first];previous=None
 while len(ring)<12:
  choices=sorted(adj[ring[-1]] & ring_set - set(ring))
  assert choices;ring.append(choices[0])
 rings=[ring];prev={front}
 for _ in range(18):
  current=set(rings[-1]);row=[]
  for i in rings[-1]:
   options=adj[i]-current-prev;assert len(options)==1;row.append(next(iter(options)))
  assert len(set(row))==12;rings.append(row);prev=current
 centers=[sum((hair.data.vertices[i].co for i in row),Vector())/12 for row in rings];phase=[.3,1.7,2.8][k]
 for n,row in enumerate(rings):
  t=n/18;center=centers[n];tan=(centers[min(18,n+1)]-centers[max(0,n-1)]).normalized();side=Vector((tan.y,-tan.x,0)).normalized();up=side.cross(tan).normalized()
  if up.z<0:up=-up
  width=1+r['hairWidthVariation']*math.sin(math.pi*t)*math.sin(2*math.pi*t+phase)-.08*math.exp(-(t/.10)**2);depth=r['hairDepthScale']+.03*math.sin(math.pi*t)*math.cos(2*math.pi*t+phase);shift=Vector((.001*math.sin(math.pi*t)*math.sin(phase),0,r['hairCrestVariationMeters']*math.sin(math.pi*t)*math.sin(2*math.pi*t+phase)))
  for i in row:
   v=hair.data.vertices[i];delta=v.co-center;v.co=center+side*delta.dot(side)*width+up*delta.dot(up)*depth+tan*delta.dot(tan)+shift
 front_info.append((rings[0],front,(centers[1]-centers[0]).normalized()))
bm=bmesh.new();bm.from_mesh(hair.data);bm.verts.ensure_lookup_table();jobs=[([bm.verts[i] for i in ring],bm.verts[cap],tan) for ring,cap,tan in front_info]
for ring,cap,tan in jobs:
 assert len(cap.link_faces)==12
 center=sum((v.co for v in ring),Vector())/12;bmesh.ops.delete(bm,geom=[cap],context='VERTS');last=ring
 for scale,distance in [(.76,.0014),(.40,.0028)]:
  row=[bm.verts.new(center+(v.co-center)*scale-tan*distance) for v in ring]
  for j in range(12):bm.faces.new((last[j],last[(j+1)%12],row[(j+1)%12],row[j]))
  last=row
 tip=bm.verts.new(center-tan*r['hairFrontRoundMeters'])
 for j in range(12):bm.faces.new((last[j],last[(j+1)%12],tip))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(hair.data);bm.free()
for poly in hair.data.polygons:poly.use_smooth=True;poly.material_index=0
for obj in asset:
 if obj.data.has_custom_normals:obj.data.normals_split_custom_set([(0,0,0)]*len(obj.data.loops))
 obj.data.update()
assert head_faces==[tuple(p.vertices) for p in head.data.polygons] and head_uv==[tuple(u.uv) for u in head.data.uv_layers.active.data]
assert all(old.dot(p.normal)>=0 for old,p in zip(old_poly_normals,head.data.polygons)),'Head polygon orientation inverted'
# Same skin palette and source PNG bytes; only hair roughness moves slightly.
materials={m.name:m for o in asset for m in o.data.materials};loaded={};texture_hashes={}
for mat in materials.values():
 if mat.name=='M01_hair':next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Roughness'].default_value=cfg['hair']['roughness']
 for node in mat.node_tree.nodes:
  if node.type!='TEX_IMAGE' or not node.image:continue
  name=Path(node.image.filepath).name
  if name not in loaded:
   old=source.parent/'textures'/name;dest=out/'textures'/name;shutil.copy2(old,dest);assert digest(old)==digest(dest);texture_hashes[name]=digest(dest);im=bpy.data.images.load(str(dest),check_existing=False);im.colorspace_settings.name=node.image.colorspace_settings.name;im.pack();loaded[name]=im
  node.image=loaded[name]
for im in list(bpy.data.images):
 if not im.users:bpy.data.images.remove(im)
high_items=[metrics(o) for o in asset];unchanged_high=['M01_body','M01_shirt','M01_pants','M01_shoes_base','M01_shoes_bottom','M01_shoes_parts']
for name in unchanged_high:assert before[name]['geometrySha256']==next(m['geometrySha256'] for m in high_items if m['name']==name)
h=cfg['heightMeters'];camera=scene.camera;cd=camera.data;rc=cfg['render'];scene.cycles.samples=rc['samples'];scene.cycles.seed=cfg['seed'];scene.render.threads_mode='FIXED';scene.render.threads=rc['threads'];scene.render.resolution_percentage=100;meta=[]
views=[('front',0,'full'),('side',90,'full'),('back',180,'full'),('three_quarter',35,'full'),('face_front',0,'face'),('face_three_quarter',35,'face'),('near_third_person',35,'near'),('game_16m_front',0,'game'),('game_16m_back',180,'game'),('shoe_close',35,'shoe'),('hand_close',35,'hand')]
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def setup(name,az,kind):
 ang=math.radians(az);focus=Vector((0,-.03 if kind=='face' else 0,h*(.88 if kind=='face' else .50)))
 if kind in ['full','face','shoe','hand']:
  cd.type='ORTHO';cd.sensor_fit='AUTO';cd.ortho_scale=h*(.31 if kind=='face' else 1.23);camera.location=focus+Vector((math.sin(ang)*h*3,-math.cos(ang)*h*3,0));scene.render.resolution_x,scene.render.resolution_y=rc['faceResolution' if kind=='face' else 'fullResolution']
  if kind=='shoe':focus=Vector((0,-.01,.055));cd.ortho_scale=.36;camera.location=focus+Vector((.9,-1.3,.55));scene.render.resolution_x=scene.render.resolution_y=900
  if kind=='hand':focus=Vector((.765,.015,1.30));cd.ortho_scale=.30;camera.location=focus+Vector((.25,-.7,.60));scene.render.resolution_x=scene.render.resolution_y=900
 else:
  cd.type='PERSP';cd.sensor_fit='VERTICAL';cd.sensor_height=32;cd.lens=32/(2*math.tan(math.radians(40)/2));dist=16 if kind=='game' else 3.2;elev=math.radians(50 if kind=='game' else 15);camera.location=focus+Vector((dist*math.cos(elev)*math.sin(ang),-dist*math.cos(elev)*math.cos(ang),dist*math.sin(elev)));scene.render.resolution_x,scene.render.resolution_y=rc['gameResolution' if kind=='game' else 'fullResolution']
 aim(camera,focus);return {'cameraType':cd.type,'location':list(camera.location),'focus':list(focus),'distanceMeters':(camera.location-focus).length,'orthoScale':cd.ortho_scale if cd.type=='ORTHO' else None,'verticalFovDegrees':math.degrees(cd.angle_y) if cd.type=='PERSP' else None,'resolution':[scene.render.resolution_x,scene.render.resolution_y]}
def render(prefix='',only=None):
 expected=[metrics(o)['geometrySha256'] for o in asset]
 for name,az,kind in views:
  if only is not None and name not in only:continue
  if only is None and a.views!='all' and name not in a.views.split(','):continue
  v=setup(name,az,kind);scene.render.filepath=str(out/'renders'/(prefix+name+'.png'));bpy.ops.render.render(write_still=True);assert expected==[metrics(o)['geometrySha256'] for o in asset];meta.append({'view':prefix+name,**v})
if a.optimize:
 render('high_',{'three_quarter','side','near_third_person','game_16m_front','shoe_close','hand_close'} if a.views=='all' else set(a.views.split(',')) & {'three_quarter','side','near_third_person','game_16m_front','shoe_close','hand_close'});setup('three_quarter',35,'full');bpy.ops.wm.save_as_mainfile(filepath=str(out/'character_high.blend'))
 from optimize_male_a03 import optimize
 opt=optimize(asset,cfg['optimization']['meshes'])
 for mesh in list(bpy.data.meshes):
  if mesh.users==0:bpy.data.meshes.remove(mesh)
else:opt=None
items=[metrics(o) for o in asset]
for name in cfg['optimization']['preserveObjects']:assert next(m['geometrySha256'] for m in items if m['name']==name)==next(m['geometrySha256'] for m in high_items if m['name']==name)
lo=[min(m['boundsWorld']['min'][k] for m in items) for k in range(3)];hi=[max(m['boundsWorld']['max'][k] for m in items) for k in range(3)];dis=[(v.co-old).length for v,old in zip(head.data.vertices,head_original)]
report={'assetId':cfg['assetId'],'iteration':'A03','phase':'A','blender':bpy.app.version_string,'sourceBlendSha256':cfg['sourceBlendSha256'],'sourceA02BlendSha256':cfg['sourceA02BlendSha256'],'meshes':items,'dimensionsMeters':[hi[k]-lo[k] for k in range(3)],'boundsWorld':{'min':lo,'max':hi},'triangles':sum(m['triangles'] for m in items),'triangleTargetRange':[cfg['optimization']['targetMinTriangles'],cfg['optimization']['targetMaxTriangles']],'triangleTargetMet':cfg['optimization']['targetMinTriangles']<=sum(m['triangles'] for m in items)<=cfg['optimization']['targetMaxTriangles'],'budgetTradeoff':cfg['optimization']['qualityPriority'],'highTriangles':sum(m['triangles'] for m in high_items),'a02Triangles':sum(m['triangles'] for m in before.values()),'materialCount':len(materials),'meshCount':len(asset),'rigsDelivered':0,'animationsDelivered':0,'embeddedTextScripts':len(bpy.data.texts),'headTopologyAndUvPreserved':True,'headDisplacementMeters':{'max':max(dis),'mean':sum(dis)/len(dis)},'bodyClothesShoesUnchangedBeforeOptimization':unchanged_high,'optimization':opt,'faceHairMeshesUnchangedByOptimization':cfg['optimization']['preserveObjects'],'textureBytesUnchangedFromA02':texture_hashes,'limitation':'Static visual/optimization review only. Snow rig, weights and50-key transport remain unproven; body LOD topology needs later weight transfer. No Phase B.'}
(out/'asset-report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in asset:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(out/(cfg['assetId']+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False)
render();setup('three_quarter',35,'full');bpy.ops.wm.save_as_mainfile(filepath=str(out/'character.blend'));(out/'render-metadata.json').write_bytes((json.dumps({'views':meta,'renderConfig':rc,'sameWorldAndLightsAsA02':True,'imageRetouching':False,'seed':cfg['seed'],'elapsedBuildSeconds':time.time()-start},indent=2)+'\n').encode());assert digest(source)==cfg['sourceA02BlendSha256'];print(json.dumps({'triangles':report['triangles'],'highTriangles':report['highTriangles'],'headDisplacement':report['headDisplacementMeters'],'optimized':a.optimize,'renderCount':len(meta),'seconds':time.time()-start}))
