# Isolated props Unity import evidence

2026-10-25. **Partially verified; the overall diagnostic failed due to empty
material pipeline tags. No complete Unity/URP compatibility pass is claimed.**
Only the exact two reviewed run-004 GLBs were used. No game project/code,
original mesh, character, other prop, gameplay integration or contract was
changed. No screenshot or realtime material render was produced.

## What ran

1. [Attempt 001](attempt-001.json): one restricted-process Unity6000.5.8f1
   launch exited **198 after 1.804s**, before package resolution, compilation
   or import. That process could not obtain an Editor/headless entitlement;
   this did not establish that the installed Editor lacked a valid license.
2. [Attempt 002](attempt-002.json): one authorized normal-host batch launch,
   using the existing entitlement without activation or credential changes,
   resolved packages, compiled the checker and imported both GLBs. It exited
   **1 after 69.474s** on the material-tag assertion described below. No third
   attempt was made.

Before the second launch, staging order was corrected: GLBs remain outside
Assets while Unity starts. The checker configures URP/Linear first, then
copies and imports the two files. This avoids choosing a cached Built-in
material generator before URP is selected. Original GLB bytes are unchanged.

## Actual second-attempt results

Unity **6000.5.8f1**, official **glTFast6.20.0**, **URP17.5.0** and Null graphics
device. The actual lock selected **Collections6.5.0 builtin** and
**Burst1.8.30 registry**, rather than glTFast's minimum Collections2.6.8.
The [summary](attempt-002.json) records every resolved version and lock hash.

| Asset | Dimensions X/Y/Z (m) | Triangles | Meshes / material slots |
|---|---|---:|---:|
| prop_mailbox_001 | .36 / 1.43 / .62 | 2,324 | 1 / 4 |
| prop_cafe_table_001 | .78 / .74 / .78 | 856 | 1 / 4 |

- Both files actually imported through GLTFast.Editor.GltfImporter.
- Expected dimensions, bottom-center pivot, unit root scale, triangle counts,
  valid indices and finite positions/normals passed. The mailbox's positive-Z
  front landmark matched with zero nearest-vertex error. The symmetric table
  has no semantic-front landmark.
- All eight material names and imported base-color/metallic/roughness values
  matched the GLB expectations. Each uses
  Shader Graphs/glTF-pbrMetallicRoughness, reports supported, and has no
  reported shader error. glTFast's color-factor gamma conversion is included
  in the expectation; this verifies material data, not a rendered match.
- Original, staged and imported GLB copies retain the same reviewed SHA256
  values. The exact unmodified Unity result is
  [unity-import-report-002.json](unity-import-report-002.json), SHA256
  `93f5d29e54cf5ba8056fcfb3088c80fcc9c9f2ccf2b565fe86684b97194f494c`.

## Why the checker failed and what remains unknown

Every Material.GetTag("RenderPipeline", false) result was empty, so the
checker's strict comparison with UniversalPipeline failed all eight
materials. The installed official shadergraph declares both UniversalTarget
and HDTarget. An empty selected-subshader tag under Null graphics is
insufficient to establish that the imported shader is invalid for URP.

The checker reached scene save/open without an exception and then repeated
the same failing material assertion. Its combined scene acceptance flag is
therefore **false**. The exact report retains that failure; no complete
save/reopen pass is inferred or rewritten.

The two box colliders are **proposed test-scene envelopes only**. They do not
establish agreed gameplay collisions, walking clearance, interaction reach or
an accepted game prefab. Actual realtime URP appearance, game import policy,
collisions and the flag-independent mailbox prompt still require Claude's
verification/agreement in game issue #53. There is no automatic merge.

## Tested source and reproduction template

- [Checker](../../scripts/PropsStaticGlbImportCheck.cs), compiled during
  attempt002: SHA256
  `a8346acf5d8c07fe5ea25baf70dfa8940612041887f25ee03e295c4530664744`.
- [Host runner](../../scripts/run_props_static_glb_import.py): SHA256
  `aa0ac28bca8855b63fe41a3214d08a8738404a008cb8e3c85ba41e8408abda1e`.

Replace the Editor path placeholder with the installed executable. The host
runner uses a Windows process-conflict check, requires a new workspace project
directory and refuses an existing Unity process. Omitting --run prepares only.
The template does not authorize an additional test iteration:

```powershell
python scripts/run_props_static_glb_import.py --editor "<path-to-Unity-6000.5.8f1>" --input build/first-playable-props/run-004 --project build/first-playable-props-unity/probe-new --run
```

Project, input copies, test scene, log and report paths are under art build/.
Normal Unity package/licensing caches may also be used. Raw logs/command files
remain local because they contain private host/licensing metadata. The exact
public result JSON was scanned before copying and contains none of those fields.

## Importer source and license

Official com.unity.cloud.gltfast6.20.0 requires Unity6000.0 or newer and
documents URP support and Editor GLB import. The exact package tarball was
checked against the registry SHA1 and its Apache-2.0 license inspected before
the probe. Unity Editor and dependency terms remain separate.

Sources: [registry](https://packages.unity.com/com.unity.cloud.gltfast),
[official overview](https://docs.unity3d.com/Packages/com.unity.cloud.gltfast@6.20/manual/index.html),
[Editor import](https://docs.unity3d.com/Packages/com.unity.cloud.gltfast@6.20/manual/ImportEditor.html),
[package license](https://github.com/Unity-Technologies/com.unity.cloud.gltfast/blob/main/Packages/com.unity.cloud.gltfast/LICENSE.md).

6.20.0 tarball SHA256:
`bc51a487caf6c75c93c69bfc272a7cd13a0e9f5b8738594b7661d45e3fc1e136`.
Its LICENSE.md SHA256:
`cccf2d7a6c705ec991d5229a775e7fbd41fa6de57d4e3f33bbecb967c3055ef9`.
