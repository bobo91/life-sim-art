"""Artist-directed surface pass over the existing Rain-derived Ava garments.

Call refine(mesh_objects, {'scale': ..., 'offset': [...]}) on a disposable high
copy of rain-visual-v0.1. Body/head geometry is never changed. Source garment
topology and materials are retained; cloth UVs support the small woven normals,
self-generated and use ordinary glTF-compatible image/Normal Map nodes.
"""
import math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)


def _bell(x,c,w):return math.exp(-((x-c)/w)**2)


def _cloth_delta(p):
    """Millimetre-scale cloth ease/gathers in the original authored frame."""
    x,y,z=p;u=abs(x);sign=1 if x>=0 else -1
    if u>.155:
        # Source upper-arm axis; use the same displacement for both cloth layers.
        cz=1.232-.015*_smooth(.18,.405,u)
        radial=Vector((0,y+.019,z-cz))
        if radial.length<1e-8:radial=Vector((0,0,1))
        radial.normalize();theta=math.atan2(z-cz,y+.019)
        sleeve=_smooth(.15,.19,u)*(1-_smooth(.398,.412,u))
        # Two quiet gathers immediately before the rolled edge, not full hoops.
        angular=.24+.76*abs(math.cos(theta))**2
        crease=(.0036*_bell(u,.373+(sign<0)*.006,.011)
                -.0014*_bell(u,.384+(sign<0)*.004,.008)
                +.0020*_bell(u,.393,.006))*angular
        # Tension folds run diagonally away from the real underarm/shoulder.
        line=.209+.43*(z-1.205)+.10*(y+.025)
        shoulder=.0019*_bell(u,line,.014)*_bell(z,1.24,.065)
        drape=.0024*_bell(u,.215,.058)*_bell(z,1.184,.025)
        d=radial*((crease+shoulder+drape)*sleeve)
        d.z-=.0017*_bell(u,.225,.065)*_bell(z,1.175,.025)
        return d
    # Restrained compression at the waist, outside the apron bib. No body edit.
    side=_smooth(.055,.115,u);front=_smooth(.015,.065,abs(y))
    line=1.026+.13*u
    folds=(.0022*_bell(z,line,.012)-.0009*_bell(z,line+.020,.012)
           +.0014*_bell(z,.951-.10*u,.014))*side*front
    normal=Vector((x*.35,y,0))
    if normal.length:normal.normalize()
    return normal*folds


def _weave_normal(name,knit=False):
    old=bpy.data.images.get(name)
    if old:return old
    size=256;image=bpy.data.images.new(name,width=size,height=size,alpha=False)
    image.colorspace_settings.name='Non-Color'
    def height(i,j):
        u=(i%size)/size*64;v=(j%size)/size*64
        if knit:
            # Offset loop rows give a small, soft knit grain rather than noise.
            return .40*math.cos(2*math.pi*u+.65*math.sin(2*math.pi*v))+.24*math.cos(2*math.pi*v)
        # Interlaced twill-like canvas warp/weft; no downloaded texture.
        return (.45*math.cos(2*math.pi*u)*(1+.32*math.sin(2*math.pi*v))
                +.33*math.cos(2*math.pi*v+.22*math.sin(2*math.pi*u)))
    pixels=[]
    for j in range(size):
        for i in range(size):
            dx=(height(i+1,j)-height(i-1,j))*.30
            dy=(height(i,j+1)-height(i,j-1))*.30
            n=Vector((-dx,-dy,1)).normalized();pixels.extend((n.x*.5+.5,n.y*.5+.5,n.z*.5+.5,1))
    image.pixels.foreach_set(pixels);image.file_format='PNG';image.pack()
    image['source']='Self-generated 256px periodic woven tangent normal; life-sim-art'
    return image


def _material_grain(material,image,strength,roughness):
    material.use_nodes=True;tree=material.node_tree
    shader=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Roughness'].default_value=roughness
    tex=tree.nodes.new('ShaderNodeTexImage');tex.name='Ava_WovenNormal';tex.label='Self-generated cloth grain, 256px';tex.image=image;tex.interpolation='Linear';tex.extension='REPEAT'
    normal=tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=strength
    tree.links.new(tex.outputs['Color'],normal.inputs['Color']);tree.links.new(normal.outputs['Normal'],shader.inputs['Normal'])


