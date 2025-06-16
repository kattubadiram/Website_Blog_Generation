import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuration
VIDEO_FILE = "video_output.mp4"
DESCRIPTION = "Auto-generated market update from our AI newsroom. #Shorts"
CATEGORY_ID = "25"  # News & Politics
PRIVACY = "public"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError("Token is invalid and can't be refreshed in CI. Re-generate token.json locally and upload it to GitHub Secrets.")
    
    return build("youtube", "v3", credentials=creds)

def upload_video():
    now_et = datetime.now(ZoneInfo("America/New_York"))
    formatted_date = now_et.strftime("%A, %B %d, %Y")
    title = f"Market Recap for {formatted_date} #Shorts"

    youtube = get_authenticated_service()
    media = MediaFileUpload(VIDEO_FILE, mimetype="video/mp4", resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": DESCRIPTION,
                "tags": ["finance", "stocks", "market", "news", "economy", "Shorts"],
                "categoryId": CATEGORY_ID,
            },
            "status": {
                "privacyStatus": PRIVACY,
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=media,
    )

    print(f"[INFO] Uploading to YouTube with title: {title}")
    response = request.execute()
    print("[SUCCESS] Uploaded: https://youtube.com/watch?v=" + response["id"])

if __name__ == "__main__":
    upload_video()
