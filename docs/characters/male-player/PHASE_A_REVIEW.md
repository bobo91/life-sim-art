> Historical pre-approval study. Superseded for Snow source access, inspection and prototype status by [MALE-NEUTRAL-A01 report](POC_REPORT.md). The NO-GO below concerned the original policy gate; it is not the final experiment verdict. Subsequent source access returned HTTP 200 and the owner approved the limited exception.

# Manlig spelarkaraktÃ¤r: Fas A

2026-10-28. **NO-GO fÃ¶r modellproduktion med nuvarande tillÃ¥tna kÃ¤llor och regler.**
Rekommendationen Ã¤r en konstnÃ¤rligt formgiven neutral med automatiserad
rendering, kontroll och export. **Snow v4 Ã¤r fÃ¶rsta kandidat fÃ¶r ett avgrÃ¤nsat
kÃ¤llprov efter uttryckligt godkÃ¤nnande**, inte en visuellt godkÃ¤nd Willow Creek-modell.
Ingen ny karaktÃ¤r, meshimport, rendering eller export har skapats i denna studie.

## VarfÃ¶r jag stoppar fÃ¶re ett nytt modellfÃ¶rsÃ¶k

[AGENTS.md](../../../AGENTS.md) fÃ¶rbjuder uttryckligen:

> No purchased packs, prebuilt meshes, or manual modeling.

Det nya uppdraget tillÃ¥ter jÃ¤mfÃ¶relsen, men sÃ¤ger ocksÃ¥ att licensbelagt material
inte fÃ¥r importeras utan godkÃ¤nnande. En kostnadsfri CC-BY-modell Ã¤r fortfarande
fÃ¶rbyggd och upphovsrÃ¤ttsligt skyddad. Tidigare huvudspecifika undantag och den
pausade Ava-PR33 ger inte tillstÃ¥nd fÃ¶r en ny manlig helkroppsbas.

Originalgeometri genom Python Ã¤r tillÃ¥ten. DÃ¤remot finns ingen verifierad egen
helkroppsbas eller tidigare metod som visat Ã¶nskad ansikts-, hÃ¥r- och kroppskvalitet.
Jag rekommenderar inte Ã¤nnu ett sÃ¥dant fÃ¶rsÃ¶k som den mest lovande vÃ¤gen.
Detta Ã¤r en bedÃ¶mning av tillgÃ¤ngligt underlag, inte ett bevis att en bra helt
procedurbyggd karaktÃ¤r Ã¤r omÃ¶jlig. Jag har inte utfÃ¶rt ett nytt fÃ¶rsÃ¶k som kan
bedÃ¶mas visuellt och presenterar dÃ¤rfÃ¶r ingen teknisk mannequin som leverans.

## Tidigare arbete och faktiska bilder

Jag granskade dokumentationen och dessa befintliga Blender-renderingar:

- [MPFB v0.2: avvisad jÃ¤mfÃ¶relse](../../../evidence/male-neutral-a01/history/mpfb-v02-rejected.png).
- [Studio-huvudet: tidigare front och trekvart](../../../evidence/male-neutral-a01/history/studio-head-rejected.png).
- [Tidigare visuell NO-GO och formfel](../../../evidence/male-neutral-a01/history/README.md).

**Bilderna Ã¤r historiskt underlag, inte en ny manlig prototyp.** MPFB-bilderna
visar insjunkna/mÃ¶rka Ã¶gon, hoptryckt kÃ¤ke och hjÃ¤lmliknande hÃ¥r. Studio-fÃ¶rsÃ¶ket
har sammanhÃ¤ngande former men fÃ¶renklat hÃ¥r och den ursprungliga ansiktsfamiljen.
Att det inte blev Ava bevisar inte att topologin Ã¤r oanvÃ¤ndbar fÃ¶r alla mÃ¤n;
det ger heller inget belÃ¤gg fÃ¶r en attraktiv, klÃ¤dd helkroppskaraktÃ¤r.

Ã…teranvÃ¤nd: kÃ¤llkopior, driverisolering, kameror, kontaktkontroller,
spara/Ã¥terÃ¶ppna, GLB-rundresa och hashmanifest. Ã…teruppta inte morph-sÃ¶kning,
landmÃ¤rkesoptimering eller nya stora parameterbanker. Tidigare 64 024 trianglar
avsÃ¥g ett huvud med tillbehÃ¶r, inte en optimerad hel karaktÃ¤r.

