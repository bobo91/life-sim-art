# ART-041 — beslut om ny metod för Ava

2026-10-30. **Nuvarande kandidat i PR #42 är underkänd (NO-GO).** PR:n förblir
draft. Inga fler småjusteringar av den modellen. Detta är research och ett
beslutsförslag; ingen ny modell, import, riggning eller animation har utförts.

## Varför A03 fungerar bättre

Bildgranskningen visar att A03:s försprång ligger i formgivningen som ärvts
från den professionellt modellerade Snow-basen. Hals, skuldergördel och överarm
hänger ihop; bröstkorg, midja och klädfall bildar en trovärdig helhet. Ansiktets
ögonhålor, kindben, näsa, munparti och käke bär varandra i flera vinklar.

Ava har i stället uppblåsta axel-/ärmvolymer, en abrupt halsövergång och en
förenklad bål. Den jämna ansiktsovalen saknar tillräckliga underliggande volymer.
Koden förklarar problemen: elliptiska loftringar, rör och pålagda ansiktsytor
sammanfogades med remesh/smoothing. Det kunde laga glipor men skapade inte
figurmodellering. Nästan samma polygonantal och bra tester gav därför inte
samma visuella kvalitet. Skillnaden i armposer begränsar exakta breddjämförelser.

## Högst tre konkreta baser

Bedömning av offentliga beskrivningar och officiella förhandsbilder, inte av
importerade produktfiler. Priser kontrollerade 30 oktober; artistarbete ingår
inte och slutlig moms kan variera.

| Bas | Pris och licens | Stil och Blender/Unity-väg |
|---|---|---|
| **[Blender Studio Rain v3](https://studio.blender.org/characters/rain/v3/)** — förstahandsval | **Gratis. CC BY 4.0:** kommersiell bearbetning/delning med attribution, licenslänk och ändringsnotis. Kredit: `Rain Rig (CC) Blender Foundation \| studio.blender.org`. | Professionell sammanhängande kvinnlig helkropp, samma stilfamilj som Snow. Native Blender, officiellt 4.1+. Bäst utgångsläge för A03-arbetsflödet. Befintligt ansikte/hår är inte Ava; faktisk spelbudget, materialbakning och GLB-export är ännu obeprövade. |
| **[wysp / Valentin Fischer — Stylized Female Basemesh](https://valentinfischer.artstation.com/store/dB9BJ/stylized-female-basemesh)** | **USD 8 Standard / USD 60 Extended Commercial.** Stock-assetlicens, inte CC0/CC BY. | Starkaste betalda alternativet för vuxen anatomi, särskilt nyckelben/axlar/bröstkorg. Tre kroppsformer; välj den mindre muskulösa. Mer heroisk än A03. Låg-/högupplöst OBJ samt ZTL; inget utlovat native Blender-underlag eller hår i OBJ. OBJ → Blender → GLB är rimligt men otestat. |
| **[Rodrigo Estero — Stylized Female Basemesh](https://www.artstation.com/marketplace/p/GGPWz/stylized-female-basemesh)** | Visat **USD 11,84 Standard / USD 58,31 Extended**, inklusive visad regional moms. Stock-assetlicens. | Native Blender samt FBX/OBJ, realtids- och UDIM-UV. Sammanhängande modellerad anatomi, men stora ögon, smalare överkropp och bredare höfter ger starkare karikatyr än A03. Formatfördel, ingen självklar stilvinst. Ingen produktimport testad. |

För båda butikskandidaterna begränsar Standard ett kommersiellt verk till
2 000 försäljningar eller 20 000 månatliga visningar; Extended saknar dessa
gränser. [Produkt-EULA](https://www.artstation.com/marketplace-product-eula)
medger spel och bearbetning men inte generell spridning av köpt bas i öppna
källarkiv. [ArtStations §46](https://www.artstation.com/tos) begränsar NoAI-input
till generativ AI. Produktens tagg/tillstånd för vår agentbearbetning och
offentliga `.blend`/GLB-leverans är inte klarerat. Inget köp eller säljarutskick
är gjort.

## Rekommendation och Avas identitet

**Välj Rain v3 och kontrollerad artiststyrd anpassning av hela karaktären.**
[Snow och Rain hör uttryckligen till samma stiliserade familj](https://studio.blender.org/blog/introducing-snow/),
och Rain utvecklades med återkoppling om design och anatomi av
[Blender Studios artistteam](https://studio.blender.org/blog/introducing-rain/).
Det väger tyngre än att en bas är procedurgenererad eller har många reglage.

Behåll basens fungerande hals–axelparti och kroppsvolymer. Ge Ava egen identitet
genom samordnad formning av kinder, käke/haka, näsa och bryn/ögonparti; brunett
lös knut med ansiktsramande slingor; bruna ögon/fräknar; kroppsanpassad gräddvit
tröja, olivförkläde, mörka jeans och ljusa sneakers. Kläderna måste följa den
valda anatomin och ha avsiktligt modellerat fall. Färgbyte/frisyr räcker inte.
Python återanvänds för scenberedning, rendering, export och proveniens.

Äldre Rain-screening avrådde från ansiktsmatchning mot AI-porträttet. Här är
prioriteten en sammanhängande kvinnlig kropp och A03:s formspråk; det motiverar
omprövning, inte ett påstående om redan bevisad Ava-likhet. Den inspekterade
officiella Rain-bilden är märkt v2; v3-sidan styrker den aktuella tekniska
versionen, inte en ny ansiktsdesign.

Ägarens nästa beslut behöver omfatta **Rain v3 som bas och artiststyrd
meshbearbetning**, motsvarande det avgränsade Snow-undantaget. Inget sådant
undantag införs nu. Källkopian ska senare hållas intakt och arbetet bedömas
visuellt innan teknisk optimering. Unity-färdighet eller bevarad källrigg
utlovas inte. [CC BY-villkoren](https://creativecommons.org/licenses/by/4.0/)
ligger till grund för Rain-alternativet.

**Stopp här för bas-/metodval.** Inga nya tester, Blender-/Unity-körningar,
modellfiler, inköp, riggar, animationer, merges eller game-repoändringar.
