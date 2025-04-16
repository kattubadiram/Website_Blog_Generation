from gtts import gTTS

# Load blog content from file
with open("blog_post.txt", "r") as f:
    blog_text = f.read()

# Generate voiceover
tts = gTTS(text=blog_text, lang='en')
tts.save("blog_voiceover.mp3")

print("✅ Voiceover saved as blog_voiceover.mp3")
