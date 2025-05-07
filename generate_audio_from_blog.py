import os
import math
import uuid
import shutil
from google.cloud import texttospeech
import subprocess

MAX_BYTES = 4500  # Safe limit below 5000 bytes

def split_text_to_chunks(text, max_bytes=MAX_BYTES):
    chunks = []
    current = ""
    for word in text.split():
        if len((current + " " + word).encode("utf-8")) > max_bytes:
            chunks.append(current.strip())
            current = word
        else:
            current += " " + word
    if current:
        chunks.append(current.strip())
    return chunks

def synthesize_chunks(chunks, output_dir, client, voice, audio_config):
    audio_paths = []
    for i, chunk in enumerate(chunks):
        input_text = texttospeech.SynthesisInput(text=chunk)
        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )
        chunk_filename = os.path.join(output_dir, f"chunk_{i}.mp3")
        with open(chunk_filename, "wb") as f:
            f.write(response.audio_content)
        audio_paths.append(chunk_filename)
        print(f"✅ Synthesized chunk {i+1}/{len(chunks)}")
    return audio_paths

def merge_audio_files(audio_paths, output_file):
    list_file = "merge_list.txt"
    with open(list_file, "w") as f:
        for path in audio_paths:
            f.write(f"file '{path}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_file])
    os.remove(list_file)

def generate_audio():
    try:
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "google-credentials.json")
        print(f"Using credentials from: {credentials_path}")

        if not os.path.exists("blog_post.txt"):
            print("❌ blog_post.txt not found")
            blog_text = "This is an automated financial news update. Please check our website for the full article."
        else:
            with open("blog_post.txt", "r") as f:
                blog_text = f.read()
            print(f"✅ Loaded blog text ({len(blog_text)} characters)")

        print("Splitting blog into byte-safe chunks...")
        chunks = split_text_to_chunks(blog_text)
        print(f"✅ Split into {len(chunks)} chunks")

        print("Initializing TTS client...")
        client = texttospeech.TextToSpeechClient()
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Wavenet-D"
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        temp_dir = f"tmp_audio_{uuid.uuid4().hex}"
        os.makedirs(temp_dir, exist_ok=True)

        audio_paths = synthesize_chunks(chunks, temp_dir, client, voice, audio_config)

        print("Merging audio chunks...")
        merge_audio_files(audio_paths, "blog_voiceover.mp3")
        print("✅ Final voiceover saved as blog_voiceover.mp3")

        shutil.rmtree(temp_dir)

    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        try:
            with open("blog_voiceover.mp3", "wb") as f:
                silent_mp3 = b'\xFF\xE3\x18\xC4\x00\x00\x00\x03H\x00\x00\x00\x00LAME3.100\x00' + b'\x00' * 50
                f.write(silent_mp3)
            print("⚠️ Created fallback silent audio file")
        except Exception as sub_e:
            print(f"❌ Also failed to write fallback audio: {sub_e}")

if __name__ == "__main__":
    generate_audio()
