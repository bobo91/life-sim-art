// B02: isolated art-only A03 skin/clip import and URP motion evidence; no game code.
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

public static class MaleNeutralB02AnimationCheck
{
 [Serializable] public class Expected { public string assetId; public int triangles=29367,materials=9,bones=52; public string[] clips; public int videoFps=24; }
 [Serializable] public class MeshResult { public string name; public int vertices,triangles,bones,bindposes,maxInfluences; public float maxWeightSumError; public bool finite,indicesValid,bonesAssigned; }
 [Serializable] public class MaterialResult { public string name,shader,pipelineTag; public bool supported,shaderHasError,baseTexturePresent; }
 [Serializable] public class Sample { public float time; public float[] min,max; public string sha256; public float maxChangeFromFirst; }
 [Serializable] public class ClipResult { public string name; public float duration; public int curves,frameCount; public bool legacy,finite,hasMotion; public float loopClosureMeters; public Sample[] samples; }
 [Serializable] public class Report {
  public string schema="male-b02-unity-motion-1",status,unityVersion,graphicsDevice,gltfastVersion,urpVersion,importer;
  public bool savedReopenedPoseMatches,urpRendered,matchedBaselineComparisonsRendered,humanoidTested=false,gameIntegrationTested=false;
  public int triangles,materialCount,skinnedMeshes,staticMeshes;
  public MeshResult[] meshes; public MaterialResult[] materials; public ClipResult[] clips; public string[] errors,importerMessages,limitations;
 }
 static string Arg(string name){var a=Environment.GetCommandLineArgs();for(int i=0;i+1<a.Length;i++)if(a[i]==name)return a[i+1];return null;}
 static bool Finite(float f)=>!float.IsNaN(f)&&!float.IsInfinity(f);
 static bool Finite(Vector3 v)=>Finite(v.x)&&Finite(v.y)&&Finite(v.z);
 static float[] V(Vector3 p)=>new[]{p.x,p.y,p.z};
 static Vector3[] Bake(GameObject root) {
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
 static void Capture(Camera cam,string path,int width,int height){
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
  string output=Arg("-b02Output");Directory.CreateDirectory(output);var errors=new List<string>();var report=new Report{unityVersion=Application.unityVersion,graphicsDevice=SystemInfo.graphicsDeviceType.ToString(),limitations=new[]{"Isolated art-only Unity URP proof, not life-sim-game or final game lighting.","Direct imported clip sampling and baked skin surfaces; actual PlayMode and limited crossfade proof are recorded separately. No Humanoid Avatar, gameplay controller, physics or runtime performance certification.","Geometry samples and close-up renders do not prove absence of every self-intersection."}};
  try {
   var expected=JsonUtility.FromJson<Expected>(File.ReadAllText(Arg("-b02Expected")));
   var rd=ScriptableObject.CreateInstance<UniversalRendererData>();AssetDatabase.CreateAsset(rd,"Assets/B02Renderer.asset");var pipeline=UniversalRenderPipelineAsset.Create(rd);AssetDatabase.CreateAsset(pipeline,"Assets/B02URP.asset");GraphicsSettings.defaultRenderPipeline=pipeline;QualitySettings.renderPipeline=null;PlayerSettings.colorSpace=ColorSpace.Linear;QualitySettings.skinWeights=SkinWeights.FourBones;AssetDatabase.SaveAssets();
   var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
   string glbPath="Assets/Character/"+expected.assetId+".glb";File.Copy(Path.Combine(Directory.GetParent(Application.dataPath).FullName,"Inputs",expected.assetId+".glb"),glbPath,false);AssetDatabase.ImportAsset(glbPath,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
   var importer=AssetImporter.GetAtPath(glbPath);report.importer=importer.GetType().FullName;
   var field=importer.GetType().GetField("reportItems",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);var messages=new List<string>();var items=field?.GetValue(importer) as System.Collections.IEnumerable;if(items!=null)foreach(var item in items){messages.Add(item.ToString());var li=item as GLTFast.Logging.LogItem;if(li!=null&&(li.Type==LogType.Error||li.Type==LogType.Exception))errors.Add("Importer error: "+item);}report.importerMessages=messages.ToArray();
   var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(glbPath);if(prefab==null)throw new Exception("No imported prefab");var instance=(GameObject)PrefabUtility.InstantiatePrefab(prefab);instance.name=expected.assetId;RestPose=instance.GetComponentsInChildren<Transform>(true).ToDictionary(t=>AnimationUtility.CalculateTransformPath(t,instance.transform),t=>Tuple.Create(t.localPosition,t.localRotation,t.localScale));
   var skins=instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);report.meshes=skins.Select(InspectSkin).ToArray();report.skinnedMeshes=skins.Length;report.staticMeshes=instance.GetComponentsInChildren<MeshFilter>(true).Length;report.triangles=report.meshes.Sum(m=>m.triangles)+instance.GetComponentsInChildren<MeshFilter>(true).Sum(f=>f.sharedMesh.triangles.Length/3);report.materialCount=instance.GetComponentsInChildren<Renderer>(true).SelectMany(r=>r.sharedMaterials).Distinct().Count();
   if(report.skinnedMeshes==0||report.triangles!=expected.triangles||report.materialCount!=expected.materials)errors.Add("Skin/triangle/material count mismatch");
   foreach(var m in report.meshes)if(!m.finite||!m.indicesValid||!m.bonesAssigned||m.bones!=m.bindposes||m.bones!=expected.bones||m.maxInfluences>4||m.maxWeightSumError>.0001f)errors.Add("Invalid skin: "+m.name);
   var clips=AssetDatabase.LoadAllAssetsAtPath(glbPath).OfType<AnimationClip>().OrderBy(c=>c.name).ToArray();if(clips.Length==0)throw new Exception("No imported animation clips");foreach(var n in expected.clips)if(!clips.Any(c=>c.name.Equals(n,StringComparison.OrdinalIgnoreCase)))errors.Add("Missing clip "+n);
   var key=new GameObject("B02_Key").AddComponent<Light>();key.type=LightType.Directional;key.intensity=1.5f;key.transform.rotation=Quaternion.Euler(40,155,0);var fill=new GameObject("B02_Fill").AddComponent<Light>();fill.type=LightType.Directional;fill.intensity=.5f;fill.transform.rotation=Quaternion.Euler(20,225,0);RenderSettings.ambientMode=AmbientMode.Flat;RenderSettings.ambientLight=new Color(.4f,.4f,.4f);
   var cam=new GameObject("B02_Camera").AddComponent<Camera>();cam.nearClipPlane=.05f;cam.farClipPlane=50;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.30f,.32f,.34f);cam.GetUniversalAdditionalCameraData().renderPostProcessing=false;
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
   RenderComparisons(instance,clips,cam,output);report.matchedBaselineComparisonsRendered=true;
   var checkClip=clips.FirstOrDefault(c=>c.name.IndexOf("walk",StringComparison.OrdinalIgnoreCase)>=0)??clips[0];SampleClip(checkClip,instance,checkClip.length*.25f);var before=Bake(instance);FullCamera(cam);EditorSceneManager.MarkSceneDirty(scene);if(!EditorSceneManager.SaveScene(scene,"Assets/B02AnimationProbe.unity"))throw new Exception("Scene save failed");EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);EditorSceneManager.OpenScene("Assets/B02AnimationProbe.unity",OpenSceneMode.Single);var reopened=GameObject.Find(expected.assetId);if(reopened==null)throw new Exception("Missing reopened character");SampleClip(checkClip,reopened,checkClip.length*.25f);report.savedReopenedPoseMatches=Delta(before,Bake(reopened))<.000001f;if(!report.savedReopenedPoseMatches)errors.Add("Reopened sampled pose differs");
   report.gltfastVersion=UnityEditor.PackageManager.PackageInfo.GetAllRegisteredPackages().First(p=>p.name=="com.unity.cloud.gltfast").version;report.urpVersion=UnityEditor.PackageManager.PackageInfo.GetAllRegisteredPackages().First(p=>p.name=="com.unity.render-pipelines.universal").version;
  } catch(Exception e){errors.Add(e.ToString());Debug.LogException(e);}
  report.errors=errors.ToArray();report.status=errors.Count==0?"passed-art-skin-animation-import-reopen":"failed";File.WriteAllText(Path.Combine(output,"unity-animation-report.json"),JsonUtility.ToJson(report,true)+"\n");EditorApplication.Exit(errors.Count==0?0:1);
 }


 // B01/B02 use the exact same camera and baseline-derived target for each paired capture.
 static void RenderComparisons(GameObject final,AnimationClip[] clips,Camera cam,string output){
  var finalRest=RestPose;final.SetActive(false);string path="Assets/Character/B01_baseline.glb";File.Copy(Arg("-b02Baseline"),path,false);AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
  var baseline=(GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(path));baseline.name="B01_Comparison";var baselineRest=baseline.GetComponentsInChildren<Transform>(true).ToDictionary(t=>AnimationUtility.CalculateTransformPath(t,baseline.transform),t=>Tuple.Create(t.localPosition,t.localRotation,t.localScale));var beforeClips=AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().ToArray();
  foreach(string clipName in new[]{"idle","walk","run"}){
   var old=beforeClips.First(c=>c.name==clipName);var current=clips.First(c=>c.name==clipName);float t=old.length*.25f;RestPose=baselineRest;baseline.SetActive(true);SampleClip(old,baseline,t);
   foreach(var q in new[]{new{label="elbow",bone="LowerArm.L",size=.23f},new{label="knee",bone="LowerLeg.L",size=.23f},new{label="wrist",bone="Hand.L",size=.105f},new{label="hand",bone="Hand.L",size=.18f}}){
    var joint=FindJoint(baseline,new[]{q.bone});var target=joint.position;if(q.label=="hand"){var middle=FindJoint(baseline,new[]{"Middle2.L"});target=(target+middle.position)*.5f;}CloseCamera(cam,target,q.size);Capture(cam,Path.Combine(output,"comparison","B01_"+clipName+"_"+q.label+".png"),700,700);
    baseline.SetActive(false);final.SetActive(true);RestPose=finalRest;SampleClip(current,final,t);Capture(cam,Path.Combine(output,"comparison","B02_"+clipName+"_"+q.label+".png"),700,700);final.SetActive(false);baseline.SetActive(true);RestPose=baselineRest;SampleClip(old,baseline,t);
   }
  }
  // Compare identity at bind under identical front/three-quarter face cameras.
  foreach(string view in new[]{"front","three_quarter"}){
   foreach(var t in baseline.GetComponentsInChildren<Transform>(true)){var p=baselineRest[AnimationUtility.CalculateTransformPath(t,baseline.transform)];t.localPosition=p.Item1;t.localRotation=p.Item2;t.localScale=p.Item3;}
   foreach(var skin in baseline.GetComponentsInChildren<SkinnedMeshRenderer>(true)){skin.updateWhenOffscreen=true;skin.forceMatrixRecalculationPerRender=true;}
   cam.orthographic=true;cam.orthographicSize=.27125f;cam.transform.position=view=="front"?new Vector3(0,1.54f,1.6f):new Vector3(-.9f,1.54f,1.285f);cam.transform.LookAt(new Vector3(0,1.54f,.03f));Capture(cam,Path.Combine(output,"comparison","B01_face_"+view+".png"),900,900);
   baseline.SetActive(false);final.SetActive(true);foreach(var t in final.GetComponentsInChildren<Transform>(true)){var p=finalRest[AnimationUtility.CalculateTransformPath(t,final.transform)];t.localPosition=p.Item1;t.localRotation=p.Item2;t.localScale=p.Item3;}foreach(var skin in final.GetComponentsInChildren<SkinnedMeshRenderer>(true)){skin.updateWhenOffscreen=true;skin.forceMatrixRecalculationPerRender=true;}Capture(cam,Path.Combine(output,"comparison","B02_face_"+view+".png"),900,900);final.SetActive(false);baseline.SetActive(true);
  }
  UnityEngine.Object.DestroyImmediate(baseline);final.SetActive(true);RestPose=finalRest;
  File.WriteAllText(Path.Combine(output,"comparison-camera.json"),"{\"schema\":\"b02-matched-comparison-1\",\"pairedCameraMatches\":true,\"jointSampleTime\":\"B01 clip duration *0.25\",\"baselineDerivedTargets\":true,\"identityViews\":\"bind front and three-quarter\",\"sourceMeshesEditedForCapture\":false}");
 }

 // A separate bounded real PlayMode smoke; four directly selected Animator states,
 // not a gameplay controller or Humanoid retargeting system.
 [Serializable] public class RuntimeClipResult {public string name;public float firstNormalizedTime,lastNormalizedTime,maxVertexMotionMeters;public bool animatorInitialized,finite;}
 [Serializable] public class TransitionResult {public string from,to;public float fadeSeconds=.2f,maxFrameStepMeters;public int samples,captureCount;public bool finite=true,reachedTarget;}
 [Serializable] public class RuntimeReport {public string schema="male-b02-actual-playmode-1",status;public bool actualPlayMode,gameIntegrationTested=false,humanoidTested=false;public RuntimeClipResult[] clips;public TransitionResult[] transitions;public string[] errors;}
 static string RuntimeOutput;static AnimationClip[] RuntimeClips;static int RuntimeIndex=-1;static double RuntimeStart;static Vector3[] RuntimeFirst;static RuntimeClipResult RuntimeCurrent;static List<RuntimeClipResult> RuntimeResults;static List<string> RuntimeErrors;
 static int TransitionIndex=-2;static string[] TransitionStates={"idle","walk","run","walk","idle","turn"};static List<TransitionResult> TransitionResults;static TransitionResult CurrentTransition;static Vector3[] PreviousTransitionPoints;static double LastTransitionSample;static int TransitionCapture;
 public static void RunPlayMode(){
  RuntimeOutput=Arg("-b02Output");Directory.CreateDirectory(RuntimeOutput);RuntimeResults=new List<RuntimeClipResult>();RuntimeErrors=new List<string>();TransitionResults=new List<TransitionResult>();
  try{
   EditorSceneManager.OpenScene("Assets/B02AnimationProbe.unity",OpenSceneMode.Single);var expected=JsonUtility.FromJson<Expected>(File.ReadAllText(Arg("-b02Expected")));var path="Assets/Character/"+expected.assetId+".glb";RuntimeClips=AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().OrderBy(c=>c.name).ToArray();
   var root=GameObject.Find(expected.assetId);if(root==null)throw new Exception("No saved probe character");var animator=root.GetComponent<Animator>()??root.AddComponent<Animator>();var controller=UnityEditor.Animations.AnimatorController.CreateAnimatorControllerAtPath("Assets/B02FourClipSmoke.controller");foreach(var clip in RuntimeClips){var state=controller.layers[0].stateMachine.AddState(clip.name);state.motion=clip;state.writeDefaultValues=false;}animator.runtimeAnimatorController=controller;animator.applyRootMotion=false;animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;animator.enabled=true;
   foreach(var skin in root.GetComponentsInChildren<SkinnedMeshRenderer>(true)){skin.updateWhenOffscreen=true;skin.forceMatrixRecalculationPerRender=true;}EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());AssetDatabase.SaveAssets();EditorSettings.enterPlayModeOptionsEnabled=true;EditorSettings.enterPlayModeOptions=EnterPlayModeOptions.DisableDomainReload;EditorApplication.update+=RuntimeTick;RuntimeStart=EditorApplication.timeSinceStartup;EditorApplication.EnterPlaymode();
  }catch(Exception e){RuntimeErrors.Add(e.ToString());FinishRuntime();}
 }
 static void RuntimeTick(){try{
  if(!EditorApplication.isPlaying){if(EditorApplication.timeSinceStartup-RuntimeStart>30)throw new Exception("PlayMode did not start");return;}var expected=JsonUtility.FromJson<Expected>(File.ReadAllText(Arg("-b02Expected")));var root=GameObject.Find(expected.assetId);var animator=root.GetComponent<Animator>();var cam=UnityEngine.Object.FindFirstObjectByType<Camera>();
  if(TransitionIndex>=-1){TickTransitions(root,animator,cam);return;}
  if(RuntimeIndex<0){RuntimeIndex=0;animator.Play(RuntimeClips[0].name,0,0);RuntimeStart=EditorApplication.timeSinceStartup;return;}double elapsed=EditorApplication.timeSinceStartup-RuntimeStart;
  if(elapsed>.15&&RuntimeFirst==null){RuntimeFirst=Bake(root);RuntimeCurrent=new RuntimeClipResult{name=RuntimeClips[RuntimeIndex].name,firstNormalizedTime=animator.GetCurrentAnimatorStateInfo(0).normalizedTime,animatorInitialized=animator.isInitialized,finite=RuntimeFirst.All(Finite)};}
  if(elapsed>Math.Max(.5,RuntimeClips[RuntimeIndex].length*.65)){
   var now=Bake(root);RuntimeCurrent.lastNormalizedTime=animator.GetCurrentAnimatorStateInfo(0).normalizedTime;RuntimeCurrent.maxVertexMotionMeters=Delta(RuntimeFirst,now);RuntimeCurrent.finite&=now.All(Finite);RuntimeResults.Add(RuntimeCurrent);if(!RuntimeCurrent.animatorInitialized||!RuntimeCurrent.finite||RuntimeCurrent.lastNormalizedTime<=RuntimeCurrent.firstNormalizedTime||RuntimeCurrent.maxVertexMotionMeters<.00005f)RuntimeErrors.Add("Runtime motion did not advance: "+RuntimeCurrent.name);FullCamera(cam);Capture(cam,Path.Combine(RuntimeOutput,RuntimeCurrent.name+"_playmode.png"),900,900);GameCamera(cam);Capture(cam,Path.Combine(RuntimeOutput,RuntimeCurrent.name+"_playmode16m.png"),1280,720);
   RuntimeIndex++;if(RuntimeIndex>=RuntimeClips.Length){TransitionIndex=-1;animator.Play("idle",0,0);RuntimeStart=EditorApplication.timeSinceStartup;return;}RuntimeFirst=null;animator.Play(RuntimeClips[RuntimeIndex].name,0,0);RuntimeStart=EditorApplication.timeSinceStartup;
  }
 }catch(Exception e){RuntimeErrors.Add(e.ToString());FinishRuntime();}}
 static void TickTransitions(GameObject root,Animator animator,Camera cam){
  double now=EditorApplication.timeSinceStartup;
  if(TransitionIndex==-1){if(now-RuntimeStart<.4)return;TransitionIndex=0;StartTransition(root,animator);return;}
  double elapsed=now-RuntimeStart;
  if(now-LastTransitionSample>=1.0/60){var pts=Bake(root);CurrentTransition.finite&=pts.All(Finite);var min=pts.Aggregate(Vector3.Min);var max=pts.Aggregate(Vector3.Max);CurrentTransition.finite&=(max-min).magnitude<5;if(PreviousTransitionPoints!=null)CurrentTransition.maxFrameStepMeters=Mathf.Max(CurrentTransition.maxFrameStepMeters,Delta(PreviousTransitionPoints,pts));PreviousTransitionPoints=pts;CurrentTransition.samples++;LastTransitionSample=now;}
  double[] captureTimes={.04,.10,.18,.28,.45};if(TransitionCapture<captureTimes.Length&&elapsed>=captureTimes[TransitionCapture]){FullCamera(cam);Capture(cam,Path.Combine(RuntimeOutput,"transitions",CurrentTransition.from+"_to_"+CurrentTransition.to+"_"+TransitionCapture.ToString("D2")+".png"),768,768);GameCamera(cam);Capture(cam,Path.Combine(RuntimeOutput,"transitions16m",CurrentTransition.from+"_to_"+CurrentTransition.to+"_"+TransitionCapture.ToString("D2")+".png"),1280,720);TransitionCapture++;CurrentTransition.captureCount++;}
  if(elapsed>.65){CurrentTransition.reachedTarget=animator.GetCurrentAnimatorStateInfo(0).shortNameHash==Animator.StringToHash(CurrentTransition.to)&&!animator.IsInTransition(0);TransitionResults.Add(CurrentTransition);if(!CurrentTransition.finite||!CurrentTransition.reachedTarget||CurrentTransition.samples<2)RuntimeErrors.Add("Transition finite/target/sample failure: "+CurrentTransition.from+" -> "+CurrentTransition.to);TransitionIndex++;if(TransitionIndex>=TransitionStates.Length-1){FinishRuntime();return;}StartTransition(root,animator);}
 }
 static void StartTransition(GameObject root,Animator animator){CurrentTransition=new TransitionResult{from=TransitionStates[TransitionIndex],to=TransitionStates[TransitionIndex+1]};PreviousTransitionPoints=Bake(root);TransitionCapture=0;RuntimeStart=LastTransitionSample=EditorApplication.timeSinceStartup;animator.CrossFadeInFixedTime(CurrentTransition.to,.2f,0,0);}
 static void FinishRuntime(){EditorApplication.update-=RuntimeTick;var report=new RuntimeReport{status=RuntimeErrors.Count==0?"passed-actual-playmode-animator-and-crossfades":"failed",actualPlayMode=EditorApplication.isPlaying,clips=RuntimeResults.ToArray(),transitions=TransitionResults.ToArray(),errors=RuntimeErrors.ToArray()};File.WriteAllText(Path.Combine(RuntimeOutput,"playmode-report.json"),JsonUtility.ToJson(report,true)+"\n");EditorApplication.Exit(RuntimeErrors.Count==0?0:1);}
}
