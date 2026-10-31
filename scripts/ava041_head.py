"""Ava's original face and swept bun. Analytic sculpt fields, no external mesh."""
import math, random
from mathutils import Vector
import ava041_geometry as g

TABLE=[(1.382,.024,.043,.026),(1.392,.041,.057,.043),(1.409,.057,.065,.057),
       (1.435,.071,.068,.071),(1.465,.083,.065,.080),(1.493,.089,.063,.084),
       (1.523,.089,.063,.085),(1.553,.087,.067,.083),(1.580,.080,.063,.077),
       (1.603,.060,.050,.059),(1.619,.029,.026,.029),(1.625,.002,.002,.002)]
def bell(x,c,w):return math.exp(-((x-c)/w)**2)
def face_y(x,z):
    w,front,back=g.interp(TABLE,z); t=max(-.9999,min(.9999,x/w))
    y=.010-front*math.sqrt(1-t*t)
    # Broad orbital hollows, malar plane, tapered bridge, nostril wings, chin.
    for s in (-1,1):
        y+=.008*bell(x,s*.040, .024)*bell(z,1.525,.015)
        y-=.005*bell(x,s*.039,.024)*bell(z,1.553,.010)
        y-=.010*bell(x,s*.054,.024)*bell(z,1.493,.017)
        y-=.009*bell(x,s*.013,.009)*bell(z,1.477,.008)
    y-=.014*bell(x,0,.012)*bell(z,1.511,.029)
    y-=.030*bell(x,0,.013)*bell(z,1.482,.012)
    y+=.004*bell(x,0,.007)*bell(z,1.470,.004)
    y-=.006*bell(x,0,.037)*bell(z,1.441,.021)
    y-=.005*bell(x,0,.025)*bell(z,1.406,.013)
    return y

