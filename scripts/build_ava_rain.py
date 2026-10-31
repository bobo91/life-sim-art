"""Rain-derived Ava: bounded authored form edits, static visual prototype only."""
import argparse,sys,math,hashlib,json,random,struct
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
sys.path.insert(0,str(Path(__file__).parent))
from ava_rain_tools import *
from ava_rain_outfit import build as outfit

def smooth(a,b,x):t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def bell(x,c,w):return math.exp(-((x-c)/w)**2)
def form(p,role):
    v=Vector(p);x,y,z=p;front=1-smooth(-.04,.035,y)
    # The actual Rain orbital volume and lids move together around the globe.
    if role in ('head','eyes','eyebrows','eyelashes'):
        c=Vector(((1 if x>0 else -1)*.04624,-.08863,1.47326));d=(v-c).length
        w=1 if role=='eyes' else 1-smooth(.044,.075,d)
        v=c+(v-c)*(1-.27*w)
    # Preserve source neck junction; narrower adult cranial/cheek design.
    v.x*=1-.12*smooth(1.31,1.39,z)
    if role=='head':
        v.x*=1-.045*bell(z,1.334,.026)*front
        v.x*=1-.14*bell(z,1.430,.018)*bell(x,0,.030)*front
        v.y+=.008*bell(z,1.432,.023)*bell(x,0,.026)*front
        v.y+=.012*bell(z,1.378,.020)*bell(x,0,.050)*front
        v.y+=.006*bell(z,1.326,.021)*bell(x,0,.045)*front
        mw=.36*bell(z,1.382,.023)*bell(x,0,.055)*front
        v.z=1.382+(v.z-1.382)*(1-mw)
        v.z+=.0025*bell(abs(x),.043,.012)*bell(z,1.382,.015)*front
        # Ear outline is scaled coherently with its surrounding authored loops.
        e=smooth(.090,.115,abs(x))*bell(z,1.448,.052)
        v.x-=(1 if x>0 else -1)*.007*e;v.z=1.448+(v.z-1.448)*(1-.13*e)
    elif role=='eyebrows':
        v.z=1.508+(v.z-1.508)*.62+.001*bell(abs(x),.03,.018)
    return v

def cat(path,t):
    t=max(0,min(len(path)-1-1e-7,t));i=int(t);u=t-i;p=[Vector(path[max(0,min(len(path)-1,j))]) for j in [i-1,i,i+1,i+2]]
    return .5*((2*p[1])+(-p[0]+p[2])*u+(2*p[0]-5*p[1]+4*p[2]-p[3])*u*u+(-p[0]+3*p[1]-3*p[2]+p[3])*u*u*u)
