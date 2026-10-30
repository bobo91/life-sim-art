# Ava Morgan — Phase A visual candidate

**Owner appearance review required. Further production is NO-GO until that
review.** This is a static candidate, not an approved NPC or a rigging delivery.

Ava has a warm freckled face, brown eyes, a brunette high bun with framing
strands, ivory rolled-sleeve sweater, olive apron/leather straps, dark cuffed
jeans and offwhite shoes. Her face, body and clothes are independently generated
original geometry. A03 is used only as unchanged comparison evidence.

| Evidence | Actual Blender image |
|---|---|
| Full body front / side / back | [Turnaround](../../../evidence/ava041/previews/turnaround.png) |
| Face | [Front](../../../evidence/ava041/previews/face_front.png), [three-quarter](../../../evidence/ava041/previews/face_three_quarter.png) |
| Same scale as approved A03 | [Ava + A03](../../../evidence/ava041/previews/ava_a03_same_scale.png) |
| Normal game distance / angle | [Native 16 m pair](../../../evidence/ava041/previews/game-camera-pair.png) |
| Juniper outdoor daylight proxy | [Full](../../../evidence/ava041/previews/cafe_daylight_full.png), [face](../../../evidence/ava041/previews/cafe_daylight_face.png) |
| Additional form review | [Three-quarter](../../../evidence/ava041/previews/three_quarter.png), [isometric](../../../evidence/ava041/previews/isometric.png) |

All model evidence is rendered by Blender. Layout adds labels/credit and reduces
some display sizes; it does not retouch geometry, colours or lighting. Native
game frames retain their complete 1280 × 720 pixels. The preview manifest records
source/output hashes and transformations. The artifact retains the full renders.

| Cost | Ava | Approved A03 static |
|---|---:|---:|
| Triangles | 28,991 | 29,367 |
| Editable mesh groups | 9 | 10 |
| Materials | 9 | 9 |
| Image textures | 0 | 13 × 2048² |
| Height including hair | 1.692 m | 1.749405 m |

The GLB has 12 material primitives because the face group uses multiple shared
roles. Counts are asset measurements, not a runtime performance certificate.

| Review area | Critical finding |
|---|---|
| Identity / adult form | Distinct female face, shorter stature, freckled skin, bun and cafe silhouette. Retains the established art wardrobe; no stale cafe branding or invented backstory. |
| Same visual language | Soft shaded forms, restrained civic colours and adult proportions relate to A03. **Facial finish is below A03**, especially the flatter eye surfaces and more graphic lids/lips. Do not approve equivalence solely from the same-scale frame. |
| Face | No obvious exploded or collapsed surface in the static front/profile/three-quarter evidence. Iris, eyelid and lip layers remain visibly constructed at close dialogue distance. Expression is a fixed relaxed neutral; no expression/deformation capability is claimed. |
| Hair | Crown covers the scalp without the earlier skin peeks. Bun and loose framing strands read clearly. Swept clumps still have a sculpted ribbon quality and the back cap is simple; this is an owner-review weakness. |
| Garment contacts | The reviewed final neutral pose removes the visible shoulder gaps, wrist seam, floating belt/strap ends and rear-pocket artifacts found in earlier probes. Garment/body overlaps are intentional. Static checks do not establish moving contact or complete self-intersection freedom. |
| Clothing / surface detail | Apron, rolled sleeves and cuffed jeans carry the cafe role at distance. Knit/denim weave, seam detail and shoe construction are simplified; obscured laces make shoes read as slip-ons. No expensive texture detail is used. |
| Game-distance readability | Bun, ivory shoulders and broad olive apron remain distinguishable. Freckles/iris detail disappears at normal 16 m distance, as expected. Full uncropped frames are provided instead of enlarged crops as the sole evidence. |
| Cafe lighting | Uses the game's documented sun colour/direction and cool ambient in a Blender proxy. The counter is outdoors in the current game. Cycles/AgX energy and appearance are not pixel-equivalent to Unity URP. |
| Technical scope | Static geometry, source reopen, independent binary validation, exact GLB regeneration and Blender reimport are measured separately from appearance. No rig, animation, runtime import, collider, LOD or gameplay test is delivered. |

The first probes exposed hair projection/scalp contacts, shoulder caps, hand
joins, rear pockets and bow/lid normal failures. They were corrected from actual
renders and validator diagnostics. The final source keeps the validator's
original winding/normal thresholds. Probe files are retained locally, not
presented as final evidence.

**Decision requested in the draft PR:** accept this appearance direction or give
specific visual revisions. The critical recommendation is to review face and
hair closely before granting appearance approval. Stop here: no rigging,
animation production, merge, game changes or A03 delivery changes.
