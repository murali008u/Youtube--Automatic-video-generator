import sys
import datetime
from db.database import SessionLocal
from services.topic_generator import generate_daily_topic
from orchestrator import process_video_pipeline

def run_daily_job():
    print("========================================================")
    print(f"[{datetime.datetime.now()}] STARTING DAILY YOUTUBE AUTOMATION JOB")
    print("========================================================")
    
    # 1. Connect to Database
    db = SessionLocal()
    
    # 2. Generate the daily topic using Ollama
    print("\n[PHASE 0] Getting the topic...")
    topic = generate_daily_topic(db)
    db.close()
    
    if not topic:
        print("[ERROR] Failed to generate a topic. Aborting.")
        sys.exit(1)
        
    print(f"\n[TOPIC SELECTED] '{topic}'")
    
    # 3. Trigger the main orchestrator pipeline
    print("\n[LAUNCHING ORCHESTRATOR]")
    success = process_video_pipeline(topic)
    
    print("\n========================================================")
    if success:
        print(f"[{datetime.datetime.now()}] DAILY JOB COMPLETED SUCCESSFULLY.")
    else:
        print(f"[{datetime.datetime.now()}] DAILY JOB FAILED.")
    print("========================================================")

if __name__ == "__main__":
    run_daily_job()