## Tre realistiska vÃ¤gar

| VÃ¤g | Kvalitet och konstnÃ¤rligt arbete | Automation och Unity | Kostnad/rÃ¤ttigheter | Beslut nu |
| --- | --- | --- | --- | --- |
| Egen geometri frÃ¥n grunden med Blender/Python | Full kontroll, men ansikte, lock, hÃ¥r, hÃ¤nder, klÃ¤der och sammanhÃ¤ngande proportioner mÃ¥ste fortfarande formges. VÃ¥ra fÃ¶rsÃ¶k har inte visat efterfrÃ¥gad kvalitet. | Script, material, kameror och statisk export kan Ã¥teranvÃ¤ndas. Bra form och deformering fÃ¶ljer inte automatiskt. | Blender 0 kr; stor, ej uppmÃ¤tt arbetsinsats. Inga nya externa mesh behÃ¶vs. | **NO-GO som rekommenderat nytt huvudspÃ¥r.** TillÃ¥tet men kvalitetsvinsten Ã¤r obevisad. |
| Formgiven Ã¶ppen bas: **Blender Studio Snow v4** | FÃ¤rdig artistformgiven manlig kÃ¤lla med ansikte, hÃ¥r och klÃ¤der. Mest lovande kÃ¤llkandidat, men fullupplÃ¶st preview och faktisk mesh kunde inte granskas hÃ¤r. Ny egen identitet krÃ¤ver medveten formgivning; omfÃ¤rgning rÃ¤cker inte. | Blender-kÃ¤lla med rigg-/ansiktsfunktioner annonseras. Lokal lÃ¤sning, statisk konvertering, material och export Ã¥terstÃ¥r att prova. Blender-riggen Ã¤r inte en verifierad Unity Humanoid-rigg. | Publicerad som Free/CC-BY. Ingen inkÃ¶psavgift annonseras. Attribution och komponentaudit krÃ¤vs; vÃ¥rt policyundantag saknas. | **Villkorat GO fÃ¶r ett enda kÃ¤llprov efter godkÃ¤nnande.** Inget visuellt eller tekniskt modell-GO Ã¤nnu. |
| ModulÃ¤rt paket: **BoZo Base Pack**; Synty som jÃ¤mfÃ¶relse | FÃ¤rdiga variationer sparar moduleringsarbete om paketets stil accepteras. Ansiktskvalitet i nÃ¤rbild Ã¤r inte verifierad. BoZo erbjuder publicerade ansikts-/kroppsval; Synty har ett mer kantigt eget formsprÃ¥k. | BoZo annonserar Humanoid och URP. Ingen verifierad `.blend`-kÃ¤lla/Python-vÃ¤g eller Unity 6000.5-rundresa. Synty har dokumenterade bakningsverktyg men avrÃ¥der frÃ¥n egna moduldelar. | BoZo visar **40 USD fÃ¶re skatt**; Synty **199,99 USD** i direktbutiken. Licens-/AI-frÃ¥gor och privat kÃ¤llhantering tillkommer. Inget kÃ¶p godkÃ¤nt. | **NO-GO fÃ¶r anvÃ¤ndning nu.** Ingen bevisad kvalitetsgenvÃ¤g eller klarerad Codex-loop. |

Produktuppgifter Ã¤r leverantÃ¶rsuppgifter, inte egna modellprov. Priser Ã¤r
visade priser 2026-10-28; SEK, skatt, platser och checkouttotal Ã¤r inte faststÃ¤llda.

## Exakt fÃ¶rsta kÃ¤llkandidat och licensgrÃ¤ns

