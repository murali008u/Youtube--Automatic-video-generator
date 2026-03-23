from sqlalchemy.orm import Session
from db.models import Script, Scene, Video
from services.llm import generate_script
from typing import Optional

def create_script_from_topic(db: Session, topic: str) -> Optional[Script]:
    print(f"Generating script for topic: '{topic}' via Ollama...")
    
    script_data = generate_script(topic)
    
    if not script_data:
        print("Failed to generate script data.")
        return None
        
    print(f"Script generated successfully. Title: {script_data.get('title')}")
    
    # Create the Script record
    new_script = Script(
        title=script_data.get("title", "Untitled Concept"),
        description=script_data.get("description", "")
    )
    db.add(new_script)
    db.flush() # Flush to get the ID
    
    # Create the Scene records
    scenes = script_data.get("scenes", [])
    for scene_data in scenes:
        new_scene = Scene(
            script_id=new_script.id,
            scene_number=scene_data.get("scene_number", 0),
            narration_text=scene_data.get("narration", ""),
            image_prompt=scene_data.get("image_prompt", ""),
            duration_estimate=scene_data.get("estimated_duration_seconds", 5.0)
        )
        db.add(new_scene)
        
    # Create an initial Video tracking record
    new_video = Video(
        script_id=new_script.id,
        status="script_generated"
    )
    db.add(new_video)
    
    db.commit()
    db.refresh(new_script)
    
    print(f"Saved script '{new_script.title}' with {len(scenes)} scenes to database.")
    return new_script
