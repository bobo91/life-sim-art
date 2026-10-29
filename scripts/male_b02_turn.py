"""B02 bounded turn-foot correction on the existing 52-joint adapter.
Only existing leg/foot matrices change; no model, body or facial editing.
"""
import math
from mathutils import Matrix, Vector

DEFAULT_CONFIG = {
    'turnDegrees':90.0,
    'steps':[
        {'side':'R','start':.05,'end':.30,'yawDegrees':45.0,'offsetXYMeters':[-.035,-.10]},
        {'side':'L','start':.35,'end':.63,'yawDegrees':90.0,'offsetXYMeters':[0.0,0.0]},
        {'side':'R','start':.68,'end':.94,'yawDegrees':90.0,'offsetXYMeters':[0.0,0.0]},
    ],
    'liftMeters':.032,
    'stanceClearanceMeters':.00005,
    'liftPhase':.25,
    'settlePhase':.75,
}

def smooth5(t):
    t=max(0.0,min(1.0,t))
    return t*t*t*(10+t*(-15+6*t))

def foot_targets(u,rest,config=None):
    c=config or DEFAULT_CONFIG
    result={}
    for side in ['L','R']:
        origin=rest['Foot.'+side].translation.copy();origin.z+=c.get('stanceClearanceMeters',0.0);yaw=0.0;lift=0.0;phase=0.0;blend=0.0;in_swing=False
        for step in c['steps']:
            if step['side']!=side:continue
            end_yaw=math.radians(step['yawDegrees']);dest=Matrix.Rotation(end_yaw,4,'Z')@rest['Foot.'+side].translation
            dest.x+=step['offsetXYMeters'][0];dest.y+=step['offsetXYMeters'][1];dest.z+=c.get('stanceClearanceMeters',0.0)
            if u<=step['start']:break
            if u>=step['end']:
                origin=dest;yaw=end_yaw;phase=1.0;continue
            phase=(u-step['start'])/(step['end']-step['start']);a,b=c['liftPhase'],c['settlePhase'];blend=smooth5((phase-a)/(b-a))
            lift=c['liftMeters']*(smooth5(phase/a) if phase<a else 1.0 if phase<=b else smooth5((1-phase)/(1-b)))
            origin=origin.lerp(dest,blend);origin.z+=lift;yaw=yaw+(end_yaw-yaw)*blend;in_swing=True;break
        result[side]={'ankle':origin,'yaw':yaw,'lift':lift,'phase':phase,'inSwing':in_swing,'transferBlend':blend}
    return result

def apply_turn(mats,u,rest,config=None):
    """Correct B01's world-rotated feet with three small placements, retaining its upper body.

    mats/rest are dictionaries of armature-space 4x4 matrices. Call after the
    existing B01 buildpose('turn',u). Source rest lengths and ordinary LBS stay.
    """
    result={name:m.copy() for name,m in mats.items()};targets=foot_targets(u,rest,config)
    body_yaw=math.radians((config or DEFAULT_CONFIG)['turnDegrees'])*(3*u*u-2*u*u*u)
    bodyrot=Matrix.Rotation(body_yaw,4,'Z')
    forward=(bodyrot@Vector((0,-1,0))).normalized()
    for side in ['L','R']:
        upper='UpperLeg.'+side;lower='LowerLeg.'+side;foot='Foot.'+side;toe='Toes.'+side
        hip=(result['Hips']@rest['Hips'].inverted()@rest[upper]).translation
        ankle=targets[side]['ankle'];l1=(rest[lower].translation-rest[upper].translation).length;l2=(rest[foot].translation-rest[lower].translation).length
        v=ankle-hip;distance=v.length
        if distance>l1+l2-1e-6 or distance<abs(l1-l2)+1e-6:
            raise ValueError('B02 turn target unreachable: '+side+' u='+str(u)+' distance='+str(distance)+' lengths='+str((l1,l2)))
        direction=v.normalized();along=(l1*l1-l2*l2+distance*distance)/(2*distance);height=math.sqrt(max(0,l1*l1-along*along));perp=forward-direction*direction.dot(forward)
        if perp.length<1e-7:perp=Vector((1,0,0))-direction*direction.x
        knee=hip+direction*along+perp.normalized()*height
        for name,start,end,rest_end in [(upper,hip,knee,rest[lower].translation),(lower,knee,ankle,rest[foot].translation)]:
            initial_direction=bodyrot.to_3x3()@(rest_end-rest[name].translation)
            q=initial_direction.rotation_difference(end-start)
            m=q.to_matrix().to_4x4()@bodyrot@rest[name].to_3x3().to_4x4();m.translation=start;result[name]=m
        m=Matrix.Rotation(targets[side]['yaw'],4,'Z')@rest[foot].to_3x3().to_4x4();m.translation=ankle
        result[foot]=m;result[toe]=m@rest[foot].inverted()@rest[toe]
    return result
