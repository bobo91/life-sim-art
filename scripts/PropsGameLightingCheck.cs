// Graphics-enabled validation of unchanged original props in a pinned game scene copy.
// No PlayMode, bootstrap regeneration, save-service calls or game repository writes.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public static class PropsGameLightingCheck
{
    [Serializable] public class MaterialExpected { public string name; public float[] baseColor; public float metallic, roughness; }
    [Serializable] public class AssetExpected { public string id; public float[] dimensions, frontPoint; public int triangles; public MaterialExpected[] materials; }
    [Serializable] public class Config
    {
        public string sourceGameCommit, sourceArchiveSHA256;
        public string scenePath="Assets/LifeSim/Scenes/Bootstrap.unity";
        public string urpAssetPath="Assets/LifeSim/Settings/LifeSim_URP.asset";
        public float[] tablePosition; public AssetExpected[] assets;
    }
    [Serializable] public class MaterialResult
    {
        public string name, shader, selectedPipelineTag; public string[] declaredPipelineTags;
        public float[] baseColor; public float metallic, roughness;
        public bool propertiesMatch, shaderHasError, shaderSupported, declaresUrp;
    }
    [Serializable] public class ColliderResult
    {
        public string status="candidate-only-not-game-approved", type="BoxCollider";
        public float[] center, size; public bool containsMeshBounds, frontRayHit, topRayHit;
    }
    [Serializable] public class AssetResult
    {
        public string id, importer, placement; public float[] worldPosition, localDimensions, localBoundsMin, localBoundsMax, localScale;
        public int meshes, triangles, materialSlots; public bool validIndices, finiteData, dimensionsMatch, bottomCenterPivot, unitScale, frontLandmarkMatch;
        public float nearestFrontLandmarkError; public MaterialResult[] materials; public ColliderResult collider; public string[] errors;
    }
    [Serializable] public class ViewResult
    {
        public string file, context; public float[] cameraPosition, cameraEuler;
        public float fov; public int width, height, magentaPixels, changedPropPixels, propRoiPixels;
        public bool nonUniformImage, propVisibilityVerified; public float[] propRoi;
    }
    [Serializable] public class LightingResult
    {
        public string skybox, ambientMode, activeUrpAsset;
        public float ambientIntensity, reflectionIntensity, sunIntensity; public float[] sunColor, sunEuler;
        public bool fog, postProcessing, hdr, environmentRefreshRequested;
    }
    [Serializable] public class Report
    {
        public string schema="props-game-lighting-validation-1", status, sourceGameCommit, sourceArchiveSHA256;
        public string unityVersion, graphicsDevice, activePipeline, gltfastVersion, urpVersion;
        public bool graphicsEnabled, urpActiveAfterRendering, declaredUrpShaders, importedSceneSavedAndReopened;
        public bool originalBootstrapBytesUnchanged, originalGlbBytesUnchanged, noGameRepositoryWrites=true;
        public bool gameContractAccepted=false, productionCollidersApproved=false, interactionPromptRuntimeTested=false;
        public bool uiDisabledForAssetReview; public int disabledCanvasCount;
        public LightingResult lighting; public AssetResult[] assets; public ViewResult[] views; public string[] errors, limitations;
    }

    const int Width=1280, Height=720;
    static Camera camera;
    static string output;
    static readonly List<ViewResult> Views=new List<ViewResult>();
    static string Arg(string name) { var a=Environment.GetCommandLineArgs();for(int i=0;i+1<a.Length;i++)if(a[i]==name)return a[i+1];return null; }
    static float[] V(Vector3 v)=>new[]{v.x,v.y,v.z};
    static Vector3 V(float[] v)=>new Vector3(v[0],v[1],v[2]);
    static bool Near(Vector3 a,Vector3 b,float t=.001f)=>Vector3.Distance(a,b)<t;
    static bool Finite(float x)=>!float.IsNaN(x)&&!float.IsInfinity(x);
    static bool Finite(Vector3 v)=>Finite(v.x)&&Finite(v.y)&&Finite(v.z);
    static bool Near(Color a,Color b)=>Mathf.Abs(a.r-b.r)<.003f&&Mathf.Abs(a.g-b.g)<.003f&&Mathf.Abs(a.b-b.b)<.003f&&Mathf.Abs(a.a-b.a)<.003f;
    static bool Pink(Color32 c)=>c.r>200&&c.g<70&&c.b>200;
    static int Difference(Color32 a,Color32 b)=>Mathf.Max(Mathf.Abs(a.r-b.r),Mathf.Abs(a.g-b.g),Mathf.Abs(a.b-b.b));
    static string Package(string name)=>UnityEditor.PackageManager.PackageInfo.GetAllRegisteredPackages().First(p=>p.name==name).version;

    static AssetResult Inspect(GameObject root,AssetExpected expected,string placement)
    {
        var errors=new List<string>();
        var result=new AssetResult {id=expected.id,placement=placement,worldPosition=V(root.transform.position),localScale=V(root.transform.localScale),
            validIndices=true,finiteData=true,nearestFrontLandmarkError=-1};
        var points=new List<Vector3>(); Bounds bounds=new Bounds(); bool first=true;
        var filters=root.GetComponentsInChildren<MeshFilter>(true);result.meshes=filters.Length;
        foreach(var f in filters)
        {
            var mesh=f.sharedMesh;if(mesh==null){errors.Add("Missing mesh");continue;}
            var vertices=mesh.vertices;var normals=mesh.normals;var indices=mesh.triangles;
            result.triangles+=indices.Length/3;
            result.validIndices&=indices.Length%3==0&&indices.All(i=>i>=0&&i<vertices.Length);
            result.finiteData&=vertices.All(Finite)&&normals.Length==vertices.Length&&normals.All(Finite);
            foreach(var v in vertices)
            {
                var p=root.transform.InverseTransformPoint(f.transform.TransformPoint(v));points.Add(p);
                if(first){bounds=new Bounds(p,Vector3.zero);first=false;}else bounds.Encapsulate(p);
            }
        }
        result.localDimensions=V(bounds.size);result.localBoundsMin=V(bounds.min);result.localBoundsMax=V(bounds.max);
        result.dimensionsMatch=Near(bounds.size,V(expected.dimensions));result.unitScale=Near(root.transform.localScale,Vector3.one);
        result.bottomCenterPivot=Mathf.Abs(bounds.min.y)<.001f&&Mathf.Abs(bounds.center.x)<.001f&&Mathf.Abs(bounds.center.z)<.001f;
        if(expected.frontPoint!=null&&expected.frontPoint.Length==3)
        {
            var p=V(expected.frontPoint);p.x=-p.x; // glTFast RH -> Unity LH conversion.
            result.nearestFrontLandmarkError=points.Min(v=>Vector3.Distance(v,p));result.frontLandmarkMatch=p.z>0&&result.nearestFrontLandmarkError<.001f;
        }
        else result.frontLandmarkMatch=true; // no unique semantic front on symmetric table.
        var materials=root.GetComponentsInChildren<MeshRenderer>(true).SelectMany(r=>r.sharedMaterials).Distinct().ToArray();result.materialSlots=materials.Length;
        var mr=new List<MaterialResult>();var tag=new ShaderTagId("RenderPipeline");
        foreach(var m in materials)
        {
            var r=new MaterialResult {name=m==null?"NULL":m.name};var e=expected.materials.FirstOrDefault(v=>m!=null&&v.name==m.name);
            if(m!=null&&m.shader!=null)
            {
                r.shader=m.shader.name;r.selectedPipelineTag=m.GetTag("RenderPipeline",false);
                r.declaredPipelineTags=Enumerable.Range(0,m.shader.subshaderCount).Select(i=>m.shader.FindSubshaderTagValue(i,tag).name).ToArray();
                r.declaresUrp=r.declaredPipelineTags.Contains("UniversalPipeline");r.shaderSupported=m.shader.isSupported;r.shaderHasError=ShaderUtil.ShaderHasError(m.shader);
                if(e!=null&&m.HasProperty("baseColorFactor")&&m.HasProperty("metallicFactor")&&m.HasProperty("roughnessFactor"))
                {
                    Color c=m.GetVector("baseColorFactor");r.baseColor=new[]{c.r,c.g,c.b,c.a};r.metallic=m.GetFloat("metallicFactor");r.roughness=m.GetFloat("roughnessFactor");
                    r.propertiesMatch=Near(c,new Color(e.baseColor[0],e.baseColor[1],e.baseColor[2],e.baseColor[3]).gamma)
                        &&Mathf.Abs(r.metallic-e.metallic)<.001f&&Mathf.Abs(r.roughness-e.roughness)<.001f;
                }
            }
            if(!r.propertiesMatch||!r.declaresUrp||!r.shaderSupported||r.shaderHasError)errors.Add("Material data/declared URP shader failed: "+r.name);
            mr.Add(r);
        }
        result.materials=mr.ToArray();
        if(result.meshes!=1||result.triangles!=expected.triangles||result.materialSlots!=4||!result.validIndices||!result.finiteData||!result.dimensionsMatch||!result.unitScale||!result.bottomCenterPivot||!result.frontLandmarkMatch)
            errors.Add("Geometry, transform or expected topology mismatch");
        var collider=root.GetComponent<BoxCollider>();
        if(collider==null)errors.Add("Candidate collider missing");
        else
        {
            Physics.SyncTransforms();
            var candidate=new ColliderResult {center=V(collider.center),size=V(collider.size)};
            var b=new Bounds(collider.center,collider.size+Vector3.one*.002f);
            candidate.containsMeshBounds=points.All(p=>b.Contains(p));
            Vector3 center=root.transform.TransformPoint(collider.center);
            candidate.frontRayHit=collider.Raycast(new Ray(center+root.transform.forward*2f,-root.transform.forward),out _,4f);
            candidate.topRayHit=collider.Raycast(new Ray(center+Vector3.up*2f,Vector3.down),out _,4f);
            result.collider=candidate;if(!candidate.containsMeshBounds||!candidate.frontRayHit||!candidate.topRayHit)errors.Add("Candidate collider physics check failed");
        }
        result.errors=errors.ToArray();return result;
    }

    static Color32[] RenderPixels()
    {
        var rt=new RenderTexture(Width,Height,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB) {antiAliasing=1};rt.Create();
        var previous=RenderTexture.active;var previousTarget=camera.targetTexture;
        var picture=new Texture2D(Width,Height,TextureFormat.RGB24,false,false);
        try
        {
            camera.aspect=Width/(float)Height;camera.targetTexture=rt;
            var request=new UniversalRenderPipeline.SingleCameraRequest {destination=rt};
            // This supported URP API renders outside the game loop; no PlayMode or save service is needed.
            for(int i=0;i<4;i++)RenderPipeline.SubmitRenderRequest(camera,request);
            if(!(RenderPipelineManager.currentPipeline is UniversalRenderPipeline)||!RenderPipeline.SupportsRenderRequest(camera,request))
                throw new Exception("Actual URP render request was not active/supported");
            RenderTexture.active=rt;picture.ReadPixels(new Rect(0,0,Width,Height),0,0);picture.Apply();
            return picture.GetPixels32();
        }
        finally
        {
            camera.targetTexture=previousTarget;RenderTexture.active=previous;
            UnityEngine.Object.DestroyImmediate(picture);rt.Release();UnityEngine.Object.DestroyImmediate(rt);
        }
    }
    static void WritePng(string name,Color32[] pixels)
    {
        var texture=new Texture2D(Width,Height,TextureFormat.RGB24,false,false);texture.SetPixels32(pixels);texture.Apply();
        File.WriteAllBytes(Path.Combine(output,name),texture.EncodeToPNG());UnityEngine.Object.DestroyImmediate(texture);
    }
    static RectInt ProjectedBounds(GameObject root)
    {
        var r=root.GetComponentsInChildren<Renderer>();var b=r[0].bounds;foreach(var item in r.Skip(1))b.Encapsulate(item.bounds);
        var points=new List<Vector3>();for(int x=0;x<2;x++)for(int y=0;y<2;y++)for(int z=0;z<2;z++)
        {
            var p=camera.WorldToViewportPoint(new Vector3(x==0?b.min.x:b.max.x,y==0?b.min.y:b.max.y,z==0?b.min.z:b.max.z));
            points.Add(new Vector3(p.x*Width,p.y*Height,p.z));
        }
        if(points.Any(p=>p.z<=0))throw new Exception("Prop is behind camera");
        int left=Mathf.Clamp(Mathf.FloorToInt(points.Min(p=>p.x)),0,Width),right=Mathf.Clamp(Mathf.CeilToInt(points.Max(p=>p.x)),0,Width);
        int bottom=Mathf.Clamp(Mathf.FloorToInt(points.Min(p=>p.y)),0,Height),top=Mathf.Clamp(Mathf.CeilToInt(points.Max(p=>p.y)),0,Height);
        return new RectInt(left,bottom,right-left,top-bottom);
    }
    static void Capture(string file,string context,GameObject prop=null)
    {
        var pixels=RenderPixels();var v=new ViewResult {file=file,context=context,cameraPosition=V(camera.transform.position),cameraEuler=V(camera.transform.eulerAngles),fov=camera.fieldOfView,width=Width,height=Height,
            magentaPixels=pixels.Count(Pink),nonUniformImage=pixels.Distinct().Take(65).Count()>64};
        if(!v.nonUniformImage||v.magentaPixels>0)throw new Exception("Empty/pink render: "+file);
        if(prop!=null)
        {
            var bounds=ProjectedBounds(prop);v.propRoi=new[]{(float)bounds.x,bounds.y,bounds.width,bounds.height};v.propRoiPixels=bounds.width*bounds.height;
            var renderers=prop.GetComponentsInChildren<Renderer>();var states=renderers.Select(r=>r.enabled).ToArray();Color32[] hidden;
            try{foreach(var r in renderers)r.enabled=false;hidden=RenderPixels();}finally{for(int i=0;i<renderers.Length;i++)renderers[i].enabled=states[i];}
            for(int y=bounds.yMin;y<bounds.yMax;y++)for(int x=bounds.xMin;x<bounds.xMax;x++)if(Difference(pixels[y*Width+x],hidden[y*Width+x])>4)v.changedPropPixels++;
            v.propVisibilityVerified=v.propRoiPixels>0&&v.changedPropPixels>Mathf.Max(20,v.propRoiPixels/8);
            if(!v.propVisibilityVerified)throw new Exception("Prop is not visibly rendered: "+file);
        }
        WritePng(file,pixels);Views.Add(v);
    }
    static void Frame(Vector3 groundFocus,float distance)
    {
        var rotation=Quaternion.Euler(50f,180f,0f);camera.transform.SetPositionAndRotation(groundFocus+Vector3.up+rotation*(Vector3.back*distance),rotation);
    }
    static GameObject InstantiateProp(AssetExpected e,Vector3 position,Transform parent=null)
    {
        string path="Assets/ArtValidation/"+e.id+".glb";
        string staged=Path.Combine(Directory.GetParent(Application.dataPath).FullName,"Inputs",e.id+".glb");
        string physical=Path.Combine(Application.dataPath,"ArtValidation",e.id+".glb");
        Directory.CreateDirectory(Path.GetDirectoryName(physical));File.Copy(staged,physical,false);
        AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
        var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(path);if(prefab==null)throw new Exception("No imported prefab: "+e.id);
        var instance=(GameObject)PrefabUtility.InstantiatePrefab(prefab);instance.name="ArtValidation_"+e.id;
        if(parent!=null)instance.transform.SetParent(parent,false);
        instance.transform.SetPositionAndRotation(position,Quaternion.identity);instance.transform.localScale=Vector3.one;
        var collider=instance.AddComponent<BoxCollider>();collider.center=new Vector3(0,e.dimensions[1]/2f,0);collider.size=V(e.dimensions);
        return instance;
    }
    public static void Run()
    {
        output=Arg("-propsOutput");Directory.CreateDirectory(output);var errors=new List<string>();bool oldAsync=ShaderUtil.allowAsyncCompilation;
        var report=new Report {unityVersion=Application.unityVersion,graphicsDevice=SystemInfo.graphicsDeviceType.ToString(),limitations=new[]{
            "Read-only pinned game snapshot in art workspace; no PlayMode or game repository integration.",
            "Table placement is provisional validation-only; no table placeholder/accepted anchor exists in the pinned game.",
            "Candidate box colliders are physics-tested envelopes, not Claude-approved navigation/collision contracts.",
            "Editor offscreen URP renders verify this scene/configuration, not a shipping player build or interaction UI.",
            "Scene canvases disabled only in the isolated validation scene to exclude uninitialized EditMode HUD widgets; no image retouching.",
            "Original asset geometry/material values are immutable; no aesthetic tuning or new production props."}};
        try
        {
            var config=JsonUtility.FromJson<Config>(File.ReadAllText(Arg("-propsExpected")));report.sourceGameCommit=config.sourceGameCommit;report.sourceArchiveSHA256=config.sourceArchiveSHA256;
            report.graphicsEnabled=SystemInfo.graphicsDeviceType!=GraphicsDeviceType.Null;if(!report.graphicsEnabled)throw new Exception("A real graphics device is required");
            ShaderUtil.allowAsyncCompilation=false;
            EditorSceneManager.OpenScene(config.scenePath,OpenSceneMode.Single);camera=Camera.main;if(camera==null)throw new Exception("Actual game Main Camera missing");
            // Serialized HUD templates can cover the prop before runtime layout/visibility initializes.
            // This asset review deliberately excludes UI, without changing camera/world/light or source scene bytes.
            foreach(var canvas in UnityEngine.Object.FindObjectsByType<Canvas>(FindObjectsInactive.Include,FindObjectsSortMode.None))
                if(canvas.enabled){canvas.enabled=false;report.disabledCanvasCount++;}
            report.uiDisabledForAssetReview=true;
            var sourceUrp=AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(config.urpAssetPath);
            if(sourceUrp==null||GraphicsSettings.currentRenderPipeline!=sourceUrp||PlayerSettings.colorSpace!=ColorSpace.Linear)throw new Exception("Actual game URP/Linear settings mismatch");
            var sun=GameObject.Find("Sun").GetComponent<Light>();var data=camera.GetComponent<UniversalAdditionalCameraData>();
            report.lighting=new LightingResult {skybox=RenderSettings.skybox==null?"none":RenderSettings.skybox.name,ambientMode=RenderSettings.ambientMode.ToString(),ambientIntensity=RenderSettings.ambientIntensity,
                reflectionIntensity=RenderSettings.reflectionIntensity,fog=RenderSettings.fog,sunIntensity=sun.intensity,sunColor=new[]{sun.color.r,sun.color.g,sun.color.b,sun.color.a},sunEuler=V(sun.transform.eulerAngles),
                activeUrpAsset=AssetDatabase.GetAssetPath(sourceUrp),postProcessing=data!=null&&data.renderPostProcessing,hdr=camera.allowHDR,environmentRefreshRequested=true};
            DynamicGI.UpdateEnvironment();
            Vector3 originalCameraPosition=camera.transform.position;Quaternion originalCameraRotation=camera.transform.rotation;
            Capture("01_game_start_placeholder.png","Actual serialized Bootstrap camera and unchanged source world/light.");
            var mailbox=GameObject.Find("StarterNeighborhood/Mailbox");if(mailbox==null||!Near(mailbox.transform.position,new Vector3(-6.2f,0,-4.85f)))throw new Exception("Pinned mailbox source placement mismatch");
            foreach(var r in mailbox.GetComponentsInChildren<Renderer>())r.enabled=false;
            foreach(var c in mailbox.GetComponents<Collider>())c.enabled=false;
            var imported=new Dictionary<string,GameObject>();
            foreach(var e in config.assets)
            {
                var position=e.id=="prop_mailbox_001"?mailbox.transform.position:V(config.tablePosition);
                imported[e.id]=InstantiateProp(e,position,e.id=="prop_mailbox_001"?mailbox.transform:null);
            }
            Capture("02_game_start_imported.png","Actual serialized Bootstrap camera; imported mailbox replaces only placeholder visuals in the validation scene.",imported["prop_mailbox_001"]);
            foreach(var e in config.assets)
            {
                var instance=imported[e.id];Frame(instance.transform.position,16f);
                Capture(e.id+"_game16m.png",e.id=="prop_mailbox_001"?"Existing mailbox location, game camera parameters at16m.":"Provisional cafe validation position, game camera parameters at16m.",instance);
                Frame(instance.transform.position,6f);Capture(e.id+"_game6m.png","Game minimum zoom6m; source Bootstrap world, Sun, sky/ambient and URP unchanged.",instance);
            }
            camera.transform.SetPositionAndRotation(originalCameraPosition,originalCameraRotation);
            report.activePipeline=RenderPipelineManager.currentPipeline==null?"none":RenderPipelineManager.currentPipeline.GetType().FullName;
            report.urpActiveAfterRendering=RenderPipelineManager.currentPipeline is UniversalRenderPipeline;
            report.gltfastVersion=Package("com.unity.cloud.gltfast");report.urpVersion=Package("com.unity.render-pipelines.universal");
            var results=new List<AssetResult>();
            foreach(var e in config.assets)
            {
                var result=Inspect(imported[e.id],e,e.id=="prop_mailbox_001"?"Existing game mailbox anchor":"Provisional cafe validation site; not a game anchor");
                result.importer=AssetImporter.GetAtPath("Assets/ArtValidation/"+e.id+".glb").GetType().FullName;
                if(!result.importer.Contains("GLTFast"))errors.Add("Unexpected importer");results.Add(result);errors.AddRange(result.errors.Select(x=>e.id+": "+x));
            }
            report.assets=results.ToArray();report.declaredUrpShaders=results.All(a=>a.materials.All(m=>m.declaresUrp));
            string saved="Assets/ArtValidation/GameLightingPreview.unity";
            if(!EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(),saved))throw new Exception("Validation scene save failed");
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);EditorSceneManager.OpenScene(saved,OpenSceneMode.Single);
            report.importedSceneSavedAndReopened=true;
            foreach(var e in config.assets)
            {
                var root=GameObject.Find("ArtValidation_"+e.id);if(root==null||Inspect(root,e,"Reopened validation scene").errors.Length!=0)report.importedSceneSavedAndReopened=false;
            }
            if(!report.importedSceneSavedAndReopened)errors.Add("Imported validation scene did not preserve checks after reopen");
            if(!report.urpActiveAfterRendering||!report.declaredUrpShaders)errors.Add("Active/declared URP verification failed");
        }
        catch(Exception e){errors.Add(e.GetType().Name+": "+e.Message);}
        finally{ShaderUtil.allowAsyncCompilation=oldAsync;}
        report.views=Views.ToArray();report.errors=errors.ToArray();report.status=errors.Count==0?"passed-graphics-import-validation-only":"failed";
        File.WriteAllText(Path.Combine(output,"unity-game-lighting-report.json"),JsonUtility.ToJson(report,true)+"\n");
        Debug.Log("PROPS_GAME_LIGHTING_"+report.status);EditorApplication.Exit(errors.Count==0?0:1);
    }
}