[Snow v4](https://studio.blender.org/characters/snow/v4/) Ã¤r publicerad som
Free, Blender 4.1 och CC-BY, uppdaterad 2025-05-08. Utgivaren anger stÃ¶d fÃ¶r
4.1 och senare samt medfÃ¶ljande Python fÃ¶r riggens grÃ¤nssnitt. Det Ã¤r ett
kompatibilitetspÃ¥stÃ¥ende, inte ett lokalt prov i vÃ¥r 4.5.14-installation.
Ingen autoexekvering av medfÃ¶ljande script ska tillÃ¥tas vid fÃ¶rsta kÃ¤llinspektionen.

[Studios innehÃ¥llsvillkor](https://studio.blender.org/terms-and-conditions/)
anger CC BY 4.0 om inte annat sÃ¤gs.
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) tillÃ¥ter kommersiella
bearbetningar och distribution med korrekt kreditering, licenslÃ¤nk och
Ã¤ndringsinformation. Snow-sidan begÃ¤r krediten:
`Snow Rig (CC) Blender Foundation | studio.blender.org`.
Ingen separat NoAI-begrÃ¤nsning hittades i granskade offentliga villkor;
inbÃ¤ddade komponenter och programkod Ã¤r Ã¤nnu inte granskade. Logotyper omfattas
inte av Studios allmÃ¤nna innehÃ¥llslicens.

DirektÃ¥tkomst till Studio-sidan och previewbilden gav HTTP 402 i webbverktyget.
OvanstÃ¥ende uppgifter kommer frÃ¥n officiellt indexerat sidinnehÃ¥ll. Ingen
nedladdningsfunktion, kontokrav, rÃ¥fil, hÃ¶gupplÃ¶st bild, topologi eller bildkvalitet
har dÃ¤rfÃ¶r verifierats. HTTP-felet bevisar inte att den Free-mÃ¤rkta modellen kostar
pengar. [Officiell bildlÃ¤nk](https://studio.blender.org/files/public/thumbnail/ba/0f/ba0fe6d810333b1d73c1c359e4dc03cb-6.png)
Ã¤r endast en kÃ¤llhÃ¤nvisning, inte vÃ¥r rendering.

Vincent v1 Ã¤r en Ã¤ldre CC-BY-reserv med Blender 2.80/BlenRig och stÃ¶rre
kompatibilitetsrisk. Einar vÃ¤ljs bort: utgivaren beskriver den som realistisk,
och robotarm/Ã¤ldre identitet passar sÃ¤mre. Inga parallella modellprov fÃ¶reslÃ¥s.

BoZo anvÃ¤nder [Unity Asset Store-villkoren](https://unity.com/legal/as-terms),
vars Â§3.8(v) Ã¤ven berÃ¶r AI-indata. Anta inte att Codex-inspektion Ã¤r tillÃ¥ten bara
fÃ¶r att modelltrÃ¤ning undviks. Kommersiell speldistribution Ã¤r inte rÃ¤tt till
offentlig fristÃ¥ende GLB-/kÃ¤llspridning. Art-repot Ã¤r offentligt. Syntys
[direktlicens](https://syntystore.com/pages/one-time-purchase-licence) har ocksÃ¥
begrÃ¤nsningar fÃ¶r AI och kÃ¤lldelning. Ingen leverantÃ¶r har kontaktats.

## Rekommenderat arbetsflÃ¶de efter ett avgrÃ¤nsat tillstÃ¥nd

**En formgiven neutral fÃ¶rst; automatisera reproduktion och variation efter
visuellt godkÃ¤nnande.** Codex kan hantera kÃ¤llhashar, kopior, konfiguration,
modulval, fÃ¤rgrecept, standardkameror, exporter och kontroller. NÃ¥gon mÃ¥ste
fortfarande bedÃ¶ma och forma Ã¶gonlock, kÃ¤ke, nÃ¤sa, lÃ¤ppar, hÃ¥rfÃ¤ste, klÃ¤dfall och
anatomiska Ã¶vergÃ¥ngar. Ingen trovÃ¤rdig automatiseringsprocent eller tid per
framtida ansikte Ã¤r uppmÃ¤tt.

FÃ¶reslaget prov: **MALE-NEUTRAL-A01**, hÃ¶gst sex aktiva arbetstimmar:

1. HÃ¶gst en timmes kÃ¤llgrind: original/hash/licenser, delar, beroenden, verklig
   budget och ofÃ¶rÃ¤ndrad vyserie. Stoppa om omfattande retopologi, oklara rÃ¤ttigheter
   eller reparation behÃ¶vs. FÃ¶rhandsgranska originalets faktiska uttryck innan formpass.
2. HÃ¶gst tre timmars enda konstnÃ¤rliga form-/lookpass och en riktad korrigering:
   egen ung vuxen identitet, sammanhÃ¤ngande hÃ¥r och en enkel modern outfit.
   Arbeta i kopia; inget generellt reglagebibliotek eller ny rigg.
3. HÃ¶gst tvÃ¥ timmar fÃ¶r front, profil, bakifrÃ¥n, trekvart, ansiktsnÃ¤rbild och
   spelvy, plus geometri, Ã¥terÃ¶ppning, GLB-rundresa och rapport.

Detta Ã¤r ett fÃ¶reslaget stopptak, inte genomfÃ¶rt arbete eller ett lÃ¶fte om en
fÃ¤rdig karaktÃ¤r pÃ¥ sex timmar. Det krÃ¤ver fÃ¶rst
[det namngivna policyundantaget](POLICY_EXCEPTION_PROPOSAL.md).
Egen identitet och helhet bedÃ¶ms visuellt fÃ¶re finlir. Om kvaliteten inte rÃ¤cker
stoppas samma bas; fÃ¶rsÃ¶kstaket fÃ¶rlÃ¤ngs inte. Fas B krÃ¤ver dÃ¤refter eget godkÃ¤nnande.

LÃ¥ngsiktigt: separata godkÃ¤nda proportionfamiljer fÃ¶r vuxna mÃ¤n/kvinnor och
Ã¥ldersvariation, delad teknisk riggspecifikation dÃ¤r den fungerar och kuraterade
hÃ¥r-/klÃ¤dmoduler. En skalad vuxen Ã¤r inte automatiskt ett bra barn. Shape keys
och vikter mÃ¥ste fÃ¶rfattas och visuellt provas; de finns inte fÃ¶r vÃ¥ra framtida
NPC bara fÃ¶r att kÃ¤llriggen har ansiktskontroller. Idle/gÃ¥ng/interaktion,
deform-skelett och Unity Avatar-prov hÃ¶r till Fas B.

## Faktiskt utfÃ¶rt och vad som saknas

Aktuella [system- och Blenderprober](../../../evidence/male-player-phase-a/README.md)
kÃ¶rdes med befintligt script. Blender **4.5.14 LTS / Python 3.11.15** startade
offline i bakgrunden. System-Python Ã¤r 3.14.6. Cirka 32 GB RAM och Radeon RX
9070 XT, cirka 16 GB VRAM, rapporteras. HIP-enheter listas; detta Ã¤r inte ett
GPU-render- eller inferensprov. CUDA/OptiX Ã¤r tomma och Torch saknas i de tvÃ¥
kontrollerade interpreterarna. Live-Blender-tillÃ¤gget kunde inte ansluta;
den faktiskt fungerande vÃ¤gen Ã¤r kommandoraden. Ingen programvara installerades.

FÃ¶r den nya manliga modellen Ã¤r **mÃ¥tt, polygonantal, Ã¶gon-/hÃ¥rkontakt,
normals, material, Ã¥terÃ¶ppning och export ej testade**, eftersom ingen modell
skapats eller importerats. DÃ¤rmed finns heller inga nya front/profil/bakifrÃ¥n/
trekvarts-/ansikts-/spelavstÃ¥ndsbilder att godkÃ¤nna. Historiska bilder ovan ska
inte rÃ¤knas som leverans av den nya karaktÃ¤ren.

[Importkontraktet](IMPORT_CONTRACT_PROPOSAL.json) Ã¤r ett tydligt mÃ¤rkt fÃ¶rslag:
1,75 m referens, fotcentrerad pivot, meter och GLB + `.blend`. Den befintliga
artkamerans proxy Ã¤r 16 m, 50 graders elevation och 40 graders vertikal FOV;
en kompletterande nÃ¤rbild behÃ¶vs fÃ¶r tredje person. Detta Ã¤r inte en verifierad
aktuell Unity-kamera. Ã„ldre 16k-triangelmÃ¥l fÃ¶r hel vuxen Ã¤r ocksÃ¥ bara ett
fÃ¶rslag; Snow-meshens verkliga kostnad Ã¤r okÃ¤nd. Ingen ny budget har godkÃ¤nts.

**Beslut nu:** NO-GO fÃ¶r att kalla en ny karaktÃ¤r eller produktionspipeline
levererad. Rekommenderat nÃ¤sta beslut Ã¤r tillstÃ¥nd fÃ¶r Snow v4 och endast
MALE-NEUTRAL-A01, utan kÃ¶p eller Fas B. AGENTS.md, Ava/PR33 och game-repot Ã¤r
orÃ¶rda av detta uppdrag. Ingen prototyp-PR eller asset-release Ã¤r skapad nÃ¤r
ingen fungerande modell finns att granska.

KÃ¤llregister och exakta kontrollgrÃ¤nser finns i
[sources.json](../../../evidence/male-player-phase-a/sources.json).