def refine(objects,scale_metadata):
    """Refine the existing high garments; return a compact modification record."""
    if isinstance(objects,dict):objects=list(objects.values())
    named={o.name:o for o in objects};sc=float(scale_metadata['scale']);off=Vector(scale_metadata['offset'])
    native=lambda p:Vector(p)/sc-off
    final=lambda p:(Vector(p)+off)*sc
    body=named['Rain_body_nomask'];body_before=[v.co.copy() for v in body.data.vertices]
    top=named['Ava_CreamTop_RainSurface'];apron=named['Ava_FittedCafeApron'];pocket=named['Ava_ApronPocket'];jeans=named['Rain_jeans']
    changed={}
    def edit(ob,fn):
        maximum=0
        for v in ob.data.vertices:
            old=v.co.copy();v.co=final(fn(native(old)));maximum=max(maximum,(v.co-old).length)
        ob.data.update();changed[ob.name]={'vertices':len(ob.data.vertices),'maxDisplacementMetres':maximum}
    edit(top,lambda p:p+_cloth_delta(p))
    # Broaden the actual rolled fabric edge along the native arm axis. Retain
    # its source cross-section, with a slight nonuniform cloth turn-over.
    for name,ob in named.items():
        if 'RolledSleeve' not in name:continue
        pts=[native(v.co) for v in ob.data.vertices];cy=sum(p.y for p in pts)/len(pts);cz=sum(p.z for p in pts)/len(pts)
        sign=1 if sum(p.x for p in pts)>0 else -1
        def cuff(p):
            x,y,z=p;theta=math.atan2(z-cz,y-cy);radial=Vector((0,y-cy,z-cz)).normalized()
            return Vector((sign*.405+(x-sign*.405)*1.65,y,z))+radial*(.0012+.0007*math.cos(2*theta+.4))
        edit(ob,cuff)
    def tree(ob):
        ob.data.calc_loop_triangles()
        return BVHTree.FromPolygons([native(v.co) for v in ob.data.vertices],[t.vertices for t in ob.data.loop_triangles],all_triangles=True)
    top_tree=tree(top);jeans_tree=tree(jeans);old_apron=tree(apron);old_pocket=tree(pocket)
    def hit(b,x,z):
        p,n,i,d=b.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
        return p.y if p is not None else None
    def body_front(x,z):
        values=[h for b in (top_tree,jeans_tree) if (h:=hit(b,x,z)) is not None]
        return min(values) if values else None
    widths=[(.637,.151),(.648,.165),(.70,.166),(.78,.160),(.87,.151),(.95,.137),(1.015,.120),(1.065,.096),(1.12,.079),(1.196,.074)]
    def width(z):
        for (za,wa),(zb,wb) in zip(widths,widths[1:]):
            if za<=z<=zb:return wa+(wb-wa)*(z-za)/(zb-za)
        return widths[0][1] if z<widths[0][0] else widths[-1][1]
    # Smooth bridging over the chest, then progressively wrap the side edges
    # toward the true torso/hip surface. A clearance clamp prevents penetration.
    def drape(x,z):
        w=width(z);t=min(1,abs(x)/w)
        samples=[v for j in range(13) if (v:=body_front(w*(-1+2*j/12),z)) is not None]
        envelope=min(samples) if samples else -.10;local=body_front(x,z)
        y=envelope-.0075
        if local is not None:y+=(local-.0075-y)*(.88*_smooth(.34,.98,t))
        else:y+=.045*t*t
        if z<.98:
            fade=_smooth(.64,.73,z)*(1-_smooth(.94,.985,z));spread=.082+.055*(.98-z)
            y+=fade*(-.0038*_bell(abs(x),spread,.016)+.0015*_bell(abs(x),spread+.022,.015))
        else:
            y-=.0017*_bell(z,1.177-.42*abs(x),.010)*_smooth(.035,.075,abs(x))
        if local is not None:y=min(y,local-.005)
        return y
    # Projected body samples can change branch around the side of the waist.
    # Fair a bounded correction field first, rather than stamping those ray
    # discontinuities into otherwise good authored garment surfaces.
    rows=29;cols=25;field=[]
    for i in range(rows):
        z=.637+(1.196-.637)*i/(rows-1);w=width(z);line=[]
        for j in range(cols):
            x=w*(-1+2*j/(cols-1));old=hit(old_apron,x,z)
            if old is None:
                near,_,_,_=old_apron.find_nearest(Vector((x,-.2,z)))
                old=near.y if near is not None else drape(x,z)
            line.append(max(-.010,min(.008,drape(x,z)-old)))
        field.append(line)
    for _ in range(8):
        previous=field
        field=[[.45*previous[i][j]+.55*sum(previous[r][c] for r,c in [(max(0,i-1),j),(min(rows-1,i+1),j),(i,max(0,j-1)),(i,min(cols-1,j+1))])/4 for j in range(cols)] for i in range(rows)]
    def apron_form(p):
        x,y,z=p;v=max(0,min(rows-1-1e-7,(z-.637)/(1.196-.637)*(rows-1)));u=max(0,min(cols-1-1e-7,(x/width(z)+1)/2*(cols-1)))
        i=int(v);j=int(u);fy=v-i;fx=u-j
        dy=(field[i][j]*(1-fx)+field[i][j+1]*fx)*(1-fy)+(field[i+1][j]*(1-fx)+field[i+1][j+1]*fx)*fy
        old=hit(old_apron,x,z);local=body_front(x,z)
        if dy>0 and old is not None and local is not None:dy=min(dy,max(0,local-.005-old))
        q=Vector((x,y+dy,z));t=min(1,abs(x)/width(z))
        q.z-=.0035*(1-t*t)*_smooth(1.166,1.196,z)
        return q
    edit(apron,apron_form);new_apron=tree(apron)
    def pocket_form(p):
        x,y,z=p;old=hit(old_pocket,x,z);layer=y-old if old is not None else 0
        z-=.0020*(1-min(1,abs(x)/.101)**2)*_smooth(.869,.888,z)
        ay=hit(new_apron,x,z)
        return Vector((x,(ay if ay is not None else drape(x,z))-.0025+layer,z))
    edit(pocket,pocket_form)
    for name,ob in named.items():
        if 'LeatherStrap' in name:
            def strap(p):
                q=p+_cloth_delta(p)
                if p.y<-.04:
                    old=hit(old_apron,p.x,p.z);new=hit(new_apron,p.x,p.z)
                    if old is not None and new is not None:q.y+=(new-old)*_bell(p.z,1.190,.012)
                return q
            edit(ob,strap)
        elif name=='Ava_ApronTie' or 'TieTail' in name or 'TieLoop' in name:edit(ob,lambda p:p+_cloth_delta(p))
    # New apron/cuff construction had no UV map in v0.1. A tangent normal on
    # an unmapped surface creates false per-face shading, so lay out cloth UVs
    # in the authored metre frame before assigning its small woven normal.
    for ob in objects:
        if not ob.data.materials or ob.data.materials[0].name not in ['Ava_CreamKnit','Ava_OliveApron']:continue
        uv=ob.data.uv_layers.active or ob.data.uv_layers.new(name='AvaClothUV')
        for loop in ob.data.loops:
            p=native(ob.data.vertices[loop.vertex_index].co)
            if 'RolledSleeve' in ob.name:
                angle=math.atan2(p.z-1.22,p.y+.019);uv.data[loop.index].uv=(p.x*3,angle/math.tau)
            else:uv.data[loop.index].uv=(p.x*3,p.z*3)
    _material_grain(bpy.data.materials['Ava_CreamKnit'],_weave_normal('Ava_KnitNormal_256',True),.24,.78)
    _material_grain(bpy.data.materials['Ava_OliveApron'],_weave_normal('Ava_CanvasNormal_256'),.19,.84)
    assert all(v.co==old for v,old in zip(body.data.vertices,body_before))
    return {'bodyCoordinatesUnchanged':True,'existingTopologyRetained':True,'garments':changed,'newImages':[{'name':'Ava_KnitNormal_256','size':[256,256]},{'name':'Ava_CanvasNormal_256','size':[256,256]}]}
