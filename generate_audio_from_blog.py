import os
from google.cloud import texttospeech

def generate_audio():
    try:
        # Step 1: Use the existing credentials file
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "google-credentials.json")
        print(f"Using credentials from: {credentials_path}")
        
        # Step 2: Read blog text
        if not os.path.exists("blog_post.txt"):
            print("❌ blog_post.txt not found")
            blog_text = "This is an automated financial news update. Please check our website for the full article."
        else:
            with open("blog_post.txt", "r") as f:
                blog_text = f.read()
            print(f"✅ Loaded blog text ({len(blog_text)} characters)")
        
        # Step 3: Set up client and Wavenet voice config
        print("Initializing Text-to-Speech client...")
        client = texttospeech.TextToSpeechClient()
        print("✅ Client initialized")
        
        input_text = texttospeech.SynthesisInput(text=blog_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Wavenet-D"  # Or try Wavenet-F for female
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Step 4: Generate and save audio
        print("Generating speech...")
        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )
        print("✅ Speech generated successfully")
        
        with open("blog_voiceover.mp3", "wb") as out:
            out.write(response.audio_content)
        print("✅ Voiceover saved as blog_voiceover.mp3")
        
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        # Optional: Create a fallback silent file if generation fails
        try:
            with open("blog_voiceover.mp3", "wb") as f:
                silent_mp3 = b'\xFF\xE3\x18\xC4\x00\x00\x00\x03H\x00\x00\x00\x00LAME3.100\x00' + b'\x00' * 50
                f.write(silent_mp3)
            print("⚠️ Created fallback silent audio file")
        except Exception as sub_e:
            print(f"❌ Also failed to write fallback audio: {sub_e}")

if __name__ == "__main__":
    generate_audio()
