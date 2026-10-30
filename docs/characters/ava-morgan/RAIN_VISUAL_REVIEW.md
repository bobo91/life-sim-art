# Ava Morgan — Rain visual v0.1

**Status: statisk visuell prototyp för ägarens GO/NO-GO. PR #42 förblir draft.** Den tidigare Python-genererade Ava-kroppen är fortsatt NO-GO och har inte använts. Ägaren godkände Rain v3 som ny metod, inte denna prototyps slutliga utseende.

## Visuell bedömning

**Axlar och överkropp:** Rains sammanhängande hals, axeltopp, bröstkorg och armhåla ger en väsentligt bättre anatomisk grund än den underkända modellen. Toppen utgår från dessa faktiska ytor. A03-jämförelsen använder samma meterskala, T-pose, kamera och studioljus; ingen separat uppskalning av Ava. Jag bedömer grundanatomin som jämförbar för denna statiska pose. Toppen har däremot färre övertygande tygveck än A03:s tröja, och ärmkanter/halsringning är fortfarande enkla. Ingen deformationskvalitet är bedömd.

**Ansikte:** faktisk Rain-topologi har fått smalare kranium, mindre sammanhängande ögon-/ögonlocksvolymer, omformade kinder, käke, haka, näsa, mun och öron. Bruna iris och diskreta fräknar tillkommer. Identiteten skiljer sig från originalets form och färger, men Rains släktskap är tydligt. **Jag bedömer ännu inte ansiktets finish som likvärdig med A03:** ögonen läser öppnare och uttrycket yngre, ögonbrynens ändar är grafiska och munpartiet är fortfarande fylligt. Det är den viktigaste visuella beslutspunkten, inte något som en godkänd export kan avgöra.

**Hår och kläder:** brunett, mjuk knut omformad från Rains faktiska hästsvans, två ansiktsramande slingor, gräddvit topp med uppvikta ärmar, olivförkläde, mörka originaljeans och ljusa originalsneakers. Knuten är förenklad och behöver mer naturlig lindning för produktionsfinish. Förklädet följer bröst/jeans utan de stora genomskärningar som sågs i arbetsproverna; ficka, knytband och läderremmar är enkla. Inga uppenbara öppna kroppsglipor syns i de levererade huvudvyerna, men överlappande kläd-/hårytor innebär att detta inte är bevis på alla möjliga vinklar eller framtida rörelser.

**Spelkamera och ljus:** native 1280×720, avstånd 16 m, pitch 50°, vertikal FOV 40°, fokus 1 m. Helhetsfärger och caféförkläde går att läsa; fräknar och ögonfinish kan inte bedömas på det avståndet. Dagsljus och ambient skugga är Blender-proxyer med Juniper-solens riktning/färg/intensitet och enkelt neutralt cafébakgrundsstöd. De är inte Unity-skärmbilder, en fotometrisk matchning eller en exakt rekonstruktion av caféterrassen. Närmare materialvyer är uttryckligen märkta separat.

## Leverans och avgränsning

29 689 trianglar, **8 exporterade meshgrupper / 8 material**, fyra bilder: en 2048² hudatlas och tre 1024² kartor. A03 har 29 367 trianglar och nio material: Ava använder cirka 1,1 % fler trianglar men färre material. Höjd cirka 1,70 m inklusive hår. Redigerbar högre upplösning finns separat före statisk reduktion. GLB, redigerbara `.blend`, alla fulla renderingar, källskript, hashmanifest, attribution och ändringslista finns i granskningspaketet; små bildark finns i `evidence/ava-rain/previews/`.

Faktiskt körda kontroller är begränsade till källhashar, ingen levererad rigg/animation/inbäddad kod, befintlig oberoende GLB-kontroll av geometri/normaler/skala, återimportbilder och separat reproduktion av exporten. [Källlicens och attribution](RAIN_SOURCE_LICENSE.md), [kommandon](RAIN_REPRODUCE.md), [mätvärden](../../../evidence/ava-rain/metrics.json). Ingen stor ny testplattform, Unity-integration, riggning, animationsproduktion, ändring av A03 eller spelrepo, merge eller produktionsgodkännande.

**Stopp här:** ägaren bedömer särskilt ansiktets vuxenhet/stilmatchning och om axlar/överdel når önskad A03-nivå. Tekniska kontroller är inte ett visuellt GO.
