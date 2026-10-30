"""Read native Rain face selections/shapes for static artist edits, no rig output."""
import argparse,sys,json,hashlib
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
src=Path(a.source).resolve();before=hashlib.sha256(src.read_bytes()).hexdigest()
assert before=='831ab6d837c679040285862b15dc9ee5180b018442a88aeaf92aaa7509b80258'
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False)
o=bpy.data.objects['GEO-rain-head'];keys=o.data.shape_keys.key_blocks;groups={g.index:g.name for g in o.vertex_groups}
def weight(v,part):return sum(g.weight for g in v.groups if part in groups[g.group])
shapes=['LipsAdjust','LipsWide.L','LipsWide.R','LipsPuff_Upper','LipsPuff_Lower']
d={'sourceSha256':before,'credit':'Rain Rig (CC) Blender Foundation | studio.blender.org','purpose':'Native authored masks/shapes used as static mesh-edit selections, no delivered rig or skin weights','vertices':[{'basis':list(keys['Basis'].data[v.index].co),'upperLid':weight(v,'DEF-Eyelid_Top_'),'lowerLid':weight(v,'DEF-Eyelid_Bot_'),'brow':weight(v,'DEF-Eyebrow_'),'deltas':{k:list(keys[k].data[v.index].co-keys[k].relative_key.data[v.index].co) for k in shapes}} for v in o.data.vertices]}
out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(d,separators=(',',':'))+'\n',encoding='utf8');assert hashlib.sha256(src.read_bytes()).hexdigest()==before
print(json.dumps({'vertices':len(d['vertices']),'nativeShapes':shapes,'sourceUnchanged':True}))
