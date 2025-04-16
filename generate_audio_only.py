from gtts import gTTS
import os

# Read the script
with open("video_script.txt", "r") as f:
    script_text = f.read()

# Generate audio
tts = gTTS(text=script_text, lang='en')
tts.save("voiceover.mp3")

print("✅ Voiceover generated and saved as voiceover.mp3")
