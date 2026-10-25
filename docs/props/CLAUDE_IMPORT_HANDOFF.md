# Överlämning till Claude: First Playable Day-props

Art-PR: [#34](https://github.com/bobo91/life-sim-art/pull/34). Bekräfta kontraktet i game-[#53](https://github.com/bobo91/life-sim-game/issues/53).

Ägaren har visuellt godkänt `prop_mailbox_001` och `prop_cafe_table_001` för First Playable Day. Inga fler estetiska ändringar behövs. Bordet är godkänt som neutralt, odukat grundtillstånd; dukning hanteras separat. Originalmesh och godkända Blender-bilder ska bevaras.

Claude saknar för närvarande credits. Denna överlämning ersätter inte Claudes uttryckliga kontraktsbekräftelse. Tystnad är inte godkännande. Ingen automatisk merge eller ändring i game-repots kod ingår i art-arbetet.

## Föreslaget importkontrakt

Den maskinläsbara källan är [FPD-PROPS-IMPORT-1](first-playable-unity-import-proposal.json). Förslaget är **inte accepterat ännu**.

- Unity `6000.5.8f1`, URP `17.5.0`, `com.unity.cloud.gltfast` `6.20.0`.
- Statisk import i Editor till Unity-mesh/material; ingen GLB-laddare i runtime.
- Meter, root scale `(1, 1, 1)`, pivot nederst i centrum, `+Y` uppåt och `+Z` framåt. Skala inte till gamla placeholder-bounds.
- Fyra opaka PBR-material per föremål. Bevara färg-, metallic- och roughness-värden samt URP-kompatibel glTF-materialgraf.

| Asset-ID | Mått XYZ (m) | Föreslagen root BoxCollider: center | Föreslagen size |
| --- | --- | --- | --- |
| `prop_mailbox_001` | `(0.36, 1.43, 0.62)` | `(0, 0.715, 0)` | `(0.36, 1.43, 0.62)` |
| `prop_cafe_table_001` | `(0.78, 0.74, 0.78)` | `(0, 0.37, 0)` | `(0.78, 0.74, 0.78)` |

Kollisionsboxarna är kandidater. Bordets box blockerar avsiktligt hela fotavtrycket; den behöver godkännas tillsammans med gångvägarna. Cafébordets provplacering är inte ett godkänt spelankare.

## Verifiering och återstående beslut

Se [Unity-evidens och begränsningar](../../evidence/first-playable-props-unity/README.md) och [grafikrapport 004](../../evidence/first-playable-props-unity/graphics-004/unity-game-lighting-report.json). Grafiktest 004 passerade i en isolerad kopia av spelets scen från commit `9a85db5`, med dess faktiska URP-ljus: material, normaler, bounds, skala/pivot, sparning/återöppning och kandidaternas fysikkontroller passerade. Originalscenen och GLB-filerna är oförändrade. Tre Canvas stängdes av endast i valideringskopian för att få fria jämförelsebilder. Detta var EditMode utan PlayMode eller UI-test; interaktioner, gångvägar och spelintegration är fortfarande inte verifierade. Kontraktsbekräftelsen är fortfarande öppen.

Claude behöver därefter:

- [ ] Läsa slutrapporten och bekräfta importer, versioner och statisk importväg i #53.
- [ ] Bekräfta uppmätt skala, pivot, orientering och bevarade materialvärden.
- [ ] Kontrollera URP-utseendet med spelets faktiska ljus och dokumenterade skillnader mot Blender.
- [ ] Bestämma spelägda kollisionsytor och kontrollera närliggande gångvägar samt slutlig bordsplacering.
- [ ] Säkerställa en tydlig brevlådeprompt oberoende av flaggan. Samordna nuvarande aktionsavstånd `2.2 m` och marköravstånd `5 m` med #51:s krav på prompt från `5 m`; besluta uttryckligen vilken regel som ska gälla och testa den i spelet.
- [ ] Lägga eventuell integration och kodändring i en separat game-PR för granskning. EditMode-rendering verifierar inte interaktions-UI eller gameplay.

Ägaren ska få slutrapporten före merge. PR #34 får inte mergas automatiskt.

När Unity-kontraktet är klart är `prop_cafe_counter_001`, `prop_cafe_chair_001` och `prop_tin_001` godkända att påbörjas med samma visuella formspråk, utan en ny lång designutredning. De hålls tills dess.
