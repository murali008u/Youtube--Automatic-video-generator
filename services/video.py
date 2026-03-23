import os
from pathlib import Path

# Add our downloaded ffmpeg to the system PATH so moviepy can find it
ffmpeg_bin_dir = str((Path(__file__).parent.parent / "ffmpeg_extracted" / "ffmpeg-master-latest-win64-gpl" / "bin").absolute())
if ffmpeg_bin_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{ffmpeg_bin_dir};{os.environ.get('PATH', '')}"
    
# Import moviepy dynamically after PATH is updated so it detects our custom ffmpeg
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from db.models import Script

OUTPUT_DIR = Path("output")

def zoom_in_effect(clip, zoom_ratio=0.04):
    """Adds a basic ken-burns zoom-in effect to a MoviePy clip"""
    def effect(get_frame, t):
        img = get_frame(t)
        base_size = img.shape[0:2]
        
        # Calculate current zoom factor
        progress = t / clip.duration
        zoom = 1.0 + (zoom_ratio * progress)
        
        # We handle this manually since MoviePy 2.0 changes some fx functions
        import numpy as np
        from PIL import Image
        
        pil_img = Image.fromarray(img)
        w, h = pil_img.size
        
        # Calculate cropped dimensions
        new_w = int(w / zoom)
        new_h = int(h / zoom)
        
        left = (w - new_w) / 2
        top = (h - new_h) / 2
        right = (w + new_w) / 2
        bottom = (h + new_h) / 2
        
        cropped = pil_img.crop((left, top, right, bottom))
        resized = cropped.resize((w, h), Image.Resampling.LANCZOS)
        
        return np.array(resized)
    
    return clip.transform(effect)

def create_padded_text_clip(text, font_path="C:/Windows/Fonts/arialbd.ttf", font_size=70, 
                            color="yellow", stroke_color="black", stroke_width=4, padding=20):
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    from moviepy import ImageClip
    
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate bounding box safely for older and newer Pillow versions
    try:
        left, top, right, bottom = font.getbbox(text)
    except AttributeError:
        # Fallback for very old Pillow
        width, height = font.getsize(text)
        left, top, right, bottom = 0, 0, width, height
    
    # Text bounds include the bbox and font metrics
    try:
        ascent, descent = font.getmetrics()
    except Exception:
        ascent, descent = (bottom, 0)
        
    text_width = (right - left) + (stroke_width * 2)
    # Give plenty of room for both top/bottom accents (descenders like j, g, y)
    text_height = (bottom - top) + (stroke_width * 2) + descent + padding
    
    img_width = text_width + (padding * 2)
    img_height = text_height + (padding * 2)
    
    # Create image with transparent background
    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    
    # Center text perfectly in our box
    x = padding + stroke_width - left
    y = padding + stroke_width - top
    
    d.text((x, y), text, font=font, fill=color, stroke_width=stroke_width, stroke_fill=stroke_color)
    
    # Convert PIL Image to numpy array for MoviePy
    np_img = np.array(img)
    clip = ImageClip(np_img)
    return clip

def create_subtitle_clips(text, duration=5.0, video_size=(1080, 1920)):
    # Split text into bite-sized chunks
    words = text.split()
    chunks = []
    chunk_size = 2
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
        
    if not chunks:
        return []
        
    # Calculate duration per chunk so it syncs with the audio duration
    chunk_duration = duration / len(chunks)
    
    text_clips = []
    
    # Calculate Y pos: roughly 75% down the screen, leaving room for shorts 
    y_pos = int(video_size[1] * 0.75) if video_size else 1250

    for i, chunk in enumerate(chunks):
        try:
            #use our custom Pillow text renderer to avoid MoviePy TextClip bounding box clipping issues
            txt_clip = create_padded_text_clip(
                text=chunk.upper(),
                font_path="C:/Windows/Fonts/arialbd.ttf", 
                font_size=70, 
                color="yellow", 
                stroke_color="black", 
                stroke_width=4,
                padding=20
            )
        except Exception as e:
            from moviepy import TextClip
            print(f"Pillow Subtitle font error: {e}. Attempting unstyled TextClip fallback.")
            txt_clip = TextClip(
                text=chunk.upper(), 
                font_size=50, 
                color="yellow", 
                stroke_color="black", 
                stroke_width=3
            )
            
        # Position slightly above the shorts .
        txt_clip = txt_clip.with_position(("center", y_pos))
        # Set the start time and duration for this specific word chunk
        txt_clip = txt_clip.with_start(i * chunk_duration).with_duration(chunk_duration)
        text_clips.append(txt_clip)
        
    # Return the flat list of clips so they composite naturally with a transparent background
    return text_clips

