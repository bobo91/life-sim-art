"""Three original commercial-front modules; source Z up / exterior -Y.

The 2 m storefront and awning bays connect to the existing 6 m house span.
Sign letters are original closed geometric strokes, not an imported font.
Only the temporary brand label is configurable; no business identity is fixed.
"""
import json
import math
import unicodedata

from building_geometry import G, box, beam, finish


def build_storefront(config):
    """Actual structural opening, with a recessed two-pane opaque insert."""
    g=G()
    siding,trim,wood,glass=0,1,2,3
    # The structural pieces never cross the clear central window aperture.
    for x,label in ((-.915,'left'),(.915,'right')):
        box(g,label+'_structural_pier',.17,.18,0,2.8,siding,
            center=(x,0),bevel=.002)
    box(g,'solid_low_shopfront_base',1.66,.18,0,.25,siding,bevel=.002)
    box(g,'solid_shopfront_header',1.66,.18,2.45,2.8,siding,bevel=.002)
    # Broad vertical pilasters and panelled low base replace domestic siding.
    for x,label in ((-.915,'left'),(.915,'right')):
        box(g,label+'_painted_pilaster',.135,.09,.035,2.755,trim,
            center=(x,-.112),bevel=.009)
    box(g,'low_front_panel',1.61,.055,.035,.205,wood,
        center=(0,-.105),bevel=.006)
    box(g,'shopfront_top_rail',1.68,.12,2.43,2.51,trim,
        center=(0,-.10),bevel=.007)
    box(g,'projecting_window_sill',1.73,.23,.20,.265,trim,
        center=(0,-.055),bevel=.007)
    # The timber sash has real depth, set behind the projecting cream casing.
    for x,label in ((-.797,'left'),(.797,'right')):
        box(g,label+'_sash',.058,.09,.265,2.43,wood,
            center=(x,-.012),bevel=.005)
    for low,high,label in ((.265,.325,'bottom'),(2.365,2.43,'top')):
        box(g,label+'_sash',1.536,.09,low,high,wood,
            center=(0,-.012),bevel=.005)
    box(g,'slim_central_mullion',.036,.065,.325,2.365,trim,
        center=(0,-.026),bevel=.004)
    # Tall glazing reads as a shopfront, rather than the house's four panes.
    for x,label in ((-.395,'left'),(.395,'right')):
        box(g,label+'_large_opaque_pane',.742,.016,.331,2.359,glass,
            center=(x,.017),bevel=.001)
    obj=finish(config,g,('siding','trim','wood','glass'))
    obj['moduleAnchor']='wall-bay-bottom-centre'
    obj['sourceWallOpeningXZ']=[-.83,.83,.25,2.45]
    obj['sourceWallThicknessMeters']=.18
    obj['glassPolicy']='Opaque PBR insert; structural aperture exists behind it; no transmission dependency'
    obj['commercialStyle']='Broad shopfront pilasters, low panelled base and tall two-pane display glazing'
    return obj


def _striped_prism(g,name,profile,xmin,xmax,bands,materials):
    """One closed mesh with banded face materials, no stacked surface layers."""
    count=len(profile)
    vertices=[(xmin+(xmax-xmin)*i/bands,y,z)
              for i in range(bands+1) for y,z in profile]
    faces=[tuple(reversed(range(count)))];mats=[materials[0]]
    for i in range(bands):
        material=materials[i%len(materials)]
        for j in range(count):
            k=(j+1)%count
            faces.append((i*count+j,i*count+k,(i+1)*count+k,(i+1)*count+j));mats.append(material)
    faces.append(tuple(bands*count+j for j in range(count)));mats.append(materials[-1])
    g.part(name,vertices,faces,mats)


