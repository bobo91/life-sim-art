# ART-041 — metodbeslut efter Ava B-huvudets NO-GO

2026-10-31. **Första Ava B-huvudprototypen är slutligt visuellt underkänd.** B-designarket förblir godkänt/låst, A03 oförändrad. Ingen fortsättning på den underkända meshens formfält. Nedan är en bedömd kvalitetsrangordning, inte resultat från nya modellprov. Inga produkter har köpts, installerats eller provmodellerats; ingen artist är kontaktad.

**Rekommendation: användarens metod 3 — ett tidsbegränsat pass av en mänsklig karaktärsartist på en orörd Rain-kopia.** Den står högst i kvalitetsrangordningen nedan. Rain är redan professionellt modellerad. Det senaste försöket visar att bra bastopologi och exportautomation inte räcker för att överföra B:s sammanhängande ansiktsformer och hår.

## 1. Artistlett skulpteringspass — högst bedömd chans till B-trohet

**Tillgång/program:** befintligt Rain-original + Blender 4.5.14, låst B-ark och A03. **Agenter:** kan sköta referensuppställning, källskydd, checkpoints, identiska renderkameror, export/proveniens och avvikelsegranskning. Vårt nuvarande agentflöde har inte visat tillräcklig konstnärlig precision för att ensamt ersätta artisten.

**Konstnärligt arbete:** mänsklig karaktärsartist ansvarar för ögonhålor/lock, kind–näsa–mun–haka som en helhet, profilövergångar och verkligt svepta hårvolymer/knut. Utgångspunkt är original-Rain, inte det underkända huvudet. **Kostnad/licens:** ingen ny program-/baslicens behövs. Provramsbudget **4–8 h × EUR 70–100 = EUR 280–800**, exklusive moms; detta är vår budgetuppskattning, ingen offert. Rain-attribution/ändringsnotis enligt [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) behålls. Artistavtalet behöver uttryckligen omfatta redigerbar källleverans, rätt att publicera bearbetningen och agentstödd hantering av arbetet; inga nya stockdelar utan klarerade rättigheter.

**Litet framtida prov:** högst en arbetsdag, neutralt huvud i lera + primära hårformer, front/profil/trekvart mot låst B och A03. Ägaren bedömer identitet, vaket neutralt ögonparti, profilens näsa–läpp–haka och hårets svep innan mer arbete beställs. Ingen kroppsklädsel, rigg eller animation. **Pipeline:** versionerad `.blend` är formkällan; agenter reproducerar render/export från den. Konstnärliga handgrepp utlovas inte som en procedurgenerator.

## 2. Annat professionellt kvinnligt basmesh — medel med artist, låg evidens för agent-only

