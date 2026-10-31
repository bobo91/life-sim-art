"""Artist-controlled volume transfer on native Rain topology, independent of Ava v0.2.

Static head/hair review only. Native neck/body coordinates are retained; no rig,
action, embedded script or image-to-mesh generation is produced.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).parent))
from ava_rain_tools import material, assign, studio, render, aim, sha, write
from ava_b_hair import build as build_hair
from ava_b_brows import build as build_brows

ROOT = Path(__file__).resolve().parents[1]


def smooth(a, b, x):
    t = max(0, min(1, (x-a)/(b-a)))
    return t*t*(3-2*t)


def bell(x, c, w):
    return math.exp(-((x-c)/w)**2)


def curve(stations, x):
    """Monotone Hermite cage station interpolation, without crease-like linear joins."""
    xs, ys = zip(*stations)
    if x <= xs[0]: return ys[0] + (x-xs[0])*(ys[1]-ys[0])/(xs[1]-xs[0])
    if x >= xs[-1]: return ys[-1] + (x-xs[-1])*(ys[-1]-ys[-2])/(xs[-1]-xs[-2])
    ds = [(ys[i+1]-ys[i])/(xs[i+1]-xs[i]) for i in range(len(xs)-1)]
    slopes = [ds[0]] + [2*ds[i-1]*ds[i]/(ds[i-1]+ds[i]) if ds[i-1]*ds[i]>0 else 0 for i in range(1,len(xs)-1)] + [ds[-1]]
    i = next(i for i in range(len(xs)-1) if xs[i] <= x <= xs[i+1])
    h=xs[i+1]-xs[i];t=(x-xs[i])/h
    return (2*t**3-3*t*t+1)*ys[i]+(t**3-2*t*t+t)*h*slopes[i]+(-2*t**3+3*t*t)*ys[i+1]+(t**3-t*t)*h*slopes[i+1]


def orbital(p, role, upper=0, lower=0, scale=.77):
    c=Vector(((1 if p.x>=0 else -1)*.04624,-.08863,1.47326))
    d=p-c
    w=1 if role=='eyes' else 1-smooth(.050,.081,d.length)
    d*=1-(1-scale)*w
    # Neutral B has a quiet upward outer canthus, rather than Rain's drooping
    # round aperture. Rotate the socket/lid/globe volume together in front view.
    roll=-(1 if p.x>=0 else -1)*.085*w
    co,si=math.cos(roll),math.sin(roll)
    d.x,d.z=d.x*co+d.z*si,-d.x*si+d.z*co
    if role in ('head','eyelashes'):
        if role=='eyelashes':upper=1
        angle=.130*min(1,upper)-.045*min(1,lower)
        co,si=math.cos(angle),math.sin(angle)
        d.y,d.z=d.y*co-d.z*si,d.y*si+d.z*co
    return c+d


def sculpt(p, role, config, groups=None):
    groups=groups or {};original=p.copy();x,y,z=p
    # Locked neck/shoulder junction and posterior upper neck.
    if z<=1.32:return p.copy()
    neck_influence=1-(1-smooth(1.34,1.405,z))*smooth(-.105,-.045,y)
    weight=lambda term:sum(w for name,w in groups.items() if term in name)
    p=orbital(p,role,weight('DEF-Eyelid_Top_'),weight('DEF-Eyelid_Bot_'),config['orbitalScale'])
    x,y,z=p
    blend=smooth(1.32,1.36,z)
    p.z=z+(curve(config['verticalCageStations'],z)-z)*blend
    p.x*=curve(config['widthStations'],z)
    front=1-smooth(-.095,-.035,y)
    if role=='head':
        # Native orbital/cheek loops remain continuous; authored regional form edits.
        malar=bell(abs(x),.077,.024)*bell(z,1.449,.027)*front
        p.x+=(1 if x>=0 else -1)*.0025*malar
        p.y-=.0025*malar
        p.y+=.0025*bell(abs(x),.063,.028)*bell(z,1.393,.027)*front
        p.x*=1+.040*bell(z,1.362,.020)*front
        p.y-=.0070*bell(z,1.349,.017)*bell(x,0,.038)*front
        # Straight bridge is a real depth change; nostril/tip volumes remain authored.
        p.y-=.0105*bell(z,1.464,.028)*bell(x,0,.018)*front
        p.x*=1-.22*bell(z,1.431,.025)*bell(x,0,.044)*front
        # Artist-set dorsum rail resolves the original child's concave bridge.
        rail=curve([[1.427,-.166],[1.435,-.179],[1.446,-.180],[1.465,-.170],[1.490,-.157],[1.515,-.145]],p.z)
        rail_weight=.88*bell(x,0,.016)*front*smooth(1.430,1.447,p.z)*(1-smooth(1.502,1.523,p.z))
        p.y=p.y*(1-rail_weight)+rail*rail_weight
        p.y+=.0060*bell(z,1.388,.022)*bell(x,0,.041)*front
        lip=min(1,weight('DEF-Lip_'))
        p.z=1.398+(p.z-1.398)*(1-.35*lip)
        upper_lip=min(1,weight('DEF-Lip_Top_'))
        p.z=1.398+(p.z-1.398)*(1-.30*upper_lip)
        p.x*=1+.24*lip
        p.y+=.0030*lip
        # Ear sculpt follows attachment loops, retaining the helix authored by Rain.
        ear=min(1,weight('DEF-Ear_'))
        if ear:
            ex=(1 if x>=0 else -1)*(.094+(abs(p.x)-.094)*.62)
            p.x=p.x*(1-ear)+ex*ear
            p.z-=.014*ear
    return original.lerp(p,neck_influence)


def freckles(head, skin, out, seed):
    me=head.data;me.calc_loop_triangles();tri=list(me.loop_triangles)
    tree=BVHTree.FromPolygons([v.co for v in me.vertices],[t.vertices for t in tri],all_triangles=True)
    image=next(n.image for n in skin.node_tree.nodes if n.type=='TEX_IMAGE')
    w,h=image.size;pix=np.empty(w*h*4,dtype=np.float32);image.pixels.foreach_get(pix);pix=pix.reshape(h,w,4)
    rng=random.Random(seed);uv=me.uv_layers.active;marks=0
    for _ in range(65):
        x=rng.uniform(-.072,.072);z=rng.uniform(1.454,1.482)
        hit,n,idx,dist=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
        if hit is None:continue
        t=tri[idx];q=barycentric_transform(hit,*[me.vertices[i].co for i in t.vertices],*[Vector((*uv.data[i].uv,0)) for i in t.loops])
        xx=int(q.x*w);yy=int(q.y*h);r=rng.uniform(.65,1.25);alpha=rng.uniform(.12,.23)
        for py in range(max(0,yy-2),min(h,yy+3)):
            for px in range(max(0,xx-2),min(w,xx+3)):
                a=max(0,1-((px-xx)**2+(py-yy)**2)/(r*r))*alpha
                pix[py,px,:3]=pix[py,px,:3]*(1-a)+np.array([.19,.095,.050])*a
        marks+=1
    image.pixels.foreach_set(pix.ravel());image.filepath_raw=str(out/'skin_freckles.png');image.file_format='PNG';image.save();image.pack()
    return marks


def metrics(objects):
    data=[]
    for o in objects:
        o.data.calc_loop_triangles()
        data.append({'name':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'materials':[m.name for m in o.data.materials]})
    return data


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--original',required=True);p.add_argument('--out',required=True);p.add_argument('--a03',required=True);p.add_argument('--textures');p.add_argument('--samples',type=int,default=24);p.add_argument('--views',default='all');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    cfg=json.loads((ROOT/'configs/ava_b_head_v01.json').read_text(encoding='utf8'))
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);(out/'renders').mkdir();(out/'textures').mkdir()
    original=Path(a.original).resolve();source=Path(a.source).resolve();ref=Path(a.a03).resolve()
    assert sha(original)==cfg['sourceSha256'];assert sha(ref)==cfg['a03Sha256']
    for name,key in [('ava-b-neutral-views.png','neutral'),('ava-b-model-sheet.png','sheet')]:
        assert sha(ROOT/'evidence/ava-b-design-sheet-v01'/name)==cfg['design'][key]
    source_sha=sha(source)
    # Read authored selections/lip deltas from original; source code never executes.
    bpy.context.preferences.use_preferences_save=False
    bpy.ops.wm.open_mainfile(filepath=str(original),load_ui=False,use_scripts=False)
    h=bpy.data.objects['GEO-rain-head'];gn={g.index:g.name for g in h.vertex_groups};keys=h.data.shape_keys.key_blocks
    edits=[]
    for v in h.data.vertices:
        delta=Vector((0,0,0))
        for key,value in cfg['nativeNeutralLipEdits'].items():delta+=(keys[key].data[v.index].co-keys[key].relative_key.data[v.index].co)*value
        edits.append((delta,{gn[g.group]:g.weight for g in v.groups}))
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    native={o.name.removeprefix('Rain_'):o for o in scene.objects if o.type=='MESH' and o.name.startswith('Rain_')}
    for o in list(scene.objects):
        if o not in native.values():bpy.data.objects.remove(o,do_unlink=True)
    head=native['head'];assert len(edits)==len(head.data.vertices)
    body_before=[v.co.copy() for v in native['body_nomask'].data.vertices]
    head_before=[v.co.copy() for v in head.data.vertices]
    for v,(delta,groups) in zip(head.data.vertices,edits):
        if v.co.z>1.32:v.co=sculpt(v.co+delta,'head',cfg,groups)
    # A bounded sculpt-smooth pass eases the nasolabial troughs without touching
    # lip rims, nasal detail, cheekbone silhouette or the locked neck.
    neighbors=[set() for _ in head.data.vertices]
    for edge in head.data.edges:
        i,j=edge.vertices;neighbors[i].add(j);neighbors[j].add(i)
    for _ in range(5):
        points=[v.co.copy() for v in head.data.vertices]
        for v,(_,groups) in zip(head.data.vertices,edits):
            x,y,z=points[v.index]
            protected=sum(w for n,w in groups.items() if 'DEF-Lip_' in n or 'DEF-Nose' in n)
            w=bell(abs(x),.044,.021)*bell(z,1.423,.037)*(1-smooth(-.12,-.075,y))*(1-smooth(.02,.18,protected))
            if w>.01 and neighbors[v.index]:
                mean=sum((points[i] for i in neighbors[v.index]),Vector())/len(neighbors[v.index])
                v.co=points[v.index].lerp(mean,.30*w)
    for key in ['eyes','eyelashes']:
        for v in native[key].data.vertices:v.co=sculpt(v.co,key,cfg)
    head.name='AvaB_Head_FromNativeRain';head.data.update()
    # Core PBR and source-derived UV atlas; no materials from the rejected derivative.
    tex=Path(a.textures).resolve() if a.textures else ROOT/'build/ava-rain-v01/textures'
    skin=material('AvaB_Skin',(.7,.51,.38),.74,tex/'ava_skin_atlas.png')
    hair=material('AvaB_ChestnutHair',(.255,.141,.089),.78)
    hair_shader=next(n for n in hair.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    hair_shader.inputs['Specular IOR Level'].default_value=.22
    eyes=material('AvaB_BrownEyes',(.8,.8,.8),.31,tex/'ava_eyes_brown.png')
    img=next(n.image for n in eyes.node_tree.nodes if n.type=='TEX_IMAGE');img.scale(512,512);img.pack()
    cream=material('Context_Unfinished_RainTop',(.76,.73,.66),.85)
    denim=material('Context_Unfinished_RainJeans',(.20,.23,.27),.85)
    shoe=material('Context_Unfinished_RainShoes',(.70,.69,.65),.85)
    for key in ['head','body_nomask']:
        o=native[key];assign(o,skin);uv=o.data.uv_layers.active
        for poly in o.data.polygons:
            center=sum((uv.data[i].uv for i in poly.loop_indices),Vector((0,0)))/len(poly.loop_indices);tx=math.floor(center.x+1e-7);ty=math.floor(center.y+1e-7);tile=1001+tx+10*ty;off={1001:(0,0),1002:(.5,0),1003:(0,.5)}.get(tile,(0,0))
            for i in poly.loop_indices:
                q=uv.data[i].uv.copy();uv.data[i].uv=((q.x-tx)*.5+off[0],(q.y-ty)*.5+off[1])
    assign(native['eyes'],eyes);assign(native['eyelashes'],hair)
    for key,mat in [('top',cream),('jeans',denim),('shoes',shoe)]:assign(native[key],mat)
    for key in ['eyebrows','hair_ponytail','hair_strand','hairband','hair_main']:bpy.data.objects.remove(native[key],do_unlink=True)
    for o in [head,native['eyes'],native['eyelashes']]:
        for poly in o.data.polygons:poly.use_smooth=True
        if o.data.has_custom_normals:o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
        o.data.update()
    sub=head.modifiers.new('Rain_Surface_Preview_Subdivision','SUBSURF');sub.levels=1;sub.render_levels=1
    bpy.context.view_layer.update()
    brow_objects,brow_meta=build_brows(head,hair,scene.collection)
    hair_objects,hair_meta=build_hair(head,hair,scene.collection)
    head_objects=[head,native['eyes'],native['eyelashes']]+brow_objects+hair_objects
    context=[native[k] for k in ['body_nomask','top','jeans','shoes']]
    marks=freckles(head,skin,out/'textures',cfg['seed'])
    # Preserve the full authored edit cage. A single preview subdivision shows
    # Rain's intended continuous surface; no early face decimation is applied.
    # Keep the open neck seam on its original boundary under preview subdivision.
    edge_use={tuple(sorted(e.vertices)):0 for e in head.data.edges}
    for poly in head.data.polygons:
        vs=list(poly.vertices)
        for i in range(len(vs)):edge_use[tuple(sorted((vs[i],vs[(i+1)%len(vs)])))]+=1
    crease=head.data.attributes.get('crease_edge') or head.data.attributes.new('crease_edge','FLOAT','EDGE')
    for e in head.data.edges:
        if edge_use[tuple(sorted(e.vertices))]==1 and max(head.data.vertices[i].co.z for i in e.vertices)<1.33:crease.data[e.index].value=1
    # Match split normals at the original coincident skin seam. Coordinates
    # remain unchanged; this is normal welding, not a hidden neck reshaping.
    body=native['body_nomask'];tree=KDTree(len(body.data.vertices))
    for v in body.data.vertices:tree.insert(v.co,v.index)
    tree.balance();head_normals=[];normal_matches=0
    for loop in head.data.loops:
        v=head.data.vertices[loop.vertex_index];pos,index,d=tree.find(v.co)
        if v.co.z<1.33 and d<.0001:head_normals.append(body.data.vertices[index].normal.copy());normal_matches+=1
        else:head_normals.append((0,0,0))
    head.data.normals_split_custom_set(head_normals)
    if hasattr(sub,'use_custom_normals'):sub.use_custom_normals=True
    # Rain's separate source skin shells differ by about 13 micrometres at
    # their matching seam. Weld disposable preview copies so that a Cycles
    # self-shadow crack does not obscure the unchanged neck anatomy. Both
    # canonical edit cages remain available and are the counted source meshes.
    copies=[]
    for skin_object in [head,body]:
        c=skin_object.copy();c.data=skin_object.data.copy();scene.collection.objects.link(c)
        for mod in list(c.modifiers):c.modifiers.remove(mod)
        c.parent=None;copies.append(c)
    bpy.ops.object.select_all(action='DESELECT')
    for c in copies:c.select_set(True)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();skin_preview=copies[0]
    skin_preview.name='AvaB_ContinuousSkin_Preview'
    bm=bmesh.new();bm.from_mesh(skin_preview.data)
    seam=[v for v in bm.verts if v.co.z<1.33 and v.co.z>1.27]
    bmesh.ops.remove_doubles(bm,verts=seam,dist=.000020)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(skin_preview.data);bm.free()
    # Clear seam creases on the joined skin so the new internal edge is smooth.
    crease_preview=skin_preview.data.attributes.get('crease_edge')
    if crease_preview:
        for value in crease_preview.data:value.value=0
    skin_preview.data.normals_split_custom_set([(0,0,0)]*len(skin_preview.data.loops))
    preview_sub=skin_preview.modifiers.new('Continuous_Rain_Skin_Surface','SUBSURF');preview_sub.levels=1;preview_sub.render_levels=1
    for poly in skin_preview.data.polygons:poly.use_smooth=True
    head.hide_render=True;body.hide_render=True
    skin_preview['method']='Head/body skin copies, original neck seam welded at 20 micrometre tolerance; no anatomical reshaping'
    root=bpy.data.objects.new('AVA_B_HEAD_REVIEW_V01',None);scene.collection.objects.link(root)
    root['credit']='Rain Rig (CC) Blender Foundation | studio.blender.org';root['licence']='CC BY 4.0';root['source']='https://studio.blender.org/characters/rain/v3/';root['designCommit']=cfg['design']['commit'];root['scope']='head/hair visual prototype only; no rigging/integration approval'
    for o in head_objects+context+[skin_preview]:
        o.parent=root
        for g in list(o.vertex_groups):o.vertex_groups.remove(g)
    for arm in list(bpy.data.armatures):bpy.data.armatures.remove(arm)
    for act in list(bpy.data.actions):bpy.data.actions.remove(act)
    for txt in list(bpy.data.texts):bpy.data.texts.remove(txt)
    cam,lights,bg=studio(out,a.samples)
    camera=cfg['faceCamera'];views=[]
    for name,az in [('face_front',0),('face_profile',90),('face_three_quarter',35)]:
        if a.views=='all' or name in a.views.split(','):views.append(render(cam,out/'renders',name,'face',az,focus=camera['focus'],scale=camera['orthoScale']))
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'ava_b_head_authoring.blend'))
    report={'assetId':cfg['assetId'],'designLock':cfg['design'],'originalRainSha256':sha(original),'staticSourceSha256':source_sha,'a03Sha256':sha(ref),'headHairMeshes':metrics(head_objects),'contextMeshes':metrics(context),'headHairTriangles':sum(x['triangles'] for x in metrics(head_objects)),'contextTriangles':sum(x['triangles'] for x in metrics(context)),'bodyCoordinatesPreserved':all((v.co-b).length==0 for v,b in zip(native['body_nomask'].data.vertices,body_before)),'neckJunctionPreserved':all((v.co-b).length==0 for v,b in zip(head.data.vertices,head_before) if b.z<=1.32),'maxHeadVertexChangeMetres':max((v.co-b).length for v,b in zip(head.data.vertices,head_before)),'headVertexCountPreserved':len(head.data.vertices)==len(head_before),'staticOnly':not bpy.data.armatures and not bpy.data.actions and not bpy.data.texts,'hair':hair_meta,'brows':brow_meta,'freckles':marks,'budgetPlan':cfg['finalBudgetPlan'],'blender':bpy.app.version_string,'renderEngine':scene.render.engine,'renderDevice':scene.cycles.device,'renders':views,'approval':'pending separate visual GO/NO-GO'}
    dg=bpy.context.evaluated_depsgraph_get();evaluated_head=head.evaluated_get(dg).to_mesh();evaluated_head.calc_loop_triangles();report['evaluatedHeadTriangles']=len(evaluated_head.loop_triangles);head.evaluated_get(dg).to_mesh_clear()
    write(out/'report.json',report)
    assert report['bodyCoordinatesPreserved'] and report['neckJunctionPreserved'] and report['staticOnly'], {k:report[k] for k in ['bodyCoordinatesPreserved','neckJunctionPreserved','staticOnly']}
    assert sha(original)==cfg['sourceSha256'] and sha(source)==source_sha and sha(ref)==cfg['a03Sha256']
    write(out/'report.json',report)
    print(json.dumps({k:report[k] for k in ['headHairTriangles','contextTriangles','bodyCoordinatesPreserved','neckJunctionPreserved','maxHeadVertexChangeMetres']}))


if __name__=='__main__':main()
