import requests
import json
import base64
import os
import time
import urllib.parse
from pathlib import Path
import sys


root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from db.models import Script
from dotenv import load_dotenv

load_dotenv()

COMFY_HOST = "http://127.0.0.1:8188" # Default ComfyUI API host

OUTPUT_DIR = Path("output")

def create_output_dir(script_id: int) -> Path:
    script_dir = OUTPUT_DIR / f"script_{script_id}" / "images"
    script_dir.mkdir(parents=True, exist_ok=True)
    return script_dir

def get_default_checkpoint():
    try:
        response = requests.get(f"{COMFY_HOST}/object_info/CheckpointLoaderSimple", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]
            if models and len(models) > 0:
                print(f"Auto-selected ComfyUI checkpoint: {models[0]}")
                return models[0]
    except Exception as e:
        print(f"Failed to get checkpoint info from ComfyUI: {e}. Using default.")
    return "v1-5-pruned-emaonly.safetensors"

def generate_sd_image(prompt: str, output_path: str, seed: int = -1) -> bool:
    short_prompt = prompt[:50] if len(prompt) > 50 else prompt
    print(f"Generating image via ComfyUI for prompt: '{short_prompt}...' -> {output_path}")
    
    ckpt_name = get_default_checkpoint()
    
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed if seed != -1 else 123456789,
                "steps": 6,
                "cfg": 1.5,
                "sampler_name": "dpmpp_sde",
                "scheduler": "karras",
                "denoise": 1,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": ckpt_name
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "batch_size": 1,
                "width": 832,
                "height": 1216
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt + ", masterpiece, best quality, ultra-detailed, 8k resolution, photorealistic, cinematic lighting, professional photography, depth of field, natural skin tones, realistic shadows, insanely detailed, vibrant colors",
                "clip": ["4", 1]
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "ugly, low resolution, blurry, text, watermark, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, username, dull colors, illustration, painting, cartoon, 3d render, anime",
                "clip": ["4", 1]
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            }
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "youtube_auto",
                "images": ["8", 0]
            }
        }
    }
    
    try:
        # 1. Queue the prompt
        p = {"prompt": workflow}
        # Increase timeout if the genration is slow in you machine. 
        # ComfyUI can sometimes take a while to respond to the initial prompt submission, especially if it needs to load a large model into memory.
        response = requests.post(f"{COMFY_HOST}/prompt", json=p, timeout=300)
        response.raise_for_status()
        prompt_id = response.json()['prompt_id']
        
        # 2. Wait for completion
        print(f"Queued ComfyUI prompt ID: {prompt_id}. Waiting for image to render...")
        while True:
            # Increased timeout to 60s because sometimes the Comfy node blocks the main thread
            history_res = requests.get(f"{COMFY_HOST}/history/{prompt_id}", timeout=60)
            if history_res.status_code == 200:
                history = history_res.json()
                if prompt_id in history:
                    # Generation completed
                    outputs = history[prompt_id].get("outputs", {})
                    # Find SaveImage node (id 9)
                    if "9" in outputs and "images" in outputs["9"]:
                        image_info = outputs["9"]["images"][0]
                        filename = image_info["filename"]
                        subfolder = image_info["subfolder"]
                        folder_type = image_info["type"]
                        
                        img_url = f"{COMFY_HOST}/view?filename={urllib.parse.quote(filename)}&subfolder={urllib.parse.quote(subfolder)}&type={folder_type}"
                        
                        # Added robust retry loop for downloading because ComfyUI often marks
                        # history jobs as 'completed' milliseconds before the file is actually available
                        for attempt in range(10):
                            try:
                                img_res = requests.get(img_url, timeout=30)
                                if img_res.status_code == 200:
                                    with open(output_path, "wb") as f:
                                        f.write(img_res.content)
                                    print(f"Successfully generated and downloaded image via ComfyUI at {output_path}")
                                    return True
                            except Exception as e:
                                print(f"Download attempt {attempt+1} failed: {e}. Retrying...")
                                time.sleep(2)
                                
                        print(f"Failed to download image {filename} from ComfyUI after 10 attempts.")
                        break
            time.sleep(2)
            
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with ComfyUI API: {e}")
        # Create a valid placeholder image using PIL so MoviePy does not crash
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (1080, 1920), color = (73, 109, 137))
            d = ImageDraw.Draw(img)
            d.text((50,960), "IMAGE GENERATION FAILED", fill=(255,255,0))
            img.save(output_path)
            print(f"Created fallback placeholder image at {output_path}")
            return True # Return true so the video can still render with placeholders
        except Exception as inner_e:
            print(f"Failed to create fallback image: {inner_e}")
            return False

    return False

def generate_script_images(script: Script) -> bool:
    print(f"Starting image generation for Script {script.id}: {script.title}")
    
    output_dir = create_output_dir(script.id)
    scene_image_files = []
    
    # Use a consistent seed for recurring characters if desired
    base_seed = hash(script.title) % 1000000 
    
    for scene in sorted(script.scenes, key=lambda s: s.scene_number):
        if not scene.image_prompt:
            continue
            
        scene_file = str(output_dir / f"scene_{scene.scene_number:03d}.png")
        # Ensure we pass the seed through correctly
        success = generate_sd_image(scene.image_prompt, scene_file, seed=base_seed + scene.scene_number)
        
        if success:
            scene_image_files.append(scene_file)
            
    if not scene_image_files:
        print("No scene image files were generated.")
        return False
        
    return True