def render_video(script: Script) -> str:
    print(f"Starting video rendering for Script {script.id}: {script.title}")
    
    script_dir = OUTPUT_DIR / f"script_{script.id}"
    audio_dir = script_dir / "audio"
    images_dir = script_dir / "images"
    final_output = script_dir / f"final_video_{script.id}.mp4"
    
    if not audio_dir.exists() or not images_dir.exists():
        print(f"Missing audio or images directory for script {script.id}")
        return ""
        
    clips = []
    
    from moviepy import CompositeVideoClip
    
    for scene in sorted(script.scenes, key=lambda s: s.scene_number):
        audio_file = audio_dir / f"scene_{scene.scene_number:03d}.wav"
        image_file = images_dir / f"scene_{scene.scene_number:03d}.png"
        
        if not audio_file.exists() or not image_file.exists():
            print(f"Missing audio or image for scene {scene.scene_number}. Skipping.")
            continue
            
        print(f"Processing Scene {scene.scene_number}...")
        
        try:
            # Load audio to get its duration
            audio_clip = AudioFileClip(str(audio_file))
            duration = audio_clip.duration
            
            # Load image and set its duration to match audio
            image_clip = ImageClip(str(image_file)).with_duration(duration)
            
            # Apply Ken Burns zoom effect
            animated_clip = zoom_in_effect(image_clip)
            
            # Create a localized subtitle clip using PIL overlay
            sub_path = str(images_dir / f"sub_scene_{scene.scene_number:03d}.png")
            
            # The ORM model defines the field as 'narration_text'
            narration_word = scene.narration_text if hasattr(scene, 'narration_text') and scene.narration_text else " "
            sub_clips = create_subtitle_clips(narration_word, duration=duration, video_size=image_clip.size)
            
            # Composite video + subtitle
            if sub_clips:
                composited = CompositeVideoClip([
                    animated_clip.with_position(("center", "center")),
                    *sub_clips # Unpack the list of TextClips so they overlay correctly
                ])
            else:
                composited = animated_clip.with_position(("center", "center"))
            
            # Set audio
            final_clip = composited.with_audio(audio_clip)
            
            clips.append(final_clip)
            
        except Exception as e:
            print(f"Error processing scene {scene.scene_number}: {e}")
            
    if not clips:
        print("No valid scenes found to render.")
        return ""
        
    print(f"Concatenating {len(clips)} scenes...")
    
    # [YOUTUBE THUMBNAIL TRICK]
    # YouTube Shorts often ignores custom API thumbnails. 
    # To force a custom thumbnail, we flash the exact thumbnail image for 0.1 seconds at the very beginning of the video.
    thumbnail_file = script_dir / "thumbnail_final.jpg"
    final_clips_list = []
    
    if thumbnail_file.exists():
        print("Injecting 0.1s thumbnail flash frame at the start of the video...")
        try:
            # Create a 0.1 second clip of the thumbnail
            thumb_clip = ImageClip(str(thumbnail_file)).with_duration(0.1)
            final_clips_list.append(thumb_clip)
        except Exception as e:
            print(f"Failed to inject thumbnail frame: {e}")
            
    # Append the rest of the actual video scenes
    final_clips_list.extend(clips)
    
    try:
        # Concatenate all clips with a gentle crossfade
        # MoviePy 2 approach to crossfade involves using the proper compose/concatenate parameters
        final_video = concatenate_videoclips(final_clips_list, method="compose")
        
        print("Writing final video file using FFmpeg backend...")
        final_video.write_videofile(
            str(final_output),
            fps=60,
            bitrate="8000k",
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4
        )
        print(f"Video rendering complete: {final_output}")
        return str(final_output)
        
    except Exception as e:
        print(f"Failed to render complete video: {e}")
        return ""
    finally:
        # Ensure we close file handles
        for c in clips:
            if hasattr(c, 'close'): c.close()
