// One art-side A03 locomotion proof. Scripted trajectory, not the game's controller.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;

public static class MaleLocomotionFitMotionCheck
{
    const int Fps = 24, Frames = 240;
    const float Dt = 1f / Fps;
    [Serializable] public class FrameRow {
        public int frame; public float time,commandedSpeed,measuredRootSpeed,headingDegrees,yawDegreesPerSecond;
        public string scenario,state; public bool transition;
        public float normalizedTime,minFootY,stableGroundContactMaxMps,groundedCentreMaxMps;
        public int stableGroundContactVertexPairs; public float[] root;
    }
    [Serializable] public class ClipRow {public string name; public float seconds; public bool loop; public int curves;}
    [Serializable] public class Report {
        public string schema="a03-locomotion-fit-unity-motion-1",status,unityVersion;
        public bool actualPlayMode,manualFixedStepAnimator=true,gameControllerUsed=false,rootMotion=false,oldTurnUsed=false;
        public int fps=Fps,frames; public float runSpeed=4,turnDegreesPerSecond=720,startFadeSeconds=.08f,stopFadeSeconds=.08f;
        public ClipRow[] clips; public FrameRow[] samples; public string[] errors,limitations;
    }
    static string Output;
    static GameObject Root; static Animator Anim; static Camera Cam;
    static AnimationClip[] Clips; static SkinnedMeshRenderer Sole;
    static int[] GroundIds; static Vector3[] PreviousFeet;
    static readonly List<FrameRow> Rows = new List<FrameRow>();
    static readonly List<string> Errors = new List<string>();
    static int Index; static string State="idle"; static double Start;
    static Vector3 LastRoot; static float LastHeading;
    static string Arg(string key){var a=Environment.GetCommandLineArgs();for(int i=0;i+1<a.Length;i++)if(a[i]==key)return a[i+1];throw new Exception("Missing "+key);}
    static Transform Joint(string name)=>Root.GetComponentsInChildren<Transform>(true).First(t=>t.name==name);

