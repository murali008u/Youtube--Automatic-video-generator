import requests
import json
from typing import Dict, Any
from core.config import settings

def generate_script(topic: str) -> Dict[str, Any]:
    url = f"{settings.OLLAMA_HOST}/api/generate"
    
    prompt = f"""
    You are an expert viral YouTube Shorts script writer and historical consultant.
    Write a detailed, high-retention 60-second YouTube Shorts video script about the following topic: "{topic}".
    
    CRITICAL INSTRUCTION: The total narration word count across all scenes MUST be exactly between 130 and 150 words. This ensures the audio tracks perfectly to a 60-second Short limit.
    
    EMOTIVE NARRATION RULES:
    The narration MUST be highly emotive, deeply human, and perfectly tailored to the core concept of the story. 
    - If the story is tragic, use somber, reflective, and heavy language. 
    - If it's an epic victory, use triumphant, energetic, and powerful words.
    - If it's mysterious, build suspense and intrigue.
    CONNECT with the audience emotionally. Make them feel the weight of the history. Speak directly to human emotions rather than just listing dry facts.
    
    TOPIC HOOK RULE (CRITICAL):
    Scene 1's narration MUST explicitly announce the TOPIC of the video to hook the audience immediately before beginning the actual story. Do not bury the topic in later scenes.
    
    You MUST output valid JSON ONLY. Do not write any markdown formatting, just the raw JSON object.
    
    The JSON object must strictly match this structure:
    {{
        "title": "A catchy YouTube video title",
        "description": "A short, engaging description for the video with keywords",
        "scenes": [
            {{
                "scene_number": 1,
                "narration": "The exact words the voiceover will say.",
                "image_prompt": "A highly detailed, historically accurate photorealistic cinematic prompt. Specify exact clothing, armor, architecture, lighting, and camera angles.",
                "estimated_duration_seconds": 10
            }}
        ]
    }}
    
    Make the video engaging, fast-paced, and optimized for audience retention. Include exactly 8 to 10 short scenes. 
    IMPORTANT: Write ONLY ONE concise sentence of narration per scene to ensure the images change rapidly and sync well with the audio.
    CRITICAL SPELLING: You must use absolutely perfect grammar, punctuation, and spelling for the 'narration' text.
    
    CRITICAL IMAGE ACCURACY RULES: 
    1. The 'image_prompt' MUST be specifically visualized for a vertical 9:16 layout.
    2. Make it indistinguishable from a real-life, high-quality photograph (use keywords: masterpiece, best quality, ultra-detailed, 8k resolution, photorealistic, cinematic lighting, 85mm lens). Do NOT use words like illustration, cartoon, or painting.
    3. THE PROMPT MUST BE STRICTLY TIED TO THE SUBJECT OF THE NARRATION. Always include the explicit SUBJECT of the story in the prompt so the AI model knows exactly what it's looking at (e.g., if the story is about the Chola Kingdom, explicitly put "ancient Chola Indian king", "Chola empire architecture"). Do not assume the model knows the context of previous scenes.
    4. Generate the image prompt based ON THAT SPECIFIC TIMELINE. If the story is set in ancient times (like Ancient Chola or Rome), you MUST NOT include any modern items (no guns, modern vehicles, wristwatches, or modern buildings). If the story is set in modern times, modern items are appropriate.
    5. The prompt MUST BE A COMMA-SEPARATED LIST OF TAGS, NOT FULL SENTENCES. Write the prompt exactly as a Stable Diffusion expert would (e.g., "ancient Chola king, bronze crown, holding sword, standing in ancient indian stone temple courtyard, intricate stone carvings, masterpiece, 8k resolution, dramatic lighting, highly detailed").
    6. Always ensure the focal point (person, object, or location) is explicitly described with high-quality descriptors (e.g., "intricate details," "sharp focus," "vibrant natural colors").
    """
    
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        print("Sending prompt to Ollama (this may take a few minutes on local hardware)...")
        # Increase timeout for local generation on slower hardware
        response = requests.post(url, json=payload, timeout=600)
        response.raise_for_status()
        
        result_text = response.json().get("response", "")
        
        # Parse the JSON response
        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            print(f"Failed to parse LLM output as JSON:\n{result_text}")
            return None
            
    except requests.exceptions.Timeout:
        print("Error: Ollama generation timed out after 10 minutes. The model might be too heavy for your hardware.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return None