def build(mats,seed):
    out=[];n=64;rows=41;verts=[];faces=[]
    zs=[1.382+(1.623-1.382)*i/(rows-1) for i in range(rows)]
    for z in zs:
        w,front,back=g.interp(TABLE,z)
        for j in range(n):
            a=2*math.pi*j/n;x=w*math.sin(a);c=math.cos(a)
            base=.010-(front if c>=0 else back)*c
            y=base+(face_y(x,z)-(.010-front*math.sqrt(max(0,1-(x/w)**2))))*max(0,c)**6
            verts.append((x,y,z))
    for i in range(rows-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;faces.append((a,b,b+n,a+n))
    verts.extend([(0,.009,1.379),(0,.010,1.625)])
    for j in range(n):
        faces.append((len(verts)-2,(j+1)%n,j));faces.append((len(verts)-1,(rows-1)*n+j,(rows-1)*n+(j+1)%n))
    head=g.mesh('AVA_Head',verts,faces,mats['skin']);out.append(head)
    def tint(p,c):
        x,y,z=p;w=min(1,max(0,(-y-.01)/.04));blush=sum(.22*bell(x,s*.055,.022)*bell(z,1.491,.018) for s in (-1,1))*w
        target=g.linear((.76,.37,.30));return tuple(a*(1-blush)+b*blush for a,b in zip(c,target))
    g.paint(head,tint)
    # Neck has a shaped shoulder flare, overlapped inside sweater and jaw.
    vv=[];ff=[]
    for i,(z,rx,ry,cy) in enumerate([(1.265,.100,.065,.022),(1.291,.068,.048,.019),(1.322,.039,.034,.017),(1.367,.035,.034,.017),(1.407,.041,.041,.024)]):
        for j in range(32):a=2*math.pi*j/32;vv.append((rx*math.sin(a),cy-ry*math.cos(a),z))
    for i in range(4):
        for j in range(32):a=i*32+j;b=i*32+(j+1)%32;ff.append((a,b,b+32,a+32))
    ff.extend([tuple(reversed(range(32))),tuple(128+j for j in range(32))]);out.append(g.mesh('AVA_Neck',vv,ff,mats['skin']))
    # Ears: closed pinna bowls with a folded helix and a shaded concha.
    for s in (-1,1):
        vv=[];ff=[];N=24
        for k,r in enumerate([.0,.25,.55,.80,1.,.86,.43]):
            for j in range(N):
                a=2*math.pi*j/N
                x=s*(.087+.017*r*math.cos(a));z=1.508+.030*r*math.sin(a)
                y=[-.003,-.001,-.002,-.013,-.008,.006,.010][k]+.004*math.cos(a)
                # Tiny central ring avoids coincident fan geometry.
                if k==0:x=s*(.087+.001*math.cos(a));z=1.508+.001*math.sin(a)
                vv.append((x,y,z))
        for k in range(6):
            for j in range(N):a=k*N+j;b=k*N+(j+1)%N;ff.append((a,b,b+N,a+N))
        ff.extend([tuple(reversed(range(N))),tuple(6*N+j for j in range(N))])
        ear=g.mesh('AVA_Ear_'+str(s),vv,ff,mats['skin']);out.append(ear)
        g.paint(ear,lambda p,c:tuple(v*.78 for v in c) if abs(p.x)<.092 and p.y>-.005 else c)
        pts=[(s*(.096+.007*math.cos(a)), -.011,1.480+.010*math.sin(a)) for a in [2*math.pi*j/20 for j in range(21)]]
        out.append(g.tube('AVA_GoldHoop_'+str(s),pts,.0011,mats['detail'],6))
    # Almond sclera and sculpted upper/lower lids, with inset brown irises.
    for s in (-1,1):
        cx=s*.0395;cz=1.524;half=.025
        def aperture(t,upper):
            return cz+.002*t+(.0087 if upper else -.0060)*max(0,1-t*t)**.7
        def eye_y(x,z):
            t=(x-cx)/half;v=(z-(cz+.002*t))/.011
            return face_y(x,z)-.0015-.0075*max(0,1-t*t)*max(0,1-v*v)
        vv=[];ff=[];NX=32;NY=8
        for i in range(NX+1):
            t=-.9998+1.9996*i/NX;x=cx+half*t
            for j in range(NY+1):
                z=aperture(t,False)+(aperture(t,True)-aperture(t,False))*j/NY
                vv.append((x,eye_y(x,z),z))
        for i in range(NX):
            for j in range(NY):a=i*(NY+1)+j;ff.append((a,a+NY+1,a+NY+2,a+1))
        eye=g.mesh('AVA_EyeWhite_'+str(s),vv,ff,mats['shoe']);out.append(eye);g.paint(eye,lambda p,c:g.linear((.87,.84,.73)))
        for upper in (True,False):
            vv=[];ff=[]
            for i in range(1,32):
                t=-1+2*i/32;x=cx+half*t;z=aperture(t,upper)
                for j in range(4):
                    f=j/3;zz=z+(1 if upper else -1)*(.005 if upper else .004)*math.sin(math.pi*(t+1)/2)**.6*f
                    yy=(eye_y(x,z)-.0008)*(1-f)+face_y(x,zz)*f-.001*math.sin(math.pi*f)
                    vv.append((x,yy,zz))
            for i in range(30):
                for j in range(3):a=i*4+j;ff.append((a,a+4,a+5,a+1))
            for t in (-1,1):
                x=cx+half*t;z=aperture(t,upper);tip=len(vv);vv.append((x,eye_y(x,z)-.0008,z))
                row=0 if t<0 else 30*4
                for j in range(3):ff.append((tip,row+j,row+j+1))
            lid=g.mesh('AVA_'+('Upper' if upper else 'Lower')+'Lid_'+str(s),vv,ff,mats['skin']);out.append(lid)
            for poly in list(lid.data.polygons)[-6:]:poly.use_smooth=False
            if upper:
                pts=[]
                for i in range(26):t=-.97+1.94*i/25;x=cx+half*t;z=aperture(t,True);pts.append((x,eye_y(x,z)-.0008,z))
                lash=g.tube('AVA_Lash_'+str(s),pts,[.0004+.00055*math.sin(math.pi*i/25) for i in range(26)],mats['hair'],5);out.append(lash)
        # Iris disk is conformed to the visible eye patch rather than a protruding sphere.
        for label,radius,col,offset in [('Iris',.0095,(.27,.14,.062),.00035),('Pupil',.0041,(.045,.027,.018),.00055)]:
            vv=[(cx,eye_y(cx,cz)-offset,cz)];ff=[]
            for j in range(40):
                a=2*math.pi*j/40;x=cx+radius*math.cos(a);z=cz+radius*math.sin(a)
                t=(x-cx)/half;z=max(aperture(t,False)+.0001,min(aperture(t,True)-.0001,z))
                vv.append((x,eye_y(x,z)-offset,z))
            for j in range(40):ff.append((0,j+1,(j+1)%40+1))
            ob=g.mesh('AVA_'+label+'_'+str(s),vv,ff,mats['hair']);out.append(ob);g.paint(ob,lambda p,c,col=col:g.linear(col))
        # One quiet physical highlight, geometry sized well below iris.
        pts=[(cx-.002,eye_y(cx-.002,cz+.003)-.0009,cz+.003),(cx-.0018,eye_y(cx-.0018,cz+.0032)-.0009,cz+.0032)]
        ob=g.tube('AVA_EyeGlint_'+str(s),pts,.00055,mats['shoe'],6);out.append(ob);g.paint(ob,lambda p,c:g.linear((.98,.95,.85)))
        pts=[]
        for i in range(23):
            t=i/22;x=s*(.016+.048*t);z=1.553+.008*math.sin(math.pi*t)-.005*t
            pts.append((x,face_y(x,z)-.002,z))
        out.append(g.tube('AVA_Brow_'+str(s),pts,[.0012+.0020*math.sin(math.pi*(i/22)**.65) for i in range(23)],mats['hair'],7,depth=.0012))
    # Integrated two-surface lips; tapered corners lift into a relaxed expression.
    for upper in (True,False):
        vv=[];ff=[]
        for i in range(41):
            t=-.998+1.996*i/40;x=.029*t;seam=1.440+.0035*abs(t)**1.8
            edge=seam+((.005+.002*bell(abs(x),.009,.005)) if upper else -.007)*max(0,1-t*t)**.7
            for j in range(7):
                v=j/6;z=seam*(1-v)+edge*v
                y=face_y(x,z)-(.0015+.0025*math.sin(math.pi*v)**.7)*max(0,1-t*t)**.5
                vv.append((x,y,z))
        for i in range(40):
            for j in range(6):a=i*7+j;ff.append((a,a+7,a+8,a+1))
        ob=g.mesh('AVA_'+('Upper' if upper else 'Lower')+'Lip',vv,ff,mats['lip']);out.append(ob)
        g.paint(ob,lambda p,c:tuple(v*(.92 if upper else 1.09) for v in c))
    pts=[]
    for i in range(41):t=-1+2*i/40;x=.029*t;z=1.440+.0035*abs(t)**1.8;pts.append((x,face_y(x,z)-.0021,z))
    ob=g.tube('AVA_MouthLine',pts,[.00025+.00018*math.sin(math.pi*i/40) for i in range(41)],mats['lip'],5);out.append(ob);g.paint(ob,lambda p,c:g.linear((.40,.23,.17)))
    # Nostril slits sit on the sculpted alar underside; no dark sphere noses.
    for s in (-1,1):
        pts=[]
        for i in range(13):t=i/12;x=s*(.005+.010*t);z=1.474-.0018*math.sin(math.pi*t);pts.append((x,face_y(x,z)-.00045,z))
        ob=g.tube('AVA_Nostril_'+str(s),pts,.00065,mats['lip'],5);out.append(ob);g.paint(ob,lambda p,c:g.linear((.33,.18,.13)))
    # Seeded fine freckles; physical patches with no texture, conform to skin surface.
    rng=random.Random(seed);vv=[];ff=[]
    for k in range(114):
        x=rng.uniform(-.071,.071);z=rng.uniform(1.481,1.511)
        if abs(x)<.017 and z<1.495:continue
        r=rng.uniform(.00035,.00072);start=len(vv)
        for j in range(5):a=2*math.pi*j/5;xx=x+math.cos(a)*r;zz=z+math.sin(a)*r*.8;vv.append((xx,face_y(xx,zz)-.00013,zz))
        ff.append(tuple(start+j for j in range(5)))
    ob=g.mesh('AVA_Freckles',vv,ff,mats['skin']);out.append(ob);g.paint(ob,lambda p,c:g.linear((.47,.265,.16)))
    out.extend(hair(mats))
    return out

def hair(mats):
    out=[];vv=[];ff=[];N=48;R=16
    hair_table=[(z,w+.006,f+.006,b+.006) for z,w,f,b in TABLE[:-1]]+[(1.625,.019,.016,.019),(1.634,.001,.001,.001)]
    # Hairline is low at nape/temples and high enough to expose forehead.
    for i in range(R):
        u=i/(R-1)
        for j in range(N):
            a=2*math.pi*j/N;c=math.cos(a)
            zmin=1.503+.078*max(0,c)**.65+.035*min(0,c)
            z=zmin+(1.632-zmin)*math.sin(u*math.pi/2)
            w,front,back=g.interp(hair_table,z)
            ripple=1+.007*math.cos(14*a+u*2)
            vv.append((w*math.sin(a)*ripple,.010-(front if c>=0 else back)*c*ripple,z))
    for i in range(R-1):
        for j in range(N):a=i*N+j;b=i*N+(j+1)%N;ff.append((a,b,b+N,a+N))
    ff.append(tuple((R-1)*N+j for j in range(N)))
    out.append(g.mesh('AVA_HairCap',vv,ff,mats['hair']))
    # Broad original swept clumps follow the skull into a loosely pinned high bun.
    for side in (-1,1):
        for k in range(5):
            pts=[];rads=[]
            for i in range(17):
                t=i/16
                a=side*((.10+k*.28)*(1-t)+2.85*t)
                theta=(.97+k*.10)*(1-t)+.40*t
                z=1.525+.108*math.cos(theta);w,f,b=g.interp(hair_table,z);c=math.cos(a)
                x=w*math.sin(a);y=.010-(f if c>=0 else b)*c
                pts.append((x,y,z));rads.append(.0006+.0065*math.sin(math.pi*t)**.5*(1-.06*k))
            out.append(g.tube('AVA_SweptLock_'+str(side)+'_'+str(k),pts,rads,mats['hair'],7,depth=[r*.45 for r in rads]))
    # Bun is a closed lobed spiral mass with radiating swept ridges, not a sphere accessory.
    vv=[];ff=[];N=40;R=18
    for i in range(1,R):
        v=math.pi*i/R
        for j in range(N):
            a=2*math.pi*j/N;wave=1+.075*math.sin(7*a+2.4*v)
            vv.append((-.008+.049*math.sin(v)*math.cos(a)*wave,.043+.040*math.sin(v)*math.sin(a)*wave,1.645+.047*math.cos(v)))
    for i in range(R-2):
        for j in range(N):a=i*N+j;b=i*N+(j+1)%N;ff.append((a,b,b+N,a+N))
    vv.extend([(-.008,.043,1.692),(-.008,.043,1.598)])
    for j in range(N):ff.append((len(vv)-2,(j+1)%N,j));ff.append((len(vv)-1,(R-2)*N+j,(R-2)*N+(j+1)%N))
    out.append(g.mesh('AVA_LooseBun',vv,ff,mats['hair']))
    # Two face-framing wisps, asymmetrical ends and clear of eye apertures.
    for s in (-1,1):
        pts=[];rr=[]
        for i in range(29):
            t=i/28;pts.append((s*(.064+.025*math.sin(t*math.pi*.85)), -.046-.022*math.sin(t*math.pi)+.017*t,1.579-(.127 if s<0 else .105)*t))
            rr.append(.00065+.0045*(1-t)**.6)
        out.append(g.tube('AVA_TempleWisp_'+str(s),pts,rr,mats['hair'],7,depth=[r*.6 for r in rr]))
    # Nape wisps cover cap transition without colliding with collar.
    for s in (-1,1):
        pts=[(s*(.061-.025*t),.073+.004*math.sin(t*math.pi),1.512-.079*t) for t in [i/16 for i in range(17)]]
        out.append(g.tube('AVA_NapeWisp_'+str(s),pts,[.002*(1-i/17)+.0005 for i in range(17)],mats['hair'],6))
    return out
