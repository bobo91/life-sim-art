# Ava Morgan — rejected Phase A visual candidate

**NO-GO: owner rejected this candidate on 2026-10-30.** The rejection covers
shoulder anatomy, torso proportions and foundational face shape, as well as
hair/eyes. Passing geometry checks did not establish adequate visual quality.
No further minor adjustments of this Python-generated model are authorized.
PR #42 remains draft; preserve its source and images as rejected evidence.
See the [new method decision report](ART041_METHOD_DECISION.md).

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
| Same visual language | **Rejected.** Soft shading and related colours did not compensate for inadequate shoulder anatomy, torso proportions and face structure. The candidate does not reach A03's form quality. |
| Face | **Rejected foundational form**, beyond eye/lip surface detail: the uniform oval lower face lacks the integrated orbit, cheek, muzzle and jaw structure seen in A03. Static mesh integrity is not an artistic pass. |
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

**Owner decision: rejected.** The next task is method/base research only.
Do not patch this candidate or begin a replacement model before the owner
approves a new base and method. No rigging, animation, merge, game changes or
A03 delivery changes.
