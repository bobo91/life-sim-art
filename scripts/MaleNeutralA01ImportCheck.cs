// Isolated static GLB import proof. No game objects, gameplay or production colliders.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public static class MaleNeutralA01ImportCheck
{
    [Serializable] public class MaterialExpected { public string name; public float[] baseColor; public float metallic, roughness; public bool baseTextureExpected; }
    [Serializable] public class AssetExpected { public string id; public float[] dimensions, frontPoint; public int triangles; public MaterialExpected[] materials; }
    [Serializable] public class Expected { public AssetExpected[] assets; }
    [Serializable] public class MaterialResult { public string name, shader, pipelineTag; public float[] color; public float metallic, roughness; public bool propertiesMatch, shaderHasError, shaderSupported, baseTexturePresent; }
    [Serializable] public class AssetResult
    {
        public string id, importer, status; public float[] dimensions, boundsMin, boundsMax, rootScale;
        public int meshCount, triangles, materialCount; public bool indicesValid, finiteVerticesNormals, dimensionsMatch, bottomCenterPivot, unitScale, frontPositiveZ;
        public float frontNearestVertex; public MaterialResult[] materials; public float[] proposedColliderCenter, proposedColliderSize; public string[] errors; public string[] importerMessages;
    }
    [Serializable] public class Report
    {
        public string schema="male-neutral-a01-isolated-unity-import-1", unityVersion, status, renderPipeline, gltfastVersion, urpVersion, graphicsDevice;
        public bool sceneSavedAndReopened, importedFilesUnchanged, screenshotsRendered=false;
        public AssetResult[] assets; public string[] errors, limitations;
    }
    static string Arg(string name) { var args=Environment.GetCommandLineArgs(); for(int i=0;i+1<args.Length;i++)if(args[i]==name)return args[i+1]; return null; }
    static float[] V(Vector3 v)=>new[]{v.x,v.y,v.z};
    static Vector3 V(float[] v)=>new Vector3(v[0],v[1],v[2]);
    static bool Finite(float v)=>!float.IsNaN(v)&&!float.IsInfinity(v);
    static bool Finite(Vector3 v)=>Finite(v.x)&&Finite(v.y)&&Finite(v.z);
    static bool Close(Vector3 a,Vector3 b,float t=0.001f)=>Vector3.Distance(a,b)<t;
    static bool Close(Color a,Color b,float t=0.003f)=>Mathf.Abs(a.r-b.r)<t&&Mathf.Abs(a.g-b.g)<t&&Mathf.Abs(a.b-b.b)<t&&Mathf.Abs(a.a-b.a)<t;

    static AssetResult Inspect(GameObject root,AssetExpected expected)
    {
        var errors=new List<string>();
        var result=new AssetResult {id=expected.id,indicesValid=true,finiteVerticesNormals=true,frontNearestVertex=-1};
        var filters=root.GetComponentsInChildren<MeshFilter>(true);
        var renderers=root.GetComponentsInChildren<MeshRenderer>(true);
        result.meshCount=filters.Length;
        var points=new List<Vector3>();
        Bounds bounds=new Bounds(); bool first=true;
        foreach(var filter in filters)
        {
            var mesh=filter.sharedMesh;
            if(mesh==null){errors.Add("Missing mesh");continue;}
            var vertices=mesh.vertices; var normals=mesh.normals;
            result.finiteVerticesNormals &= vertices.All(Finite)&&normals.Length==vertices.Length&&normals.All(Finite);
            var indices=mesh.triangles; result.triangles+=indices.Length/3;
            result.indicesValid &= indices.Length%3==0&&indices.All(i=>i>=0&&i<vertices.Length);
            foreach(var p in vertices){var world=filter.transform.TransformPoint(p); points.Add(world);if(first){bounds=new Bounds(world,Vector3.zero);first=false;}else bounds.Encapsulate(world);}
        }
        result.dimensions=V(bounds.size);result.boundsMin=V(bounds.min);result.boundsMax=V(bounds.max);result.rootScale=V(root.transform.localScale);
        result.dimensionsMatch=Close(bounds.size,V(expected.dimensions));
        result.bottomCenterPivot=Mathf.Abs(bounds.min.y)<0.001f&&Mathf.Abs(bounds.center.x)<0.001f&&Mathf.Abs(bounds.center.z)<0.001f&&Close(root.transform.position,Vector3.zero);
        result.unitScale=Close(root.transform.localScale,Vector3.one);
        if(expected.frontPoint!=null&&expected.frontPoint.Length==3)
        {
            Vector3 front=V(expected.frontPoint); front.x=-front.x; // glTFast mirrors X for RH -> Unity LH.
            result.frontNearestVertex=points.Min(p=>Vector3.Distance(p,front));
            result.frontPositiveZ=front.z>0&&result.frontNearestVertex<0.001f;
        }
        else result.frontPositiveZ=true; // symmetric table has no semantic front landmark.
        var materials=renderers.SelectMany(r=>r.sharedMaterials).Distinct().ToArray(); result.materialCount=materials.Length;
        var materialResults=new List<MaterialResult>();
        foreach(var material in materials)
        {
            var mr=new MaterialResult {name=material!=null?material.name:"NULL"};
            var e=expected.materials.FirstOrDefault(m=>material!=null&&m.name==material.name);
            if(material!=null&&material.shader!=null)
            {
                mr.shader=material.shader.name;mr.pipelineTag=material.GetTag("RenderPipeline",false);mr.shaderHasError=ShaderUtil.ShaderHasError(material.shader);mr.shaderSupported=material.shader.isSupported;
                if(e!=null&&material.HasProperty("baseColorFactor")&&material.HasProperty("metallicFactor")&&material.HasProperty("roughnessFactor"))
                {
                    Color c=material.GetVector("baseColorFactor");mr.color=new[]{c.r,c.g,c.b,c.a};mr.metallic=material.GetFloat("metallicFactor");mr.roughness=material.GetFloat("roughnessFactor");
                    var target=new Color(e.baseColor[0],e.baseColor[1],e.baseColor[2],e.baseColor[3]).gamma;
                    mr.baseTexturePresent=material.HasProperty("baseColorTexture")&&material.GetTexture("baseColorTexture")!=null;
                    mr.propertiesMatch=(!e.baseTextureExpected||mr.baseTexturePresent)&&Close(c,target)&&Mathf.Abs(mr.metallic-e.metallic)<0.001f&&Mathf.Abs(mr.roughness-e.roughness)<0.001f;
                }
            }
            if(!mr.propertiesMatch||mr.shaderHasError||mr.pipelineTag!="UniversalPipeline")errors.Add("Material/shader mismatch: "+mr.name);
            materialResults.Add(mr);
        }
        result.materials=materialResults.ToArray();
        result.proposedColliderCenter=new[]{0f,expected.dimensions[1]/2f,0f};result.proposedColliderSize=expected.dimensions;
        if(result.meshCount!=10||result.triangles!=expected.triangles||result.materialCount!=9)errors.Add("Mesh/triangle/material count mismatch");
        if(!result.indicesValid||!result.finiteVerticesNormals||!result.dimensionsMatch||!result.bottomCenterPivot||!result.unitScale||!result.frontPositiveZ)errors.Add("Geometry/scale/pivot/forward mismatch");
        result.errors=errors.ToArray();result.status=errors.Count==0?"passed":"failed";return result;
    }

    static void RenderReview(string output)
    {
        var cam=new GameObject("ArtReviewCamera").AddComponent<Camera>();
        cam.transform.position=new Vector3(-2.8f,1.5f,4.0f);cam.transform.LookAt(new Vector3(0,.875f,0));
        cam.orthographic=true;cam.orthographicSize=1.08f;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.30f,.32f,.34f);cam.nearClipPlane=.05f;cam.farClipPlane=50;
        var light=new GameObject("ArtReviewKey").AddComponent<Light>();light.type=LightType.Directional;light.intensity=2;light.transform.rotation=Quaternion.Euler(40,155,0);
        RenderSettings.ambientMode=AmbientMode.Flat;RenderSettings.ambientLight=new Color(.3f,.3f,.3f);
        var rt=new RenderTexture(768,768,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB);rt.Create();
        var request=new UniversalRenderPipeline.SingleCameraRequest {destination=rt};
        for(int i=0;i<4;i++)RenderPipeline.SubmitRenderRequest(cam,request);
        if(!(RenderPipelineManager.currentPipeline is UniversalRenderPipeline)||!RenderPipeline.SupportsRenderRequest(cam,request))throw new Exception("URP render request unavailable");
        var previous=RenderTexture.active;RenderTexture.active=rt;var image=new Texture2D(768,768,TextureFormat.RGB24,false);
        image.ReadPixels(new Rect(0,0,768,768),0,0);image.Apply();File.WriteAllBytes(Path.Combine(Path.GetDirectoryName(output),"unity-three-quarter.png"),image.EncodeToPNG());
        RenderTexture.active=previous;UnityEngine.Object.DestroyImmediate(image);rt.Release();UnityEngine.Object.DestroyImmediate(rt);
    }

    public static void Run()
    {
        var report=new Report {unityVersion=Application.unityVersion,graphicsDevice=SystemInfo.graphicsDeviceType.ToString(),limitations=new[]{
            "Isolated static character import in art workspace; no game changes or contract acceptance.",
            "One isolated URP/D3D review render; different lighting/tonemapping from Blender, no game-lighting equivalence.",
            "Proposed collider boxes are test-scene envelopes only, not approved game collisions.",
            "No skinning, animation, Humanoid Avatar, LOD, gameplay or game integration test."}};
        string output=Arg("-propsReport");var errors=new List<string>();
        try
        {
            var expected=JsonUtility.FromJson<Expected>(File.ReadAllText(Arg("-propsExpected")));
            var renderer=ScriptableObject.CreateInstance<UniversalRendererData>();AssetDatabase.CreateAsset(renderer,"Assets/ProbeRenderer.asset");
            var pipeline=UniversalRenderPipelineAsset.Create(renderer);AssetDatabase.CreateAsset(pipeline,"Assets/ProbeURP.asset");
            GraphicsSettings.defaultRenderPipeline=pipeline;QualitySettings.renderPipeline=null;PlayerSettings.colorSpace=ColorSpace.Linear;
            AssetDatabase.SaveAssets();
            report.renderPipeline=GraphicsSettings.defaultRenderPipeline.GetType().FullName;
            report.gltfastVersion=UnityEditor.PackageManager.PackageInfo.GetAllRegisteredPackages().First(p=>p.name=="com.unity.cloud.gltfast").version;
            report.urpVersion=UnityEditor.PackageManager.PackageInfo.GetAllRegisteredPackages().First(p=>p.name=="com.unity.render-pipelines.universal").version;
            var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var results=new List<AssetResult>();
            foreach(var e in expected.assets)
            {
                string path="Assets/Props/"+e.id+".glb";
                // Keep GLBs outside Assets during startup: the first material
                // generator must be chosen after URP/Linear are configured.
                string staged=Path.Combine(Directory.GetParent(Application.dataPath).FullName,"Inputs",e.id+".glb");
                File.Copy(staged,path,false);
                AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
                var importer=AssetImporter.GetAtPath(path);
                var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(path);if(prefab==null)throw new Exception("No imported prefab: "+e.id);
                var instance=(GameObject)PrefabUtility.InstantiatePrefab(prefab);instance.name=e.id;
                RenderReview(output);report.screenshotsRendered=true;
                var result=Inspect(instance,e);result.importer=importer.GetType().FullName;
                var field=importer.GetType().GetField("reportItems",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
                var items=field==null?null:field.GetValue(importer) as System.Collections.IEnumerable;
                var messages=new List<string>();if(items!=null)foreach(object item in items){messages.Add(item.ToString());var logItem=item as GLTFast.Logging.LogItem;if(logItem!=null&&(logItem.Type==LogType.Error||logItem.Type==LogType.Exception))errors.Add("glTFast import error: "+item.ToString());}
                result.importerMessages=messages.ToArray();
                // Warnings are retained verbatim; actual importer Error/Exception entries fail above.
                if(!result.importer.Contains("GLTFast"))errors.Add("Unexpected importer "+result.importer);
                results.Add(result);
                var collider=instance.AddComponent<BoxCollider>();collider.center=V(result.proposedColliderCenter);collider.size=V(result.proposedColliderSize);
            }
            report.assets=results.ToArray();
            string scenePath="Assets/StaticMaleProbe.unity";if(!EditorSceneManager.SaveScene(scene,scenePath))throw new Exception("Save scene failed");
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);var reopened=EditorSceneManager.OpenScene(scenePath,OpenSceneMode.Single);
            report.sceneSavedAndReopened=true;
            foreach(var e in expected.assets)
            {
                var root=reopened.GetRootGameObjects().Single(g=>g.name==e.id);var again=Inspect(root,e);var before=report.assets.Single(a=>a.id==e.id);
                var collider=root.GetComponent<BoxCollider>();
                if(again.status!="passed"||!Close(V(again.dimensions),V(before.dimensions))||collider==null||!Close(collider.size,V(e.dimensions)))report.sceneSavedAndReopened=false;
            }
            if(report.assets.Any(a=>a.status!="passed"))errors.Add("One or more imported props failed");
            if(!report.sceneSavedAndReopened)errors.Add("Save/reopen mismatch");
        }
        catch(Exception e){errors.Add(e.ToString());}
        report.errors=errors.ToArray();report.status=errors.Count==0?"passed-static-import-and-reopen":"failed";
        File.WriteAllText(output,JsonUtility.ToJson(report,true)+"\n");Debug.Log("PROPS_STATIC_GLB_PROBE_"+report.status);
        EditorApplication.Exit(errors.Count==0?0:1);
    }
}
