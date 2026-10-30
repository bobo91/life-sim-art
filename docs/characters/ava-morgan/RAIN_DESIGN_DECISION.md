# ART-041 — design före mer mesh

**Rain Ava v0.2 är visuellt NO-GO. Modellproduktionen är pausad.** Rain-basen och den förbättrade hals-/axel-/bröstanatomin behålls. 31 290 trianglar överskrider kontraktets 30 000 med **1 290 / 4,3 %**. Det tidigare lokala granskningsvärdet 32 000 ändrar inte kontraktet; v0.2 är inte en godkänd leverans.

**Förslag till beslut:** beställningsunderlaget för nästa steg ska vara ett godkänt, eget 2D-designark för Ava. Därefter rekommenderas ett sammanhängande artistlett formpass i Blender med agentstöd. Inga fler småjusteringar av v0.2-ansiktet.

## Konkreta referenser och föreslagen riktning

| Referens | Vad den styr |
|---|---|
| [Godkänd A03, i befintlig skalarendering](https://github.com/bobo91/life-sim-art/blob/9c3e7d2576ebdf6a1600ddb4a4e3aaaa717b8206/evidence/ava-rain-v02/previews/ava_a03_same_scale.png) | Graden av stilisering, sammanhängande ansiktsplan, dämpade material och hårdetaljernas skala. A03:s manliga ansiktsform kopieras inte. |
| [Proko: huvudkonstruktion framifrån/profil/trekvart](https://www.proko.com/course-lesson/how-to-draw-the-head-from-any-angle/) | Rita hårfäste–bryn–näsbas–haka och kind-/käkplan sammanhängande i flera vinklar. Ansiktstredjedelar är en konstruktionsstart, inte fasta proportioner för alla personer. |
| [Olga Solo: verklig brunettknut i profil/bakifrån](https://unsplash.com/photos/a-woman-with-her-hair-in-a-low-bun-vwO5lBQPU2I) | Mjuk uppsamling, överlappande hårflöde och en tunn, avsmalnande ansiktsslinga. Fotot har inspekterats. Knutens lägre placering är ett förslag att godkänna, inte en redan fastslagen ändring. |

**Avas föreslagna identitet:** en varm, praktisk 29-årig cafémedarbetare. Något avlångt ansikte med mjukt käkstöd och tydlig haka; lugnare nedre kinder och en måttligt markerad näsrygg. Bruna, naturligt öppna ögon med överlock över övre iris; mjukt avsmalnande bryn och lågmält läpprött utan framskjutet munparti. Diskreta fräknar behålls. Kastanjebrun snedbena, en löst uppsatt knut, ett synligt öra och ett fåtal tunna slingor ger en egen siluett. Gräddvitt/oliv/mörk denim behålls.

Nästa **designsteg**, om ägaren godkänner förslaget: högst två tydligt olika originalskisser inom denna brief. Välj ett ansikte och gör ett sammanhängande ark med front, profil, trekvart, hårsilhuett och ett litet leende. Visa det bredvid A03 i samma presentationsskala. Markera valda landmärken, bryn-/läppform och hårflöde. Ägaren godkänner **personen och stilen före mesh**. Inga sådana skisser eller nya karaktärsbilder har skapats i detta uppdrag. Fotot är en länkad referens under sin egen licens, inte en CC BY-modelltextur eller en persons identitet att kopiera.

## Metod efter separat design- och produktions-GO

Blender Studios [Rain/Snow-arbetsflöde](https://studio.blender.org/training/stylized-character-workflow/) skiljer designutforskning från senare topologi och finish. Min rekommendation är en karaktärartist för originalarket och det avgörande ansikts-/hårformpasset, med Codex som ansvarig för art-leveransen. Ingen artist har kontaktats eller beställts.

Agenter ställer upp godkända [bildreferenser](https://docs.blender.org/manual/en/4.5/modeling/empties.html), skyddar anatomin med [masker](https://docs.blender.org/manual/en/4.5/sculpt_paint/sculpting/editing/mask.html), hanterar checkpoints/render/export och granskar mot arket. En enda skrivande Blender-operatör formar sammanhängande volymer i Edit/Sculpt Mode; en annan granskar bilderna. Efter nytt produktions-GO används en orörd Rain-huvudkopia mot arket, med den bevarade kroppen och fungerande topologi. v0.2-ansiktet förblir jämförelseunderlag. MCP ger explicit `bpy/bmesh`-styrning och bilder, inte en verifierad automatisk karaktärsdesigner eller konstnärlig garanti. Detta är en metodbedömning, inte ett utfört verktygsprov.

Om helt agentbaserad produktion krävs: börja först efter godkänd design med ett avgränsat huvudprov mot dess landmärken. Vid utebliven identitet stannar arbetet för metodbeslut. Det blir inte en ny serie globala Gauss-/reglageändringar. Slutlig mesh ska rymmas inom **30 000 inklusive hår och kläder**; ingen geometri ändras eller optimeras under pausen.

**Stopp här för beslut om designsteget och arbetsformen.** Endast research, dokumentation och status har ändrats. Ingen Blender-körning, ny modell, riggning, animation, merge eller GAME-049/life-sim-game-integration.
