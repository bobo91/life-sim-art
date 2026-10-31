"""Additional BEFORE crops from the preserved v0.1 delivered static source."""
import sys,argparse,json
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).parent))
from ava_rain_tools import sha,render
p=argparse.ArgumentParser();p.add_argument('--before',required=True);p.add_argument('--metadata',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
source=Path(a.before).resolve();before=sha(source);out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);meta=json.loads(Path(a.metadata).read_text())
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False);bpy.context.scene.cycles.samples=36;cam=bpy.context.scene.camera
focus=(0,meta['offset'][1]*meta['scale'],1.477*meta['scale'])
render(cam,out,'hair_rear_three_quarter','face',145,focus=focus)
render(cam,out,'clothes_detail','face',35,focus=(0,0,1.13),scale=1.05)
assert sha(source)==before
