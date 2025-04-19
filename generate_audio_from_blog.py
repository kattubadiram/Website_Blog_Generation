from gtts import gTTS
import os

def generate_audio():
    try:
        # Check if the blog post file exists
        if not os.path.exists("blog_post.txt"):
            print("❌ Error: blog_post.txt file not found")
            # Create a minimal emergency message if file is missing
            blog_text = "This is an automated financial news update. Please check our website for the full article."
        else:
            # Load blog content from file
            with open("blog_post.txt", "r") as f:
                blog_text = f.read()

        # Generate voiceover with error handling
        try:
            tts = gTTS(text=blog_text, lang='en', slow=False)
            tts.save("blog_voiceover.mp3")
            print("✅ Voiceover saved as blog_voiceover.mp3")
        except Exception as e:
            print(f"❌ Error generating audio: {e}")
            # Create a silent audio file as fallback (1 second silent mp3)
            with open("blog_voiceover.mp3", "wb") as f:
                # Simple silent MP3 header (not perfect, but works as emergency fallback)
                silent_mp3 = b'\xFF\xE3\x18\xC4\x00\x00\x00\x03H\x00\x00\x00\x00LAME3.100\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                f.write(silent_mp3)
            print("⚠️ Created fallback silent audio file")
            
    except Exception as e:
        print(f"❌ Unexpected error in audio generation: {e}")

if __name__ == "__main__":
    generate_audio()
