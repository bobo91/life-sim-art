# Ava Rain v0.2 — sista visuella förbättringen

**Stopp för slutligt visuellt GO/NO-GO i draft-PR #42.** Före är levererad Rain Ava v0.1; efter är samma Rain-baserade karaktär med riktade formändringar. Alla bilder är faktiska Blender-renderingar; bildarken ordnar och skalar enbart dessa bilder.

- Ansikte: lugnare ögonöppning och bryn som samverkar, bredare avslappnat munparti, tydligare käkstöd, lugnare nedre kindplan och mer sammanhängande näsrygg. Rains ursprungliga ansiktsytor, lip-neutralform och ögonlocksurval används. Ögongloberna och hals-/axel-/bröstanatomin har inte skulpterats om.
- Hår: lägre lindad knut med instoppat centrum, byggd genom bearbetning av Rains faktiska hästsvans; bredare kontakt mot uppsamlingen. Ansiktsslingornas ursprungliga infästning bevaras och deras fria del får frigång.
- Kläder: små spänningsveck vid ärmar/axlar, tydligare uppvik, försiktigare förklädesfall och två små 256² vävnormaler. Den enkla fickan och hårknutens ganska regelbundna lindning är kvarvarande förenklingar.

Min bedömning: ett vuxnare och mer sammanhållet uttryck än v0.1, med bättre hårvolym och materialkänsla. A03 är fortfarande jämförelsen för finish; bilderna ska avgöra om helheten nu räcker. Inget automatiskt visuellt GO.

[Ansikte före/efter](previews/face-before-after.png) · [hår före/efter](previews/hair-before-after.png) · [helkropp före/efter](previews/body-before-after.png) · [kläder nära](previews/clothes-before-after.png) · [direkt A03-jämförelse i samma skala](previews/ava_a03_same_scale.png) · [normal spelkamera före/efter](previews/normal-game-camera.png). Dagsljus/skugga är samma Blender-ljusproxy som förra leveransen, inte Unity eller en exakt caférekonstruktion.

Paketet länkas i [draft-PR #42](https://github.com/bobo91/life-sim-art/pull/42). Det innehåller redigerbar hög/reducerad källa, statisk GLB, fulla före/efter-bilder, frysta v0.1-indata och källrecept. Från paketets rot med Blender 4.5.14:

```powershell
& $blender --background --factory-startup --offline-mode --disable-autoexec --python-exit-code 1 --python scripts/refine_ava_rain.py -- --before before/character_high.blend --metadata before/report.json --native-edits inputs/native-face-edits.json --source-static inputs/static-source.blend --out reproduced --samples 36
```

Ingen stor ny testplattform eller optimeringsinsats. Tidigare statiska reduktion återanvänds, med mer geometri till hårknuten. Befintlig GLB-kontroll och faktisk återimport används för exporten. Inga riggar, animationer, Unity-integration, ändringar av A03/life-sim-game eller merge.

Rain Rig (CC) Blender Foundation | studio.blender.org — [Rain v3](https://studio.blender.org/characters/rain/v3/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). [Källlicens och ändringar](../../docs/characters/ava-morgan/RAIN_SOURCE_LICENSE.md). Ava-bearbetning: life-sim-art. A03-jämförelse endast: Snow Rig (CC) Blender Foundation | studio.blender.org — [Snow v4](https://studio.blender.org/characters/snow/v4/), samma licens. Originalfiler och A03 är oförändrade.
