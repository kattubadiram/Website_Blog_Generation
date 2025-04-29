import os
import pickle
from datetime import datetime
from zoneinfo import ZoneInfo
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

VIDEO_FILE = "video_output.mp4"
DESCRIPTION = "Auto-generated market update from our AI newsroom. #Shorts"
CATEGORY_ID = "25"
PRIVACY = "public"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "youtube_token.pkl"

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError("Missing or invalid YouTube token. Cannot re-auth in CI.")

    return build("youtube", "v3", credentials=creds)

def upload_video():
    # ➡️ Generate today's date in Eastern Time
    now_et = datetime.now(ZoneInfo("America/New_York"))
    formatted_date = now_et.strftime("%A, %B %d, %Y")  # Example: Monday, April 28, 2025

    # ➡️ Final dynamic title
    title = f"AI-Powered Market Recap for {formatted_date} #Shorts"

    youtube = get_authenticated_service()
    media = MediaFileUpload(VIDEO_FILE, mimetype="video/mp4", resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": DESCRIPTION,
                "tags": ["finance", "stocks", "market", "ai", "Shorts"],
                "categoryId": CATEGORY_ID,
            },
            "status": {"privacyStatus": PRIVACY},
        },
        media_body=media,
    )

    print(f"📤 Uploading to YouTube Shorts with title: {title}")
    response = request.execute()
    print("✅ Uploaded: https://youtube.com/watch?v=" + response["id"])

if __name__ == "__main__":
    upload_video()
