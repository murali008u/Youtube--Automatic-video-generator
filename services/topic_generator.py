import os
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import Script
from services.llm import settings
import requests
import json
import random

def generate_daily_topic(db: Session = None) -> str:
    """
    Generates a unique daily topic by reading from a predefined list in topics.txt.
    Pops the top topic off the list so it is never reused.
    """
    topics_file = "topics.txt"
    
    if not os.path.exists(topics_file):
        print(f"[TOPIC GENERATOR] ERROR: {topics_file} not found!")
        # Fallback if the file is completely missing
        return "The Hidden Tactics of the Mongol Empire"
        
    try:
        with open(topics_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Filter out any purely empty lines
        topics = [line.strip() for line in lines if line.strip()]
        
        if not topics:
            print("[TOPIC GENERATOR] ERROR: topics.txt is empty! Please add more topics.")
            return "The True Scale of the Universe Explained"
            
        # Pop the first topic
        selected_topic = topics.pop(0)
        
        # Write the remaining topics back to the file to complete all topics.
        with open(topics_file, 'w', encoding='utf-8') as f:
            for remaining_topic in topics:
                f.write(remaining_topic + "\n")
                
        print(f"[TOPIC GENERATOR] Selected Topic: '{selected_topic}'")
        print(f"[TOPIC GENERATOR] {len(topics)} topics remaining in queue.")
        
        return selected_topic
        
    except Exception as e:
        print(f"[TOPIC GENERATOR] File Error: {e}")
        return "The Forgotten Kingdom of Axum"

if __name__ == "__main__":
    db = SessionLocal()
    topic = generate_daily_topic(db)
    print(f"Test Generation: {topic}")
    db.close()