    public static void Run() {
        Output=Arg("-fitOutput"); Directory.CreateDirectory(Output);
        try {
            EditorSceneManager.OpenScene("Assets/LocomotionFitAnimationProbe.unity",OpenSceneMode.Single);
            Root=GameObject.Find("chr_player_male_poc_001"); if(Root==null)throw new Exception("Missing saved character");
            var path="Assets/Character/chr_player_male_poc_001.glb";
            Clips=AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().OrderBy(c=>c.name).ToArray();
            if(!Clips.Select(c=>c.name).OrderBy(x=>x).SequenceEqual(new[]{"idle","run","walk"}))throw new Exception("Unexpected clip set / turn present");
            Anim=Root.GetComponent<Animator>()??Root.AddComponent<Animator>();
            var controller=AssetDatabase.LoadAssetAtPath<AnimatorController>("Assets/LocomotionFitReview.controller");
            if(controller==null){controller=AnimatorController.CreateAnimatorControllerAtPath("Assets/LocomotionFitReview.controller");
            foreach(var clip in Clips){var state=controller.layers[0].stateMachine.AddState(clip.name);state.motion=clip;state.writeDefaultValues=false;if(clip.name=="idle")controller.layers[0].stateMachine.defaultState=state;}}
            Anim.runtimeAnimatorController=controller; Anim.applyRootMotion=false;Anim.cullingMode=AnimatorCullingMode.AlwaysAnimate;
            // No automatic update in addition to the explicit fixed 24Hz evaluation.
            Anim.enabled=false; Anim.speed=1;
            foreach(var r in Root.GetComponentsInChildren<SkinnedMeshRenderer>(true)){r.updateWhenOffscreen=true;r.forceMatrixRecalculationPerRender=true;r.quality=SkinQuality.Bone4;}
            Sole=Root.GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r=>r.name=="M01_shoes_bottom");
            GroundIds=Sole.sharedMesh.vertices.Select((v,i)=>new{v,i}).Where(x=>x.v.y<.004f).Select(x=>x.i).ToArray();
            if(GroundIds.Length<100)throw new Exception("No sole patch");
            Cam=UnityEngine.Object.FindFirstObjectByType<Camera>();
            if(GameObject.Find("ReviewGround_1mGrid")==null)MakeFloor();Root.transform.SetPositionAndRotation(Vector3.zero,Quaternion.identity);
            EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());AssetDatabase.SaveAssets();
            EditorSettings.enterPlayModeOptionsEnabled=true;EditorSettings.enterPlayModeOptions=EnterPlayModeOptions.DisableDomainReload;
            EditorApplication.update+=Tick; Start=EditorApplication.timeSinceStartup;EditorApplication.EnterPlaymode();
        } catch(Exception e){Errors.Add(e.ToString());Finish();}
    }

    static void MakeFloor(){
        var floor=GameObject.CreatePrimitive(PrimitiveType.Plane);floor.name="ReviewGround_1mGrid";floor.transform.position=new Vector3(0,-.002f,0);floor.transform.localScale=new Vector3(6,1,6);
        var tex=new Texture2D(128,128,TextureFormat.RGB24,true);tex.wrapMode=TextureWrapMode.Repeat;tex.filterMode=FilterMode.Trilinear;tex.anisoLevel=8;
        for(int y=0;y<128;y++)for(int x=0;x<128;x++){bool line=x<2||y<2;tex.SetPixel(x,y,line?new Color(.44f,.46f,.39f):new Color(.66f,.66f,.56f));}tex.Apply();AssetDatabase.CreateAsset(tex,"Assets/ReviewGrid.asset");
        var mat=new Material(Shader.Find("Universal Render Pipeline/Lit"));mat.name="ReviewGround";mat.SetTexture("_BaseMap",tex);mat.mainTextureScale=new Vector2(60,60);mat.SetFloat("_Smoothness",.05f);AssetDatabase.CreateAsset(mat,"Assets/ReviewGround.mat");floor.GetComponent<Renderer>().sharedMaterial=mat;
        UnityEngine.Object.DestroyImmediate(floor.GetComponent<Collider>());
        foreach(var light in UnityEngine.Object.FindObjectsByType<Light>(FindObjectsSortMode.None))if(light.type==LightType.Directional){light.shadows=LightShadows.Soft;light.shadowStrength=.5f;}
    }
    static void Command(float t,out float speed,out float yaw,out string label,out string state){
        yaw=0;speed=0;state="idle";label="idle";
        if(t>=1&&t<3){speed=4;state="run";label="straight4";}
        else if(t>=3&&t<3.7f){label="stop1";}
        else if(t>=3.7f&&t<5){speed=4;state="run";label="restart4";}
        else if(t>=5&&t<5.6f){speed=4;yaw=90;state="run";label="right90_720";}
        else if(t>=5.6f&&t<6.2f){speed=4;yaw=-90;state="run";label="reverse180_720";}
        else if(t>=6.2f&&t<7){speed=4;state="run";label="forward90_720";}
        else if(t>=7&&t<7.8f){label="stop2";}
        else if(t>=7.8f&&t<9){speed=1.4f;state="walk";label="walk1p4";}
        else if(t>=9){label="walkStop";}
    }
    static Vector3[] Feet(){var m=new Mesh();Sole.BakeMesh(m);var result=GroundIds.Select(i=>Sole.transform.TransformPoint(m.vertices[i])).ToArray();UnityEngine.Object.DestroyImmediate(m);return result;}
    static void FrameCamera(bool game){
        var focus=Root.transform.position+Vector3.up*.875f;
        Cam.orthographic=!game;
        if(game){Cam.fieldOfView=40;Cam.transform.position=focus+new Vector3(0,16*Mathf.Sin(50*Mathf.Deg2Rad),16*Mathf.Cos(50*Mathf.Deg2Rad));}
        else{Cam.orthographicSize=1.35f;Cam.transform.position=focus+new Vector3(-2.8f,.25f,4);}
        Cam.transform.LookAt(focus);Cam.farClipPlane=120;
    }
    static void Tick(){
        try {
            if(!EditorApplication.isPlaying){if(EditorApplication.timeSinceStartup-Start>45)throw new Exception("PlayMode did not start");return;}
            if(Index==0){
                Root=GameObject.Find("chr_player_male_poc_001");Anim=Root.GetComponent<Animator>();Anim.enabled=false;Anim.Rebind();Anim.Play("idle",0,0);Anim.Update(0);
                Sole=Root.GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r=>r.name=="M01_shoes_bottom");Cam=UnityEngine.Object.FindFirstObjectByType<Camera>();LastRoot=Root.transform.position;LastHeading=Root.transform.eulerAngles.y;
            }
            float t=Index*Dt; Command(t,out float speed,out float targetYaw,out string label,out string desiredState);
            if(desiredState!=State){Anim.CrossFadeInFixedTime(desiredState,.08f,0,0);State=desiredState;}
            float heading=Mathf.MoveTowardsAngle(Root.transform.eulerAngles.y,targetYaw,720*Dt);
            Root.transform.rotation=Quaternion.Euler(0,heading,0);
            // Fixed controller command: immediate speed, travel along desired input,
            // visual heading catches up at720deg/s. No acceleration/foot locking.
            Root.transform.position+=Quaternion.Euler(0,targetYaw,0)*Vector3.forward*speed*Dt;
            Anim.Update(Dt);
            var points=MaleLocomotionFitImportCheck.Bake(Root);
            if(points.Length==0||points.Any(v=>!MaleLocomotionFitImportCheck.Finite(v)))throw new Exception("Nonfinite skin");
            var feet=Feet();var info=Anim.GetCurrentAnimatorStateInfo(0);
            var row=new FrameRow{frame=Index,time=t,scenario=label,state=State,transition=Anim.IsInTransition(0),normalizedTime=info.normalizedTime,commandedSpeed=speed,measuredRootSpeed=Vector3.Distance(Root.transform.position,LastRoot)/Dt,headingDegrees=heading,yawDegreesPerSecond=Mathf.Abs(Mathf.DeltaAngle(LastHeading,heading))/Dt,minFootY=feet.Min(v=>v.y),root=new[]{Root.transform.position.x,Root.transform.position.y,Root.transform.position.z}};
            if(PreviousFeet!=null){
                for(int j=0;j<feet.Length;j++)if(feet[j].y<=.003f&&PreviousFeet[j].y<=.003f){row.stableGroundContactVertexPairs++;row.stableGroundContactMaxMps=Mathf.Max(row.stableGroundContactMaxMps,Vector2.Distance(new Vector2(feet[j].x,feet[j].z),new Vector2(PreviousFeet[j].x,PreviousFeet[j].z))/Dt);}
            }
            if(row.yawDegreesPerSecond>720.01f||Mathf.Abs(row.measuredRootSpeed-speed)>.001f)throw new Exception("Trajectory contract violated");
            Rows.Add(row);PreviousFeet=feet;LastRoot=Root.transform.position;LastHeading=heading;
            FrameCamera(false);MaleLocomotionFitImportCheck.Capture(Cam,Path.Combine(Output,"frames","full","frame_"+Index.ToString("D4")+".png"),960,720);
            FrameCamera(true);MaleLocomotionFitImportCheck.Capture(Cam,Path.Combine(Output,"frames","game16m","frame_"+Index.ToString("D4")+".png"),1280,720);
            if(new[]{18,36,48,64,72,76,96,121,125,136,140,151,156,168,172,192,216,222}.Contains(Index)){
                foreach(var side in new[]{"L","R"}){
                    var target=Joint("LowerArm."+side).position;Cam.orthographic=true;Cam.orthographicSize=.21f;Cam.transform.position=target+new Vector3(side=="L"?-.6f:.6f,.18f,.8f);Cam.transform.LookAt(target);
                    MaleLocomotionFitImportCheck.Capture(Cam,Path.Combine(Output,"closeups","elbow_"+side+"_"+Index.ToString("D4")+".png"),640,640);
                }
                var targetFoot=(Joint("Foot.L").position+Joint("Foot.R").position)*.5f;Cam.orthographic=true;Cam.orthographicSize=.65f;Cam.transform.position=targetFoot+new Vector3(-2,.65f,1);Cam.transform.LookAt(targetFoot);
                MaleLocomotionFitImportCheck.Capture(Cam,Path.Combine(Output,"closeups","feet_"+Index.ToString("D4")+".png"),960,640);
            }
            Index++;if(Index>=Frames)Finish();
        }catch(Exception e){Errors.Add(e.ToString());Finish();}
    }
    static void Finish(){
        EditorApplication.update-=Tick;
        var report=new Report{status=Errors.Count==0&&Index==Frames?"passed-art-playmode-trajectory-capture":"failed",actualPlayMode=EditorApplication.isPlaying,unityVersion=Application.unityVersion,frames=Index,samples=Rows.ToArray(),clips=Clips?.Select(c=>new ClipRow{name=c.name,seconds=c.length,curves=AnimationUtility.GetCurveBindings(c).Length,loop=AnimationUtility.GetAnimationClipSettings(c).loopTime}).ToArray(),errors=Errors.ToArray(),limitations=new[]{"Actual art-only PlayMode; deterministic manual Animator.Update at24Hz with auto update disabled. Not OS input or the real game controller.","Root speed changes immediately. Pose crossfades only; no root easing, foot locking, braking clip, lean or turn clip.","1m ground grid; full and50deg/16m cameras follow translation with fixed world offsets. VerticalFOV40deg. Not Neighborhood lighting.","Stable-contact metric tracks same sole vertices within3mm floor in adjacent frames; foot roll, transitions and turns remain separately reviewable. No terrain/physics test.","B02 elbow/hand/knee limitations retained. No close-up quality approval."}};
        Directory.CreateDirectory(Output);File.WriteAllText(Path.Combine(Output,"motion-report.json"),JsonUtility.ToJson(report,true)+"\n");
        EditorApplication.Exit(Errors.Count==0&&Index==Frames?0:1);
    }
}
