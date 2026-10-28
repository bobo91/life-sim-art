"""One frozen A02 art direction; smooth geometry field, not an NPC parameter bank.
Coordinates are the evaluated A01 static metre frame, NOT original Snow Basis.
Future bind/key/bone transport requires an explicit, separately verified rebase.
"""
import math

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def bell(x,c,r):return math.exp(-((x-c)/r)**2)
def deform(point,c):
 x,y,z=point;ax=abs(x);front=1-smooth(-.10,-.025,y)
 neck=smooth(1.385,1.475,z);chin=bell(z,1.44,.045)
 width=c['cranialWidthScale']+(c['chinWidthScale']-c['cranialWidthScale'])*chin
 nx=x*(1-neck*(1-width));ny=y+c['chinProjectionBackMeters']*bell(z,1.435,.025)*bell(x,0,.06)*front;nz=z-c['chinDropMeters']*bell(z,1.455,.045)*front
 # Compact nose edit, excluding eyes and rear head.
 nose=(1-smooth(.023,.047,ax))*(1-smooth(.016,.043,abs(z-1.538)))*(1-smooth(-.105,-.085,y))
 nx*=1-(1-c['noseWidthScale'])*nose;ny+=c['noseProjectionBackMeters']*nose;ny-=.0018*bell(x,0,.014)*bell(z,1.567,.017)*(1-smooth(-.10,-.08,y))
 # Local QC rounding of the central nasal underside; wings/bridge stay fixed.
 nz+=.0032*bell(x,0,.012)*bell(z,1.525,.011)*(1-smooth(-.105,-.09,y))
 # Upper/lower lips move about ONE seam center, preserving their shared fit.
 lip=(1-smooth(.030,.050,ax))*(1-smooth(.018,.035,abs(z-1.495)))*(1-smooth(-.09,-.065,y))
 nx*=1-(1-c['lipWidthScale'])*lip;nz-=(z-1.495)*(1-c['lipFullnessScale'])*lip;ny+=c['lipProjectionBackMeters']*lip
 nz+=c['mouthCornerLiftMeters']*bell(ax,.029,.014)*bell(z,1.495,.013)*(1-smooth(-.09,-.065,y))
 # Smaller tucked pinnae; retain attachment roots with a continuous field.
 ear=smooth(.080,.125,ax)*math.exp(-((z-1.585)/.085)**4)
 nx-=math.copysign(c['earTuckMeters']*ear,x);nz-=(z-1.585)*(1-c['earHeightScale'])*ear;ny+=(.026-y)*.13*ear+.002*ear
 # Globe + socket transform is uniform near each eye, blended into the face.
 for side in [-1,1]:
  cx=side*.043442;cy=-.0458;cz=1.5813
  radius=math.sqrt((x-cx)**2+(y-cy)**2+(z-cz)**2);w=1-smooth(.034,.058,radius)
  ex=cx*c['eyeCenterWidthScale']+(x-cx)*c['eyeUniformScale'];ey=cy+(y-cy)*c['eyeUniformScale'];ez=cz+(z-cz)*c['eyeUniformScale']
  nx=nx*(1-w)+ex*w;ny=ny*(1-w)+ey*w;nz=nz*(1-w)+ez*w
 return (nx,ny,nz)
def skin_point(point,c):
 x,y,z=point;nx,ny,nz=deform(point,c)
 # Open only the upper lid tissue slightly; never deform globe shape for expression.
 for side in [-1,1]:
  w=bell(x,side*.043442,.027)*bell(z,1.598,.011)*bell(y,-.071,.021)*smooth(1.582,1.590,z)
  nz+=c['upperLidRaiseMeters']*w
 return (nx,ny,nz)