def roll_ponytail(ob):
    # Recontour the actual source ponytail cross-sections into an asymmetric bun.
    points=[v.co.copy() for v in ob.data.vertices];bins=[]
    for i in range(17):
        y=.081+(.509-.081)*i/16;near=sorted(points,key=lambda p:abs(p.y-y))[:24];bins.append(sum(near,Vector())/len(near))
    for v in ob.data.vertices:
        old=v.co.copy();t=max(0,min(1,(old.y-.081)/(.509-.081)));u=t*16;i=min(15,int(u));center=bins[i].lerp(bins[i+1],u-i)
        # Round the long native sections into a pinned, softly irregular bun.
        # This edits existing vertices only; no new hair primitive is substituted.
        dx=(old.x-center.x)/.045;dz=(old.z-center.z)/.027;angle=math.atan2(dz,dx)
        radius=max(0,math.sin(math.pi*t))**.60
        irregular=.94+.06*min(1.5,math.hypot(dx,dz))-.027*math.cos(7*angle+4*t)
        v.co=(.005*math.sin(2*math.pi*t)+.058*radius*irregular*math.cos(angle),.132+.045*radius*irregular*math.sin(angle),1.551+.124*t)
    bm=bmesh.new();bm.from_mesh(ob.data)
    for _ in range(6):bmesh.ops.smooth_vert(bm,verts=list(bm.verts),factor=.25,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    bm.to_mesh(ob.data);bm.free()
    ob.data.update();ob.name='Ava_LooseBun_FromRainPonytail'

def freckles(head,skin,out):
    me=head.data;me.calc_loop_triangles();ts=list(me.loop_triangles);bv=BVHTree.FromPolygons([v.co for v in me.vertices],[t.vertices for t in ts],all_triangles=True)
    image=next(n.image for n in skin.node_tree.nodes if n.type=='TEX_IMAGE');w,h=image.size;pixels=np.empty(w*h*4,dtype=np.float32);image.pixels.foreach_get(pixels);pixels=pixels.reshape(h,w,4);rng=random.Random(41033);marks=[]
    uv=me.uv_layers.active
    for _ in range(85):
        x=rng.uniform(-.072,.072);z=rng.uniform(1.434,1.459)
        hit,normal,idx,d=bv.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
        if hit is None:continue
        t=ts[idx];p=[me.vertices[i].co for i in t.vertices];u=[Vector((*uv.data[i].uv,0)) for i in t.loops]
        q=barycentric_transform(hit,*p,*u);xx=int(q.x*w);yy=int(q.y*h);rad=rng.uniform(.8,1.6);alpha=rng.uniform(.15,.29)
        for py in range(max(0,yy-2),min(h,yy+3)):
            for px in range(max(0,xx-2),min(w,xx+3)):
                weight=max(0,1-((px-xx)**2+(py-yy)**2)/(rad*rad))*alpha
                pixels[py,px,:3]=pixels[py,px,:3]*(1-weight)+np.array([.13,.058,.027])*weight
        marks.append([float(q.x),float(q.y),rad,alpha])
    image.pixels.foreach_set(pixels.ravel());image.filepath_raw=str(out/'ava_skin_freckles.png');image.file_format='PNG';image.save();image.pack();return marks

def metrics(objects):
    result=[]
    for o in objects:
        o.data.calc_loop_triangles();pp=[o.matrix_world@v.co for v in o.data.vertices]
        result.append({'name':o.name,'vertices':len(pp),'triangles':len(o.data.loop_triangles),'min':[min(p[k] for p in pp) for k in range(3)],'max':[max(p[k] for p in pp) for k in range(3)],'source':o.get('rainSourceObject'),'materials':[m.name for m in o.data.materials]})
    return result

def surface_normals(objects):
    # Thin garment hems, fingertips and soles can acquire opposing averaged
    # normals after reduction. Keep those few faces flat, with their true normal.
    changed={}
    for o in objects:
        me=o.data;marked=set()
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces))
        collapsed=[f for f in bm.faces if f.calc_area()<1e-14]
        if collapsed:bmesh.ops.delete(bm,geom=collapsed,context='FACES_ONLY')
        loose=[v for v in bm.verts if not v.link_faces]
        if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
        bm.to_mesh(me);bm.free()
        for _ in range(12):
            me.update();me.calc_loop_triangles();bad=[];normals=me.corner_normals
            for t in me.loop_triangles:
                a,b,c=[me.vertices[i].co for i in t.vertices]
                n=sum((normals[i].vector for i in t.loops),Vector())
                if (b-a).cross(c-a).dot(n)<=0:bad.append(t.polygon_index)
            if not bad:break
            for i in bad:me.polygons[i].use_smooth=False;marked.add(i)
        assert not bad,(o.name,bad)
        if marked:changed[o.name]=len(marked)
    return changed

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--textures',required=True);ap.add_argument('--out',required=True);ap.add_argument('--views',default='all');ap.add_argument('--a03');ap.add_argument('--samples',type=int,default=32);ap.add_argument('--optimize',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    source=Path(a.source).resolve();tex=Path(a.textures).resolve();out=Path(a.out).resolve();assert not out.exists();out.mkdir(parents=True);(out/'renders').mkdir();(out/'textures').mkdir();before=sha(source)
    bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    native={o.name.removeprefix('Rain_'):o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('Rain_')}
    for o in list(bpy.context.scene.objects):
        if o not in native.values():bpy.data.objects.remove(o,do_unlink=True)
    mats={'skin':material('Ava_Skin',(.7,.5,.36),.71,tex/'ava_skin_atlas.png'),'hair':material('Ava_Brunette',(.19,.09,.047),.79),'eyes':material('Ava_BrownEyes',(.8,.8,.8),.30,tex/'ava_eyes_brown.png'),'cream':material('Ava_CreamKnit',(.83,.79,.68),.84),'olive':material('Ava_OliveApron',(.25,.30,.18),.88),'leather':material('Ava_Leather',(.28,.16,.085),.76),'denim':material('Ava_DarkDenim',(.18,.21,.25),.86,tex/'ava_denim.png',tex/'ava_denim_normal.png'),'shoe':material('Ava_Sneakers',(.78,.76,.69),.80)}
    original=[]
    for key,o in native.items():
        o['rainSourceObject']='GEO-rain-'+key;o['assetId']='chr_npc_ava_morgan_001'
        if key=='body_nomask':
            for v in o.data.vertices:
                v.co.x+=(1 if v.co.x>0 else -1)*.08*smooth(.22,.63,abs(v.co.x))
        if key in ('head','eyes','eyebrows','eyelashes','hair_main','hair_strand','hair_ponytail','hairband'):
            old=[v.co.copy() for v in o.data.vertices]
            if key=='hair_ponytail':roll_ponytail(o)
            for v in o.data.vertices:v.co=form(v.co,key if key in ('head','eyes','eyebrows','eyelashes') else 'hair')
            if key=='hair_strand':
                for v in o.data.vertices:
                    t=1-smooth(1.46,1.57,v.co.z);v.co.z-=.018*t;v.co.x+=.008*t
            o.data.update();original.append({'name':key,'verticesPreserved':len(old)==len(o.data.vertices),'maxVertexShift':max((v.co-p).length for v,p in zip(o.data.vertices,old))})
        if key in ('head','body_nomask'):
            assign(o,mats['skin']);uv=o.data.uv_layers.active
            for p in o.data.polygons:
                center=sum((uv.data[li].uv for li in p.loop_indices),Vector((0,0)))/len(p.loop_indices);tx=math.floor(center.x+1e-7);ty=math.floor(center.y+1e-7);tile=1001+tx+10*ty;offset={1001:(0,0),1002:(.5,0),1003:(0,.5)}.get(tile,(0,0))
                for li in p.loop_indices:
                    old=uv.data[li].uv.copy();uv.data[li].uv=((old.x-tx)*.5+offset[0],(old.y-ty)*.5+offset[1])
        elif key=='eyes':assign(o,mats['eyes'])
        else:assign(o,mats['hair'] if any(s in key for s in ('hair','eyebrow','eyelash')) else mats['cream'])
    # A second restrained framing strand reuses the actual source strand surface.
    strand=native['hair_strand'];second=strand.copy();second.data=strand.data.copy();second.name='Ava_RightFramingStrand';bpy.context.scene.collection.objects.link(second)
    for v in second.data.vertices:v.co.x=-v.co.x;v.co.z+=.012;v.co.y+=.003
    bm=bmesh.new();bm.from_mesh(second.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(second.data);bm.free()
    objects=[native[k] for k in ['head','eyes','eyebrows','eyelashes','hair_main','hair_strand','hair_ponytail','hairband']]+[second]
    objects+=outfit(native['body_nomask'],native['jeans'],native['shoes'],mats)
    bpy.data.objects.remove(native['top'],do_unlink=True)
    marks=freckles(native['head'],mats['skin'],out/'textures')
    for o in objects:
        if o.data.has_custom_normals:o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
        o.data.update()
    # Authored hair surfaces were designed for subdivision; retain a smooth high copy.
    from ava_rain_outfit import apply
    for key in ['hair_main','hair_ponytail','hair_strand','eyebrows']:
        apply(native[key],'SUBSURF',levels=1,render_levels=1)
    apply(second,'SUBSURF',levels=1,render_levels=1)
    # Source-authored high copy is canonical. Optional later static reduction.
    root=bpy.data.objects.new('CHR_AvaMorgan_Rain_V01',None);bpy.context.scene.collection.objects.link(root);root['assetId']='chr_npc_ava_morgan_001';root['version']='rain-visual-v0.1';root['credit']='Rain Rig (CC) Blender Foundation | studio.blender.org';root['licence']='CC BY 4.0';root['scope']='static visual prototype only, approval pending'
    for o in objects:o.parent=root;o['assetId']='chr_npc_ava_morgan_001'
    bpy.context.view_layer.update();items=metrics(objects);lo=[min(m['min'][k] for m in items) for k in range(3)];hi=[max(m['max'][k] for m in items) for k in range(3)];sc=1.70/(hi[2]-lo[2]);offset=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))
    for o in objects:
        for v in o.data.vertices:v.co=(v.co+offset)*sc
        o.data.update()
    used_mats={m for o in objects for m in o.data.materials}
    for m in list(bpy.data.materials):
        if m not in used_mats:bpy.data.materials.remove(m)
    for ng in list(bpy.data.node_groups):
        if ng.users==0:bpy.data.node_groups.remove(ng)
    for im in list(bpy.data.images):
        if not im.users:bpy.data.images.remove(im)
    for im in bpy.data.images:
        if im.users and im.source!='TILED':
            try:im.pack()
            except Exception:pass
    cam,lights,bg=studio(out,a.samples);metadata=[]
    surface_normals(objects)
    high_metrics=metrics(objects)
    if a.optimize:
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'character_high.blend'))
        targets={'Rain_head':8700,'Rain_eyes':1600,'Rain_eyebrows':400,'Rain_eyelashes':472,'Rain_hair_main':3000,'Ava_LooseBun_FromRainPonytail':800,'Rain_hair_strand':500,'Ava_RightFramingStrand':500,'Rain_hairband':150,'Rain_body_nomask':3000,'Ava_CreamTop_RainSurface':2400,'Rain_jeans':3300,'Rain_shoes':2200,'Ava_FittedCafeApron':1300,'Ava_ApronPocket':200,'Ava_ApronTie':150}
        for o in objects:
            o.data.calc_loop_triangles();target=targets.get(o.name,150 if 'RolledSleeve' in o.name else 120);n=len(o.data.loop_triangles)
            if n>target:apply(o,'DECIMATE',ratio=target/n,use_collapse_triangulate=True)
            for p in o.data.polygons:p.use_smooth=True
    normals_adjusted=surface_normals(objects)
    views=[('front','full',0),('side','full',90),('back','full',180),('three_quarter','three',35),('face_front','face',0),('face_profile','face',90),('face_three_quarter','face',35)]
    def shot(name,kind,az):
        if a.views!='all' and name not in a.views.split(','):return
        metadata.append(render(cam,out/'renders',name,kind,az,focus=(0,offset.y*sc,1.477*sc) if kind=='face' else None))
    for v in views:shot(*v)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'character.blend'))
    report={'assetId':'chr_npc_ava_morgan_001','version':'rain-visual-v0.1','sourceStaticSha256':before,'originalRainSha256':'831ab6d837c679040285862b15dc9ee5180b018442a88aeaf92aaa7509b80258','changes':original,'scale':sc,'offset':list(offset),'freckles':len(marks),'highMeshes':high_metrics,'meshes':metrics(objects),'triangleCount':sum(m['triangles'] for m in metrics(objects)),'materialCount':len({m for o in objects for m in o.data.materials}),'sourcePreserved':sha(source)==before,'rigs':len(bpy.data.armatures),'texts':len(bpy.data.texts),'animations':len(bpy.data.actions),'flatNormalCorrections':normals_adjusted,'renderViews':metadata,'approval':'pending owner visual GO/NO-GO'}
    write(out/'report.json',report);assert sha(source)==before;print(json.dumps({k:report[k] for k in ['triangleCount','materialCount','rigs','texts','animations','freckles']}))
if __name__=='__main__':main()
