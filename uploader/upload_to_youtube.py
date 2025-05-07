import os
from datetime import datetime
from zoneinfo import ZoneInfo
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuration
VIDEO_FILE = "video_output.mp4"
DESCRIPTION = "Auto-generated market update from our AI newsroom."
CATEGORY_ID = "25"  # News & Politics
PRIVACY = "public"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    creds = Credentials(
        None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=SCOPES
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def upload_video():
    now_et = datetime.now(ZoneInfo("America/New_York"))
    formatted_date = now_et.strftime("%A, %B %d, %Y")
    title = f"Market Recap for {formatted_date}"

    youtube = get_authenticated_service()
    media = MediaFileUpload(VIDEO_FILE, mimetype="video/mp4", resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": DESCRIPTION,
                "tags": ["finance", "stocks", "market", "news", "economy"],
                "categoryId": CATEGORY_ID,
            },
            "status": {
                "privacyStatus": PRIVACY
            }
        },
        media_body=media,
    )

    print(f"Uploading to YouTube with title: {title}")
    response = request.execute()
    print("Uploaded successfully: https://youtube.com/watch?v=" + response["id"])

if __name__ == "__main__":
    upload_video()