**Tillgång/program:** [wysp / Valentin Fischer, Stylized Female Basemesh](https://valentinfischer.artstation.com/store/dB9BJ/stylized-female-basemesh) + Blender. Säljaren anger tre kroppstyper, låg-/högupplöst OBJ utan hår och ZTL. OBJ-vägen kräver inte ZBrush. Den mer heroiska Fortnite/Overwatch-inriktningen behöver mjukas mot A03.

**Agenter:** OBJ-import, struktur/UV-granskning och teknisk export är genomförbara med befintlig Blender-automation. **Konstnärligt arbete:** ansiktsomformning, nackanslutning/stilmatchning och hela B-frisyren kvarstår. Byte av bas med samma numeriska formmetod ger inget visat kvalitetslyft. **Kostnad/licens:** listat **USD 8 Standard / USD 60 Extended**, artisttid tillkommer. Standard har försäljnings-/visningsgränser; Extended undanröjer dessa men medger inte automatiskt offentlig råfilsdistribution. Vårt repo är publikt. [Stock-EULA](https://www.artstation.com/marketplace-product-eula) och tillgångens [NoAI-villkor](https://www.artstation.com/tos) måste klareras för redigerbara GitHub-filer och agentindata innan köp/användning. Ingen sådan klarering finns nu.

**Litet framtida prov:** efter licensklarering, importera endast huvudet och avsätt 2–4 h för ett avgränsat B-formpass/hårblock; stoppa om den nya startformen inte tydligt förbättrar trevyslikheten. **Pipeline:** OBJ → Blender → core-PBR GLB. Topologi/UV, halsfog och slutbudget behöver faktisk kontroll; produktens förhandsbild bevisar inte Unity-kompatibilitet.

## 3. Specialiserat verktyg — Reallusion Character Creator 5

**Tillgång/program:** [CC5 Standard cirka USD 299 / Deluxe cirka USD 479](https://www.reallusion.com/character-creator/), Blender; hårinnehåll kan kosta extra. Använd ansiktsreglage mot den låsta designen. Anatomiskt kopplade morphs ger mer kontrollerad start än egna formfält, men stiliserad B-likhet är obevisad. **Agenter:** delvis; CC5 har [Python-meny](https://manual.reallusion.com/Character-Creator-5/Content/ENU/5.0/03-Main-Menu/Menu-Script.htm), men vår CC-koppling, morph-/hårstyrning och GUI-automation är inte verifierade. Blender-steget finns redan. **Konstnärligt arbete:** val/tolkning av morphs, ögon-/munbalans, förenkling av hud samt B:s särskilda snedbena/låga knut.

**Licensrisk: hög för vår leveransform.** [Content-EULA](https://www.reallusion.com/Content/EULA/EULA.htm), särskilt 2.1 och 6.3, skiljer spelanvändning från råfilsdelning och har uttryckliga AI-relaterade begränsningar. Agentbearbetning, publik `.blend`/GLB och eventuella framtida anpassningsfunktioner behöver leverantörens skriftliga klarering; Enterprise-kostnad är inte känd. Standard spel-export är inget klartecken för vårt publika källpaket.

**Litet framtida prov:** [30-dagarstrial med 30 exporter](https://www.reallusion.com/character-creator/download.html), först lokal mänsklig bedömning av huvud/profil och hårkontroll inom en halvdag. Trialen medger inte kommersiell användning; agentpilot/publik leverans väntar på licensklarering. **Pipeline:** statisk OBJ/FBX → Blender → GLB; proprietära Digital Human-material och groom/hår måste förenklas/bakas till core PBR. Verktygets färdiga rigg är inte bevis på rätt NPC-kontrakt.

## Gemensam kontraktsväg och stopp

Behåll **30 000 trianglar totalt inklusive hår/kropp/kläder**, meter, axelkonvertering, core glTF PBR, stabila namn/ID:n, versionerad källa och SHA256. Nuvarande [NPC-kontrakt på game/main](https://github.com/bobo91/life-sim-game/blob/main/docs/contracts/NPC_CHARACTER_CONTRACT.md), blob `51ceea9f5499125a3682d45edcc6394d0cac7ebe`, är fortfarande **draft**: GLB/glTFast, **Generic Animator, ingen Humanoid-avatar**. Dess övriga föreslagna budgetar (12 skinnade meshgrupper, 10 material, 8 bilder ≤2048) ska följas upp innan produktionsleverans; de är inga godkännanden av rigg eller import. Senare rigg/bennamn/klipp, GUID och faktisk URP-/Unity-kontroll kräver separat GO och game-ägaren Claude. Codex levererar art-källa/export/kontrakt. Ingen integration sker i denna utvärdering.

**Beslutsförslag:** godkänn endast ett artistlett kvalitetstest med fast tids-/kostnadstak som nästa steg. Fram till ett sådant beslut är modellproduktionen pausad. Ingen ny modell, riggning, animation, Unity-integration, merge eller ändring i life-sim-game/A03. PR #42 förblir draft. Den underkända prototypens bilder och ZIP bevaras oförändrade som historik.
