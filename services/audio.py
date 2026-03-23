import os
import subprocess
from pathlib import Path
from db.models import Script

# Paths for Piper executable and voice model and output directory. These can be overridden by environment variables for flexibility.
PIPER_EXECUTABLE = os.environ.get("PIPER_EXECUTABLE", str(Path(__file__).parent.parent / "piper" / "piper.exe"))
PIPER_VOICE = os.environ.get("PIPER_VOICE", str(Path(__file__).parent.parent / "piper" / "en_US-ryan-medium.onnx"))
OUTPUT_DIR = Path("output")

def create_output_dir(script_id: int) -> Path:
    script_dir = OUTPUT_DIR / f"script_{script_id}" / "audio"
    script_dir.mkdir(parents=True, exist_ok=True)
    return script_dir

def generate_scene_audio(text: str, output_path: str):
    print(f"Generating Piper audio for text: '{text[:30]}...' -> {output_path}")
    
    try:
        # Run Piper executable via subprocess
        # We pass the text via stdin
        cmd = [
            PIPER_EXECUTABLE,
            "--model", PIPER_VOICE,
            "--output_file", output_path
        ]
        
        # We need to explicitly encode text to UTF-8 to prevent charmap errors on Windows
        encoded_text = text.encode('utf-8')
        
        process = subprocess.run(
            cmd, 
            input=encoded_text, 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        if os.path.exists(output_path):
            print(f"Successfully generated Piper audio at {output_path}")
            return True
        else:
            print(f"Piper failed to write file to {output_path}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate audio via Piper: Process error {e}")
        print("Ensure 'piper.exe' exists and the onnx model is valid.")
        return False
    except Exception as e:
        print(f"Failed to generate audio via Piper: {e}")
        return False

def merge_audio_files(input_files: list[str], output_file: str):
    if not input_files:
        return False
        
    print(f"Merging {len(input_files)} audio files into {output_file}...")
    
    # Create a list file for ffmpeg
    list_file_path = Path(output_file).parent / "concat_list.txt"
    with open(list_file_path, "w") as f:
        for audio_file in input_files:
            # Format required by ffmpeg concat demuxer: file 'path/to/file'
            f.write(f"file '{Path(audio_file).absolute().as_posix()}'\n")
            
    try:
        # Run ffmpeg to concatenate
        cmd = [
            str(Path(__file__).parent.parent / "ffmpeg_extracted" / "ffmpeg-master-latest-win64-gpl" / "bin" / "ffmpeg.exe"), 
            "-y", "-f", "concat", "-safe", "0", 
            "-i", str(list_file_path), 
            "-c", "copy", output_file
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Successfully merged audio to {output_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to merge audio files using ffmpeg: {e}")
        print("Ensure ffmpeg is installed and in your system PATH.")
        return False
    except FileNotFoundError:
        print("ffmpeg command not found. Ensure it is installed and in your system PATH.")
        return False
    finally:
        # Cleanup the list file
        if list_file_path.exists():
            list_file_path.unlink()
            
    return os.path.exists(output_file)

def generate_script_audio(script: Script) -> bool:
    print(f"Starting audio generation for Script {script.id}: {script.title}")
    
    output_dir = create_output_dir(script.id)
    scene_audio_files = []
    
    for scene in sorted(script.scenes, key=lambda s: s.scene_number):
        if not scene.narration_text:
            continue
            
        scene_file = str(output_dir / f"scene_{scene.scene_number:03d}.wav")
        success = generate_scene_audio(scene.narration_text, scene_file)
        
        if success:
            scene_audio_files.append(scene_file)
            
    if not scene_audio_files:
        print("No scene audio files were generated.")
        return False
        
    final_output = str(output_dir / "final_narration.wav")
    success = merge_audio_files(scene_audio_files, final_output)
    
    return success
