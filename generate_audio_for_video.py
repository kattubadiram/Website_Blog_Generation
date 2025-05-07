# read_video_prompt.py

import os
from google.cloud import texttospeech

# -------------------------
# Read blog narration and generate voiceover using Google TTS
# -------------------------
def read_video_prompt():
    try:
        # Load credentials path
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "google-credentials.json")
        print(f"Using credentials from: {credentials_path}")

        # Load narration text
        if not os.path.exists("video_prompt.txt"):
            print("video_prompt.txt not found")
            video_text = "This is an automated financial news update. Please check our website for the full article."
        else:
            with open("video_prompt.txt", "r") as f:
                video_text = f.read()
            print(f"Loaded blog text ({len(video_text)} characters)")

        # Initialize TTS client and configuration
        print("Initializing Text-to-Speech client...")
        client = texttospeech.TextToSpeechClient()
        print("Client initialized")
        
        input_text = texttospeech.SynthesisInput(text=video_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Wavenet-F"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Generate audio
        print("Generating speech...")
        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )
        print("Speech generated successfully")
        
        # Save output MP3
        with open("video_voiceover.mp3", "wb") as out:
            out.write(response.audio_content)
        print("Voiceover saved as video_voiceover.mp3")

    except Exception as e:
        print(f"Error generating audio: {e}")
        try:
            # Write silent fallback audio file
            with open("video_voiceover.mp3", "wb") as f:
                silent_mp3 = b'\xFF\xE3\x18\xC4\x00\x00\x00\x03H\x00\x00\x00\x00LAME3.100\x00' + b'\x00' * 50
                f.write(silent_mp3)
            print("Created fallback silent audio file")
        except Exception as sub_e:
            print(f"Also failed to write fallback audio: {sub_e}")

# -------------------------
# Main entry point
# -------------------------
if __name__ == "__main__":
    read_video_prompt()
