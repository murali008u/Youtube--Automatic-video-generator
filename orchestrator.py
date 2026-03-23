from db.database import SessionLocal
from services.script_manager import create_script_from_topic
from services.audio import generate_script_audio
from services.images import generate_script_images
from services.video import render_video
from services.thumbnail import generate_thumbnail
import time
import subprocess
import os

def manage_ollama(action="start"):
    if action == "start":
        print("\n[RESOURCE MANAGER] Starting Ollama...")
        subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        return subprocess.Popen("ollama serve", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif action == "stop":
        print("\n[RESOURCE MANAGER] Stopping Ollama to free system memory...")
        subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)

def manage_comfyui(action="start", proc=None):
    if action == "start":
        print("\n[RESOURCE MANAGER] Starting Local ComfyUI Server...")
        print("Waiting 30 seconds for the ComfyUI API to become available. Please be patient...")
        # ComfyUI is installed in a default location or accessible via python main.py
        # Change this path if ComfyUI is located elsewhere.
        cwd_path = r"d:\ComfyUI-master"
        
        if not os.path.exists(cwd_path):
            print(f"Warning: {cwd_path} not found. Ensure ComfyUI is already running manually!")
            return None
            
        # Often ComfyUI is run via a .bat or python main.py
        # Use the ComfyUI venv Python
        venv_python = os.path.join(cwd_path, "venv", "Scripts", "python.exe")
        if not os.path.exists(venv_python):
            print(f"Warning: Python executable not found at {venv_python}. Trying global python...")
            venv_python = "python"
            
        p = subprocess.Popen([venv_python, "main.py"], cwd=cwd_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        import urllib.request
        from urllib.error import URLError
        timeout = 180 # Wait up to 3 minutes for the heavy models to load into GPU
        start_poll = time.time()
        
        while time.time() - start_poll < timeout:
            try:
                # ComfyUI serves a basic UI at the root, so 200 means it's running
                response = urllib.request.urlopen("http://127.0.0.1:8188/", timeout=2)
                if response.getcode() == 200:
                    print(f"ComfyUI server started successfully in {int(time.time() - start_poll)} seconds!")
                    break
            except (URLError, Exception):
                pass
            time.sleep(3)
        else:
            print("Warning: ComfyUI failed to start within the 3 minute timeout. Proceeding anyway, but generations may fail.")
            
        return p
    elif action == "stop" and proc:
        print("\n[RESOURCE MANAGER] Stopping ComfyUI process tree to free VRAM...")
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
        except Exception as e:
            print(f"Failed to kill ComfyUI: {e}")

def process_video_pipeline(topic: str):
    print(f"\n{'='*50}")
    print(f"STARTING YOUTUBE AUTOMATION PIPELINE: '{topic}'")
    print(f"{'='*50}\n")
    
    db = SessionLocal()
    comfy_process = None
    try:
        # SPIN UP OLLAMA
        manage_ollama("start")
        
        # Step 1: LLM Script Generation
        print("\n--- PHASE 1: Script Generation ---")
        script = create_script_from_topic(db, topic)
        
        if not script:
            print("Pipeline Failed: Could not generate script.")
            return False
            
        print(f"Script generated successfully. Total Scenes: {len(script.scenes)}")
        
        # Keep track of the timeline for logs
        start_time = time.time()
        
        # TEAR DOWN OLLAMA
        manage_ollama("stop")
        
        # Step 2: Audio Generation
        print("\n--- PHASE 2: Audio Generation ---")
        audio_success = generate_script_audio(script)
        
        if not audio_success:
            print("Pipeline Failed: Could not generate audio.")
            return False
            
        # SPIN UP COMFYUI
        comfy_process = manage_comfyui("start")
        
        # Step 3: Image Generation
        print("\n--- PHASE 3: Image Generation ---")
        image_success = generate_script_images(script)
        
        if not image_success:
            print("Pipeline Failed: Could not generate images.")
            return False
            
        # Step 4: Thumbnail Generation
        print("\n--- PHASE 4: Thumbnail Generation ---")
        thumbnail_path = generate_thumbnail(script)
        
        if not thumbnail_path:
            print("Warning: Failed to generate thumbnail. Video will not have a custom cover frame.")
            
        # Step 5: Video Rendering
        print("\n--- PHASE 5: Video Rendering ---")
        video_path = render_video(script)
        
        if not video_path:
            print("Pipeline Failed: Could not render video.")
            return False
            
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        from services.youtube_upload import push_script_to_youtube
        
        # Step 6: YouTube Upload
        print("\n--- PHASE 6: YouTube Upload ---")
        print("\n[MANUAL REVIEW REQUIRED]")
        print(f"Watch the final video here: {video_path}")
        if thumbnail_path:
            print(f"Review the thumbnail here: {thumbnail_path}")
            
        user_input = input("\nDo you want to upload this video to YouTube? (Y/n): ")
        if user_input.strip().lower() in ['y', 'yes', '']:
            print("Proceeding with YouTube upload...")
            upload_success = push_script_to_youtube(script, video_path, thumbnail_path)
            
            if upload_success:
                print("Successfully uploaded to YouTube via API!")
                if script.videos:
                    script.videos[0].status = "uploaded"
                    db.commit()
            else:
                print("Warning: Completed video generation but failed to upload to YouTube.")
        else:
            print("Upload cancelled by user. The video is saved locally.")
        
        return True
        
    except Exception as e:
        print(f"Critical error in pipeline: {e}")
        return False
    finally:
        if comfy_process:
            manage_comfyui("stop", comfy_process)
        db.close()

if __name__ == "__main__":
    import sys
    topic = "The Rise and Fall of Ancient Rome" if len(sys.argv) < 2 else sys.argv[1]
    process_video_pipeline(topic)