def _scalloped_valance(g):
    # Each stripe has a soft single dip. Adjacent strips share edges, rather
    # than having duplicate coplanar side caps between coloured pieces.
    bands=16;vertices=[]
    for i in range(bands+1):
        x=-1+2*i/bands;bottom=-.40 if i%2==0 else -.44
        vertices.extend(((x,-1.195,bottom),(x,-1.23,bottom),
                         (x,-1.23,-.27),(x,-1.195,-.27)))
    faces=[(3,2,1,0)];mats=[0]
    for i in range(bands):
        for j in range(4):
            k=(j+1)%4
            faces.append((4*i+j,4*i+k,4*(i+1)+k,4*(i+1)+j));mats.append((i//2)%2)
    faces.append(tuple(4*bands+j for j in range(4)));mats.append(1)
    g.part('single_closed_striped_scalloped_valance',vertices,faces,mats)


def build_fascia(config):
    """Continuous fascia + striped canvas awning; anchor at wall-top datum.

    Install source/world Z3.20. The valance bottom is consequently Z2.76,
    leaving 2.16 m clear above the existing .60 m floor datum.
    """
    g=G();roof,trim,wood=0,1,2
    box(g,'painted_commercial_fascia',2,.12,0,.56,roof,
        center=(0,-.10),bevel=.006)
    for low,high,label in ((.015,.055,'lower'),(.50,.54,'upper')):
        box(g,label+'_continuous_cream_pinstripe',2,.05,low,high,trim,
            center=(0,-.17),bevel=.003)
    _striped_prism(g,'single_closed_striped_canvas',
        [(-.10,-.03),(-1.20,-.25),(-1.20,-.30),(-.10,-.08)],-1,1,8,(roof,trim))
    _scalloped_valance(g)
    for x,label in ((-.88,'left'),(.88,'right')):
        beam(g,label+'_awning_support',(x,-.09,-.42),(x,-1.04,-.275),.038,wood)
    obj=finish(config,g,('roof','trim','wood'))
    obj['moduleAnchor']='wall-top-bay-centre'
    obj['sourceConnectionSpanX']=[-1,1]
    obj['sourceRecommendedInstallZ']=3.2
    obj['clothPolicy']='Opaque closed striped solids; no cloth simulation or transparent surface'
    return obj


# Original geometric uppercase stroke alphabet. Points are normalized X/Z;
# curves use short angular strokes so every element remains a closed solid.
GLYPHS={
 'A':[((0,0),(.5,1),(1,0)),((.22,.42),(.78,.42))],
 'B':[((0,0),(0,1),(.7,1),(1,.8),(.7,.52),(0,.52)),((.7,.52),(1,.29),(.8,0),(0,0))],
 'C':[((1,.88),(.75,1),(.2,1),(0,.8),(0,.2),(.2,0),(.75,0),(1,.12))],
 'D':[((0,0),(0,1),(.65,1),(1,.75),(1,.25),(.65,0),(0,0))],
 'E':[((1,1),(0,1),(0,0),(1,0)),((0,.5),(.8,.5))],
 'F':[((0,0),(0,1),(1,1)),((0,.5),(.8,.5))],
 'G':[((1,.86),(.75,1),(.2,1),(0,.8),(0,.2),(.2,0),(1,0),(1,.47),(.55,.47))],
 'H':[((0,0),(0,1)),((1,0),(1,1)),((0,.5),(1,.5))],
 'I':[((0,1),(1,1)),((.5,0),(.5,1)),((0,0),(1,0))],
 'J':[((0,1),(1,1),(1,.2),(.8,0),(.2,0),(0,.2))],
 'K':[((0,0),(0,1)),((1,1),(0,.5),(1,0))],
 'L':[((0,1),(0,0),(1,0))],
 'M':[((0,0),(0,1),(.5,.45),(1,1),(1,0))],
 'N':[((0,0),(0,1),(1,0),(1,1))],
 'O':[((.2,0),(0,.2),(0,.8),(.2,1),(.8,1),(1,.8),(1,.2),(.8,0),(.2,0))],
 'P':[((0,0),(0,1),(.8,1),(1,.8),(1,.65),(.8,.5),(0,.5))],
 'Q':[((.2,0),(0,.2),(0,.8),(.2,1),(.8,1),(1,.8),(1,.2),(.8,0),(.2,0)),((.6,.35),(1,0))],
 'R':[((0,0),(0,1),(.8,1),(1,.8),(1,.65),(.8,.5),(0,.5)),((.5,.5),(1,0))],
 'S':[((1,.86),(.8,1),(.2,1),(0,.8),(.2,.5),(.8,.5),(1,.2),(.8,0),(.2,0),(0,.14))],
 'T':[((0,1),(1,1)),((.5,1),(.5,0))],
 'U':[((0,1),(0,.2),(.2,0),(.8,0),(1,.2),(1,1))],
 'V':[((0,1),(.5,0),(1,1))],
 'W':[((0,1),(.2,0),(.5,.5),(.8,0),(1,1))],
 'X':[((0,1),(1,0)),((0,0),(1,1))],
 'Y':[((0,1),(.5,.5),(1,1)),((.5,.5),(.5,0))],
 'Z':[((0,1),(1,1),(0,0),(1,0))],
 '0':[((.2,0),(0,.2),(0,.8),(.2,1),(.8,1),(1,.8),(1,.2),(.8,0),(.2,0))],
 '1':[((.15,.8),(.5,1),(.5,0)),((.15,0),(.85,0))],
 '2':[((0,.8),(.2,1),(.8,1),(1,.8),(1,.65),(0,0),(1,0))],
 '3':[((0,1),(.8,1),(1,.8),(.55,.5),(1,.2),(.8,0),(0,0))],
 '4':[((.8,0),(.8,1),(0,.35),(1,.35))],
 '5':[((1,1),(0,1),(0,.5),(.8,.5),(1,.3),(1,.2),(.8,0),(0,0))],
 '6':[((1,.9),(.8,1),(.2,1),(0,.8),(0,.2),(.2,0),(.8,0),(1,.2),(1,.4),(.8,.55),(0,.55))],
 '7':[((0,1),(1,1),(.25,0))],
 '8':[((.2,.5),(0,.7),(0,.8),(.2,1),(.8,1),(1,.8),(1,.7),(.8,.5),(.2,.5),(0,.3),(0,.2),(.2,0),(.8,0),(1,.2),(1,.3),(.8,.5))],
 '9':[((1,.45),(.2,.45),(0,.65),(0,.8),(.2,1),(.8,1),(1,.8),(1,.2),(.8,0),(.2,0))],
 '-':[((0,.5),(1,.5))],
}


def normalized_label(value):
    value=unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().upper()
    value=' '.join(value.split())
    if not value or len(value)>22 or any(c!=' ' and c not in GLYPHS for c in value):
        raise ValueError('Cafe sign supports 1..22 ASCII letters/digits/spaces/hyphens')
    return value


def add_label(g,text,*,width=2.60,height=.29,bottom=.13,y=-.076,
              material=1,stroke=None,prefix='original_letter'):
    """Add centred closed-stroke text in source X/Z, facing -Y.

    A street-name board can reuse this with its own width/height, bottom, Y
    mounting plane and material index. Returns the normalized actual label.
    Width is a maximum, not a forced stretch; long labels scale uniformly.
    """
    label=normalized_label(text)
    glyph_w=height*.16/.29;gap=height*.058/.29;space=height*.115/.29
    total=sum(space if c==' ' else glyph_w+gap for c in label)-gap
    scale=min(1,width/total);char_w=glyph_w*scale;char_h=height*scale
    thickness=(height*.026/.29 if stroke is None else stroke)*scale
    x=-total*scale/2
    for i,char in enumerate(label):
        if char==' ':x+=space*scale;continue
        for j,path in enumerate(GLYPHS[char]):
            for k,(a,b) in enumerate(zip(path,path[1:])):
                beam(g,f'{prefix}_{i}_{char}_{j}_{k}',
                    (x+a[0]*char_w,y,bottom+a[1]*char_h),
                    (x+b[0]*char_w,y,bottom+b[1]*char_h),thickness,material)
        x+=(glyph_w+gap)*scale
    return label


def build_sign(config):
    g=G();roof,trim,wood=0,1,2
    box(g,'soft_dark_signboard',3,.14,0,.55,roof,bevel=.018)
    for low,high,label in ((.015,.065,'lower'),(.485,.535,'upper')):
        box(g,label+'_timber_sign_rim',2.96,.06,low,high,wood,
            center=(0,-.07),bevel=.007)
    for x,label in ((-1.44,'left'),(1.44,'right')):
        box(g,label+'_timber_sign_rim',.08,.06,.065,.485,wood,
            center=(x,-.07),bevel=.007)
    label=add_label(g,config.get('cafeName','Juniper Cafe'),bottom=.13,material=trim)
    obj=finish(config,g,('roof','trim','wood'))
    obj['moduleAnchor']='bottom-centre'
    obj['temporaryCafeName']=label
    obj['labelConfigKey']='cafeName'
    obj['letterProvenance']='Original geometric closed-stroke alphabet; no imported font or logo'
    obj['interactionPolicy']='Static visual identity; editable temporary name, no gameplay'
    return obj


BUILDERS={'bld_cafe_storefront_200_001':build_storefront,
          'bld_cafe_fascia_200_001':build_fascia,
          'prop_cafe_sign_001':build_sign}
ROLES={'bld_cafe_storefront_200_001':('siding','trim','wood','glass'),
       'bld_cafe_fascia_200_001':('roof','trim','wood'),
       'prop_cafe_sign_001':('roof','trim','wood')}
# Source XYZ bounds are fixed by the surrounding structural envelopes, not
# measured from the generated file. Parent converts to exported X/Z/-Y.
BOUNDS={'bld_cafe_storefront_200_001':{'min':[-1,-.17,0],'max':[1,.09,2.8]},
        'bld_cafe_fascia_200_001':{'min':[-1,-1.23,-.44],'max':[1,-.04,.56]},
        'prop_cafe_sign_001':{'min':[-1.5,-.10,0],'max':[1.5,.07,.55]}}
