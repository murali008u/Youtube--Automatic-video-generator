import os
import httplib2
import random
import time
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from db.models import Script

# The code below allows to authenticate our YouTube account
# Need 'client_secrets.json' in the root directory or credentials in .env to generate an OAuth token for the channel
from dotenv import load_dotenv
import glob

load_dotenv()

CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Valid YouTube categories (22 = People & Blogs, 27 = Education, 24 = Entertainment)
YOUTUBE_CATEGORY_ID = "27" 

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def get_authenticated_service():
    """OAuth 2.0 flow to authenticate our local script with YouTube API"""
    
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            print("[YOUTUBE UPLOAD] Loaded matching token.json.")
        except Exception as e:
            print(f"[YOUTUBE UPLOAD] Error loading token.json: {e}")
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[YOUTUBE UPLOAD] Refreshing expired YouTube token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[YOUTUBE UPLOAD] Token refresh failed: {e}. Requesting new login...")
                creds = None
                
        if not creds:
            # 1. Try to build the config dynamically from .env so the user doesn't need physical secrets lying around
            client_id = os.environ.get('GOOGLE_CLIENT_ID')
            project_id = os.environ.get('GOOGLE_PROJECT_ID')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
            
            if client_id and project_id and client_secret:
                print("\n[YOUTUBE UPLOAD] Loading OAuth credentials securely from .env variables...")
                client_config = {
                    "installed": {
                        "client_id": client_id,
                        "project_id": project_id,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_secret": client_secret,
                        "redirect_uris": ["http://localhost"]
                    }
                }
                try:
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                except Exception as e:
                    print(f"\n[YOUTUBE UPLOAD] Error loading OAuth credentials from .env: {e}")
                    return None
                    
            # 2. Fallback to reading the physical JSON file if .env keys are missing
            else:
                secret_file = CLIENT_SECRETS_FILE
                if not os.path.exists(secret_file):
                    possible_files = glob.glob("client_secret*.json")
                    if possible_files:
                        secret_file = possible_files[0]
                        print(f"\n[YOUTUBE UPLOAD] Found OAuth json credentials: {secret_file}")
                    else:
                        print(f"\n[YOUTUBE UPLOAD] MISSING CREDENTIALS: No client_secret JSON or .env keys found!")
                        print("You must add GOOGLE_CLIENT_ID, GOOGLE_PROJECT_ID, and GOOGLE_CLIENT_SECRET to your .env file.")
                        return None
                        
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
                except Exception as e:
                    print(f"\n[YOUTUBE UPLOAD] Error loading OAuth credentials from {secret_file}: {e}")
                    return None
            
            # The port 0 tells it to pick an open port. It will pop up a browser window for the user to log in.
            print("\n[YOUTUBE UPLOAD] Opening browser to authenticate YouTube Channel. Please grant access...")
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            print("[YOUTUBE UPLOAD] Saved Youtube authentication token for future runs.")
            
    return build('youtube', 'v3', credentials=creds)

def upload_video(youtube, video_path: str, thumbnail_path: str, title: str, description: str):
    safe_title = title.encode('ascii', 'ignore').decode()
    print(f"\n[YOUTUBE UPLOAD] Initializing upload for: '{safe_title}'")
    tags = ["history", "facts", "education", "story", "shorts", "documentary"]

    body = dict(
        snippet=dict(
            title=title[:100], # YouTube title limit
            description=description,
            tags=tags,
            categoryId=YOUTUBE_CATEGORY_ID
        ),
        status=dict(
            privacyStatus='public', # Post as public so it goes live automatically
            selfDeclaredMadeForKids=False,
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )

    response = None
    error = None
    retry = 0
    max_retries = 3

    print(f"[YOUTUBE UPLOAD] Uploading {video_path}...")
    while response is None and retry < max_retries:
        try:
            status, response = insert_request.next_chunk()
            if status:
                print(f"[YOUTUBE UPLOAD] Uploaded {int(status.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                error = f"A retriable HTTP error {e.resp.status} occurred."
            else:
                raise e
        except Exception as e:
            error = f"A retriable error occurred: {e}"

        if error:
            print(error)
            retry += 1
            time.sleep(random.random() * (2 ** retry))
            error = None

    if response:
        video_id = response.get('id')
        print(f"\n[YOUTUBE UPLOAD] SUCCESS: Video uploaded. ID: {video_id}")
        
        # Upload Thumbnail if it exists
        if thumbnail_path and os.path.exists(thumbnail_path):
            print(f"[YOUTUBE UPLOAD] Now uploading thumbnail: {thumbnail_path}...")
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                print("[YOUTUBE UPLOAD] Thumbnail uploaded successfully.")
            except Exception as e:
                print(f"[YOUTUBE UPLOAD] Failed to post thumbnail: {e}")
                
        # Link for the user
        print(f"\n=> Video available at: https://youtu.be/{video_id}")
        return True
    else:
        print("\n[YOUTUBE UPLOAD] FAILED to upload video.")
        return False

def push_script_to_youtube(script: Script, video_path: str, thumbnail_path: str) -> bool:
    youtube = get_authenticated_service()
    if not youtube:
        return False
        
    # Append shorts tags so it goes to the shorts feed
    # Add the hashtag here so YouTube categorizes it as a Short
    title = f"{script.title} #shorts #history #education #facts #story #documentary #religion #science #entertainment" 
    description = script.description
    
    return upload_video(youtube, video_path, thumbnail_path, title, description)
