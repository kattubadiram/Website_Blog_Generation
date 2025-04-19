from gtts import gTTS
import os

def read_video_prompt():
    if not os.path.exists("video_prompt.txt"):
        print("❌ Error: video_prompt.txt not found.")
        return None
    with open("video_prompt.txt", "r", encoding="utf-8") as file:
        return file.read().strip()

def generate_video_voiceover(text, output_file="voiceover.mp3"):
    try:
        tts = gTTS(text=text, lang='en', tld='com')
        tts.save(output_file)
        print(f"✅ Video voiceover saved as {output_file}")
    except Exception as e:
        print(f"❌ Error generating video voiceover: {e}")

if __name__ == "__main__":
    script = read_video_prompt()
    if script:
        generate_video_voiceover(script)
