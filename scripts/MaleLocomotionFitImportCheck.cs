// LocomotionFit: isolated art-only A03 skin/clip import and URP motion evidence; no game code.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public static class MaleLocomotionFitImportCheck
{
 [Serializable] public class Expected { public string assetId; public int triangles=29367,materials=9,bones=52; public string[] clips; public int videoFps=24; }
 [Serializable] public class MeshResult { public string name; public int vertices,triangles,bones,bindposes,maxInfluences; public float maxWeightSumError; public bool finite,indicesValid,bonesAssigned; }
 [Serializable] public class MaterialResult { public string name,shader,pipelineTag; public bool supported,shaderHasError,baseTexturePresent; }
 [Serializable] public class Sample { public float time; public float[] min,max; public string sha256; public float maxChangeFromFirst; }
 [Serializable] public class ClipResult { public string name; public float duration; public int curves,frameCount; public bool legacy,finite,hasMotion; public float loopClosureMeters; public Sample[] samples; }
 [Serializable] public class Report {
  public string schema="male-fit-unity-motion-1",status,unityVersion,graphicsDevice,gltfastVersion,urpVersion,importer;
  public bool savedReopenedPoseMatches,urpRendered,matchedBaselineComparisonsRendered,humanoidTested=false,gameIntegrationTested=false;
  public int triangles,materialCount,skinnedMeshes,staticMeshes;
  public MeshResult[] meshes; public MaterialResult[] materials; public ClipResult[] clips; public string[] errors,importerMessages,limitations;
 }
 static string Arg(string name){var a=Environment.GetCommandLineArgs();for(int i=0;i+1<a.Length;i++)if(a[i]==name)return a[i+1];return null;}
 public static bool Finite(float f)=>!float.IsNaN(f)&&!float.IsInfinity(f);
 public static bool Finite(Vector3 v)=>Finite(v.x)&&Finite(v.y)&&Finite(v.z);
 static float[] V(Vector3 p)=>new[]{p.x,p.y,p.z};
 public static Vector3[] Bake(GameObject root) {
  var points=new List<Vector3>();
  foreach(var r in root.GetComponentsInChildren<SkinnedMeshRenderer>(true).OrderBy(r=>r.name)) {
   var m=new Mesh();r.BakeMesh(m);points.AddRange(m.vertices.Select(v=>r.transform.TransformPoint(v)));UnityEngine.Object.DestroyImmediate(m);
  }
  foreach(var f in root.GetComponentsInChildren<MeshFilter>(true).OrderBy(f=>f.name))points.AddRange(f.sharedMesh.vertices.Select(v=>f.transform.TransformPoint(v)));
  return points.ToArray();
 }
 static string Hash(Vector3[] pts){using(var h=SHA256.Create()){var data=new byte[pts.Length*12];for(int i=0;i<pts.Length;i++){Buffer.BlockCopy(BitConverter.GetBytes(pts[i].x),0,data,i*12,4);Buffer.BlockCopy(BitConverter.GetBytes(pts[i].y),0,data,i*12+4,4);Buffer.BlockCopy(BitConverter.GetBytes(pts[i].z),0,data,i*12+8,4);}return BitConverter.ToString(h.ComputeHash(data)).Replace("-","").ToLowerInvariant();}}
 static float Delta(Vector3[] a,Vector3[] b){if(a.Length!=b.Length)throw new Exception("Baked vertex count changed");return a.Select((p,i)=>Vector3.Distance(p,b[i])).DefaultIfEmpty(0).Max();}
 static Sample InspectSample(Vector3[] pts,float time,Vector3[] first){if(pts.Length==0||!pts.All(Finite))throw new Exception("Nonfinite/empty baked surface");var min=pts.Aggregate(Vector3.Min);var max=pts.Aggregate(Vector3.Max);if((max-min).magnitude>5)throw new Exception("Exploded sampled surface");return new Sample{time=time,min=V(min),max=V(max),sha256=Hash(pts),maxChangeFromFirst=Delta(pts,first)};}
 static MeshResult InspectSkin(SkinnedMeshRenderer r){
  var m=r.sharedMesh;var v=m.vertices;var n=m.normals;var indices=m.triangles;
  var x=new MeshResult{name=r.name,vertices=v.Length,triangles=indices.Length/3,bones=r.bones.Length,bindposes=m.bindposes.Length,finite=v.All(Finite)&&n.Length==v.Length&&n.All(Finite),indicesValid=indices.All(i=>i>=0&&i<v.Length),bonesAssigned=r.bones.All(b=>b!=null)};
  foreach(var b in m.bindposes)for(int i=0;i<16;i++)x.finite&=Finite(b[i]);
  var counts=m.GetBonesPerVertex();var weights=m.GetAllBoneWeights();int cursor=0;
  foreach(byte count in counts){x.maxInfluences=Math.Max(x.maxInfluences,count);float sum=0;for(int j=0;j<count;j++){var w=weights[cursor++];sum+=w.weight;x.finite&=Finite(w.weight)&&w.weight>=0&&w.boneIndex>=0&&w.boneIndex<r.bones.Length;}x.maxWeightSumError=Mathf.Max(x.maxWeightSumError,Mathf.Abs(sum-1));}
  counts.Dispose();weights.Dispose();return x;
 }
 public static void Capture(Camera cam,string path,int width,int height){
  Directory.CreateDirectory(Path.GetDirectoryName(path));float previousAspect=cam.aspect;cam.aspect=width/(float)height;var rt=new RenderTexture(width,height,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB);rt.Create();var request=new UniversalRenderPipeline.SingleCameraRequest{destination=rt};
  for(int i=0;i<2;i++)RenderPipeline.SubmitRenderRequest(cam,request);if(!(RenderPipelineManager.currentPipeline is UniversalRenderPipeline))throw new Exception("URP not active");
  var old=RenderTexture.active;RenderTexture.active=rt;var tex=new Texture2D(width,height,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,width,height),0,0);tex.Apply();File.WriteAllBytes(path,tex.EncodeToPNG());RenderTexture.active=old;UnityEngine.Object.DestroyImmediate(tex);rt.Release();UnityEngine.Object.DestroyImmediate(rt);cam.aspect=previousAspect;
 }
 static void FullCamera(Camera cam){cam.orthographic=true;cam.orthographicSize=1.10f;cam.transform.position=new Vector3(-2.8f,1.0f,4);cam.transform.LookAt(new Vector3(0,.875f,0));}
 static void GameCamera(Camera cam){cam.orthographic=false;cam.fieldOfView=40;var target=new Vector3(0,.875f,0);cam.transform.position=target+new Vector3(0,16*Mathf.Sin(50*Mathf.Deg2Rad),16*Mathf.Cos(50*Mathf.Deg2Rad));cam.transform.LookAt(target);}
 static void CloseCamera(Camera cam,Vector3 target,float size){cam.orthographic=true;cam.orthographicSize=size;cam.transform.position=target+new Vector3(-.55f,.25f,1);cam.transform.LookAt(target);}
 static Transform FindJoint(GameObject root,string[] tokens){return root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t=>tokens.Any(s=>t.name.Equals(s,StringComparison.OrdinalIgnoreCase)))??root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t=>tokens.Any(s=>t.name.IndexOf(s,StringComparison.OrdinalIgnoreCase)>=0));}
 static Dictionary<string,Tuple<Vector3,Quaternion,Vector3>> RestPose;
 static void SampleClip(AnimationClip clip,GameObject instance,float time){
  foreach(var t in instance.GetComponentsInChildren<Transform>(true)){string path=AnimationUtility.CalculateTransformPath(t,instance.transform);if(RestPose.TryGetValue(path,out var p)){t.localPosition=p.Item1;t.localRotation=p.Item2;t.localScale=p.Item3;}}
  foreach(var animator in instance.GetComponentsInChildren<Animator>(true))animator.enabled=false;clip.SampleAnimation(instance,time);foreach(var r in instance.GetComponentsInChildren<SkinnedMeshRenderer>(true)){r.updateWhenOffscreen=true;r.forceMatrixRecalculationPerRender=true;r.quality=SkinQuality.Bone4;}}
 public static void Run(){
  string output=Arg("-fitOutput");Directory.CreateDirectory(output);var errors=new List<string>();var report=new Report{unityVersion=Application.unityVersion,graphicsDevice=SystemInfo.graphicsDeviceType.ToString(),limitations=new[]{"Isolated art-only Unity URP proof, not life-sim-game or final game lighting.","Direct imported clip sampling and baked skin surfaces; actual PlayMode and limited crossfade proof are recorded separately. No Humanoid Avatar, gameplay controller, physics or runtime performance certification.","Geometry samples and close-up renders do not prove absence of every self-intersection."}};
  try {
   var expected=JsonUtility.FromJson<Expected>(File.ReadAllText(Arg("-fitExpected")));
   var rd=ScriptableObject.CreateInstance<UniversalRendererData>();AssetDatabase.CreateAsset(rd,"Assets/LocomotionFitRenderer.asset");var pipeline=UniversalRenderPipelineAsset.Create(rd);AssetDatabase.CreateAsset(pipeline,"Assets/LocomotionFitURP.asset");GraphicsSettings.defaultRenderPipeline=pipeline;QualitySettings.renderPipeline=null;PlayerSettings.colorSpace=ColorSpace.Linear;QualitySettings.skinWeights=SkinWeights.FourBones;AssetDatabase.SaveAssets();
   var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
   string glbPath="Assets/Character/"+expected.assetId+".glb";File.Copy(Path.Combine(Directory.GetParent(Application.dataPath).FullName,"Inputs",expected.assetId+".glb"),glbPath,false);AssetDatabase.ImportAsset(glbPath,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
   var importer=AssetImporter.GetAtPath(glbPath);report.importer=importer.GetType().FullName;
   var field=importer.GetType().GetField("reportItems",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);var messages=new List<string>();var items=field?.GetValue(importer) as System.Collections.IEnumerable;if(items!=null)foreach(var item in items){messages.Add(item.ToString());var li=item as GLTFast.Logging.LogItem;if(li!=null&&(li.Type==LogType.Error||li.Type==LogType.Exception))errors.Add("Importer error: "+item);}report.importerMessages=messages.ToArray();
   var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(glbPath);if(prefab==null)throw new Exception("No imported prefab");var instance=(GameObject)PrefabUtility.InstantiatePrefab(prefab);instance.name=expected.assetId;RestPose=instance.GetComponentsInChildren<Transform>(true).ToDictionary(t=>AnimationUtility.CalculateTransformPath(t,instance.transform),t=>Tuple.Create(t.localPosition,t.localRotation,t.localScale));
   var skins=instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);report.meshes=skins.Select(InspectSkin).ToArray();report.skinnedMeshes=skins.Length;report.staticMeshes=instance.GetComponentsInChildren<MeshFilter>(true).Length;report.triangles=report.meshes.Sum(m=>m.triangles)+instance.GetComponentsInChildren<MeshFilter>(true).Sum(f=>f.sharedMesh.triangles.Length/3);report.materialCount=instance.GetComponentsInChildren<Renderer>(true).SelectMany(r=>r.sharedMaterials).Distinct().Count();
   if(report.skinnedMeshes==0||report.triangles!=expected.triangles||report.materialCount!=expected.materials)errors.Add("Skin/triangle/material count mismatch");
   foreach(var m in report.meshes)if(!m.finite||!m.indicesValid||!m.bonesAssigned||m.bones!=m.bindposes||m.bones!=expected.bones||m.maxInfluences>4||m.maxWeightSumError>.0001f)errors.Add("Invalid skin: "+m.name);
   var clips=AssetDatabase.LoadAllAssetsAtPath(glbPath).OfType<AnimationClip>().OrderBy(c=>c.name).ToArray();if(clips.Length==0)throw new Exception("No imported animation clips");foreach(var n in expected.clips)if(!clips.Any(c=>c.name.Equals(n,StringComparison.OrdinalIgnoreCase)))errors.Add("Missing clip "+n);
   var key=new GameObject("LocomotionFit_Key").AddComponent<Light>();key.type=LightType.Directional;key.intensity=1.5f;key.transform.rotation=Quaternion.Euler(40,155,0);var fill=new GameObject("LocomotionFit_Fill").AddComponent<Light>();fill.type=LightType.Directional;fill.intensity=.5f;fill.transform.rotation=Quaternion.Euler(20,225,0);RenderSettings.ambientMode=AmbientMode.Flat;RenderSettings.ambientLight=new Color(.4f,.4f,.4f);
   var cam=new GameObject("LocomotionFit_Camera").AddComponent<Camera>();cam.nearClipPlane=.05f;cam.farClipPlane=50;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.30f,.32f,.34f);cam.GetUniversalAdditionalCameraData().renderPostProcessing=false;
   var results=new List<ClipResult>();
   foreach(var clip in clips) {
    var cr=new ClipResult{name=clip.name,duration=clip.length,legacy=clip.legacy,curves=AnimationUtility.GetCurveBindings(clip).Length,finite=true};var samples=new List<Sample>();SampleClip(clip,instance,0);var first=Bake(instance);
    for(int i=0;i<=8;i++){float t=clip.length*i/8;SampleClip(clip,instance,t);var pts=Bake(instance);samples.Add(InspectSample(pts,t,first));if(i==8)cr.loopClosureMeters=Delta(pts,first);}
    cr.samples=samples.ToArray();cr.hasMotion=samples.Max(s=>s.maxChangeFromFirst)>.00005f;if(cr.curves==0||clip.length<=0||!cr.hasMotion)errors.Add("Empty/static clip "+clip.name);
    cr.frameCount=Mathf.Max(2,Mathf.CeilToInt(clip.length*expected.videoFps));
    for(int i=0;i<cr.frameCount;i++){SampleClip(clip,instance,i/(float)expected.videoFps);FullCamera(cam);Capture(cam,Path.Combine(output,"frames",clip.name,"frame_"+i.ToString("D4")+".png"),768,768);GameCamera(cam);Capture(cam,Path.Combine(output,"frames16m",clip.name,"frame_"+i.ToString("D4")+".png"),1280,720);}
    SampleClip(clip,instance,clip.length*.25f);FullCamera(cam);Capture(cam,Path.Combine(output,clip.name+"_full.png"),900,900);GameCamera(cam);Capture(cam,Path.Combine(output,clip.name+"_game16m.png"),1280,720);
    foreach(var joint in new[]{new{label="elbow",names=new[]{"DEF-Forearm_1.L","Forearm.L","LowerArm.L","LeftLowerArm"}},new{label="knee",names=new[]{"DEF-Shin_1.L","Shin.L","LowerLeg.L","LeftLowerLeg"}},new{label="hand",names=new[]{"DEF-Hand.L","Hand.L","LeftHand"}}}){var bone=FindJoint(instance,joint.names);if(bone!=null){var target=bone.position;if(joint.label=="hand"){var middle=FindJoint(instance,new[]{"Middle2.L"});if(middle!=null)target=(target+middle.position)*.5f;}CloseCamera(cam,target,joint.label=="hand"?.18f:.23f);Capture(cam,Path.Combine(output,clip.name+"_"+joint.label+".png"),700,700);}}
    results.Add(cr);
   }
   report.materials=instance.GetComponentsInChildren<Renderer>(true).SelectMany(r=>r.sharedMaterials).Distinct().Select(mat=>new MaterialResult{name=mat==null?"NULL":mat.name,shader=mat?.shader?.name,pipelineTag=mat==null?"":mat.GetTag("RenderPipeline",false),supported=mat!=null&&mat.shader!=null&&mat.shader.isSupported,shaderHasError=mat==null||mat.shader==null||ShaderUtil.ShaderHasError(mat.shader),baseTexturePresent=mat!=null&&mat.HasProperty("baseColorTexture")&&mat.GetTexture("baseColorTexture")!=null}).ToArray();
   foreach(var m in report.materials)if(!m.supported||m.shaderHasError||m.pipelineTag!="UniversalPipeline")errors.Add("Unsupported/error/non-URP material after active URP render: "+m.name+" tag="+m.pipelineTag+" shader="+m.shader);
   report.clips=results.ToArray();report.urpRendered=RenderPipelineManager.currentPipeline is UniversalRenderPipeline;
   report.matchedBaselineComparisonsRendered=false; // Appearance/rig preservation is checked independently against B02.
   var checkClip=clips.FirstOrDefault(c=>c.name.IndexOf("walk",StringComparison.OrdinalIgnoreCase)>=0)??clips[0];SampleClip(checkClip,instance,checkClip.length*.25f);var before=Bake(instance);FullCamera(cam);EditorSceneManager.MarkSceneDirty(scene);if(!EditorSceneManager.SaveScene(scene,"Assets/LocomotionFitAnimationProbe.unity"))throw new Exception("Scene save failed");EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);EditorSceneManager.OpenScene("Assets/LocomotionFitAnimationProbe.unity",OpenSceneMode.Single);var reopened=GameObject.Find(expected.assetId);if(reopened==null)throw new Exception("Missing reopened character");SampleClip(checkClip,reopened,checkClip.length*.25f);report.savedReopenedPoseMatches=Delta(before,Bake(reopened))<.000001f;if(!report.savedReopenedPoseMatches)errors.Add("Reopened sampled pose differs");
   report.gltfastVersion=UnityEditor.PackageManager.PackageInfo.GetAllRegisteredPackages().First(p=>p.name=="com.unity.cloud.gltfast").version;report.urpVersion=UnityEditor.PackageManager.PackageInfo.GetAllRegisteredPackages().First(p=>p.name=="com.unity.render-pipelines.universal").version;
  } catch(Exception e){errors.Add(e.ToString());Debug.LogException(e);}
  report.errors=errors.ToArray();report.status=errors.Count==0?"passed-art-skin-animation-import-reopen":"failed";File.WriteAllText(Path.Combine(output,"unity-animation-report.json"),JsonUtility.ToJson(report,true)+"\n");EditorApplication.Exit(errors.Count==0?0:1);
 }


}
