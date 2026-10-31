# Begränsad reproduktion — huvud/hår

Kör från repo-roten. Blender 4.5.14 LTS, Python 3.14/Pillow 12.3.0. Program-/A03-sökvägarna nedan är de verifierade lokala sökvägarna från denna leverans; anpassa dem vid en annan installation. Alla utmatningsmappar ska vara nya. Källor laddas med script-autoexec avstängt.

```powershell
# Vid behov: hämta den exakta officiella fria källan och kontrollera låsta hashvärden.
python scripts/acquire_ava_rain.py --out build/ava-b-reproduce/source
$avaBlender = 'C:/Users/rcalm/tools/blender/blender-4.5.14-windows-x64/blender.exe'
$avaSource = 'build/ava-b-reproduce/source/original/Rain v3.3/rain_v3.2.blend'
$avaA03 = 'C:/dir/life-sim-art/build/male-neutral-a01-worktree/build/male-neutral-a03/delivery-003/character.blend'

& $avaBlender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/prepare_ava_rain.py -- --source $avaSource --out build/ava-b-reproduce/native-neutral --lids 0.18 --smile 0 --views none
python scripts/prepare_ava_rain_textures.py --source "build/ava-b-reproduce/source/original/Rain v3.3/textures" --out build/ava-b-reproduce/textures
& $avaBlender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/build_ava_b_head.py -- --source build/ava-b-reproduce/native-neutral/static-source.blend --original $avaSource --textures build/ava-b-reproduce/textures --out build/ava-b-reproduce/candidate --a03 $avaA03 --samples 48
& $avaBlender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/review_ava_b_head.py -- --candidate build/ava-b-reproduce/candidate --a03 $avaA03 --samples 48
python scripts/compose_ava_b_head_review.py --candidate build/ava-b-reproduce/candidate --outdir build/ava-b-reproduce/boards
```

I denna leverans användes de redan verifierade originalen i `build/ava-rain-v01/source/`, de oförändrade källbaserade hud-/ögonkartorna i `build/ava-rain-v01/textures/`, en ny extraktion i `build/ava-b-head-v01/native-neutral/` och ny kandidat `build/ava-b-head-v01/delivery-001/`. Ingen gammal Ava-kandidat är indata. Rain-originalets filhash och B-arkets hash måste stämma eller stoppas bygget. Se `configs/ava_b_head_v01.json` och referenslåset för seed/formstationer. En reproducerbar kommandokedja betyder här dokumenterade indata/formkontroller; ingen byteidentitet mellan Blender-installationer utlovas.

`ava_b_head_review.blend` innehåller de separata edit-mesharna samt den sammanfogade hudkopian för visning; de separata hudmesharnas renderflagga är avstängd för att undvika dubblerad hud. `ava_b_head_review_only.glb` innehåller endast statiskt huvud/hår, utan kropp/kläder, rigg, morphs eller animation. Ingen fullständig spelimport har gjorts.
