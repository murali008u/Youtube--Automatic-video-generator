from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from services.images import generate_sd_image
from db.models import Script

OUTPUT_DIR = Path("output")

def create_output_dir(script_id: int) -> Path:
    script_dir = OUTPUT_DIR / f"script_{script_id}"
    script_dir.mkdir(parents=True, exist_ok=True)
    return script_dir

def generate_thumbnail(script: Script) -> str:
    print(f"Starting thumbnail generation for Script {script.id}: {script.title}")
    
    script_dir = create_output_dir(script.id)
    base_image_path = str(script_dir / "thumbnail_base.png")
    final_output = str(script_dir / "thumbnail_final.jpg")
    
    # Try to grab the first scene's image prompt for maximum relevance to the story
    context_prompt = script.scenes[0].image_prompt if script.scenes and len(script.scenes) > 0 and script.scenes[0].image_prompt else "Epic cinematic hero shot, central subject in focus"
    
    # 1. Generate dramatic base image
    prompt = f"YouTube thumbnail background for: {script.title}. {context_prompt[:150]}. vibrant colors, clear background, professional photography, natural lighting."
    success = generate_sd_image(prompt, base_image_path)
    
    if not success:
        print("Failed to generate base thumbnail image via SD.")
        return ""
        
    try:
        # Open base image
        img = Image.open(base_image_path).convert("RGBA")
        
        # 2. Add dramatic color grade / vignette
        vignette = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw_vignette = ImageDraw.Draw(vignette)
        # Create a basic vignette effect natively in PIL via a dark semi-transparent rectangle we blur
        draw_vignette.rectangle([0, 0, img.width, img.height], outline=(0, 0, 0, 200), width=100)
        vignette = vignette.filter(ImageFilter.GaussianBlur(50))
        
        img = Image.alpha_composite(img, vignette)
        
        # 3. Add bold text overlay
        draw = ImageDraw.Draw(img)
        
        # Try to load a bold font, fallback to default
        try:
            # Arial Black is usually available on Windows or you can specify a path to a bold TTF font file
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 50)
        except IOError:
            print("Warning: Bold font not found, using default.")
            font = ImageFont.load_default()
            
        # Get a short hook version of the title (first 3-4 words)
        words = script.title.split()
        hook_text = " ".join(words[:4]).upper() + ("!" if not words[0].endswith("!") else "")
        
        # Dynamically scale font size so it fits inside the image width with padding
        target_width = img.width - 200 # Leave 100px padding on each side
        
        # Start at 180 and tick down until it fits
        font_size = 180
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
        left, top, right, bottom = draw.textbbox((0, 0), hook_text, font=font)
        text_width = right - left
        
        while text_width > target_width and font_size > 50:
            font_size -= 10
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
            left, top, right, bottom = draw.textbbox((0, 0), hook_text, font=font)
            text_width = right - left
            
        text_height = bottom - top
        
        # Position at the center-bottom of the thumbnail
        x = (img.width - text_width) / 2
        y = (img.height - text_height) - 100
        
        # Add a thick black stroke (outline) for high visibility
        stroke_width = 15
        stroke_fill = "black"
        
        # Draw main text in bright yellow or white
        draw.text(
            (x, y), 
            hook_text, 
            font=font, 
            fill="yellow", 
            stroke_width=stroke_width, 
            stroke_fill=stroke_fill
        )
        
        # Save final result as high quality JPG
        final_img = img.convert("RGB")
        final_img.save(final_output, "JPEG", quality=95)
        
        print(f"Thumbnail successfully generated: {final_output}")
        return final_output
        
    except Exception as e:
        print(f"Error drawing text on thumbnail: {e}")
        return ""
