import os
import subprocess
from pydub import AudioSegment
from pyannote.audio import Pipeline
from tqdm import tqdm
import math

input_wav = "input.wav"
audio_file = "mix16k.wav"
merged_rttm = "full_dialogue.rttm"
speaker_a = "SPEAKER_00"
speaker_b = "SPEAKER_01"

# Step 0: Convert input.wav to mono, 16kHz using ffmpeg
def convert_audio(input_path, output_path):
    print("Converting audio to mono 16kHz...")
    command = [
        "ffmpeg", "-y", "-i", input_path,
        "-ac", "1", "-ar", "16000",
        output_path
    ]
    subprocess.run(command, check=True)
    print(f"Saved converted file as {output_path}")

# Step 1: Run diarization on full audio and save RTTM
def diarize_full(audio_path, rttm_path):
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
    diarization = pipeline(audio_path, num_speakers=2)
    with open(rttm_path, "w") as f:
        diarization.write_rttm(f)
    print(f"RTTM saved to: {rttm_path}")

# Step 2: Parse RTTM and extract per-speaker segments
def extract_speakers_audio(audio_path, rttm_path):
    with open(rttm_path) as f:
        lines = [line.strip() for line in f if line.strip()]

    speakers = sorted({line.split()[7] for line in lines})
    if len(speakers) != 2:
        raise ValueError(f"Expected 2 speakers in RTTM, found {len(speakers)}: {speakers}")
    mapping = {speakers[0]: speaker_a, speakers[1]: speaker_b}

    full_audio = AudioSegment.from_wav(audio_path)
    duration_ms = len(full_audio)
    audio_tracks = {
        speaker_a: AudioSegment.silent(duration=duration_ms),
        speaker_b: AudioSegment.silent(duration=duration_ms)
    }

    for line in tqdm(lines, desc="Extracting speaker audio"):
        parts = line.split()
        start_ms = int(float(parts[3]) * 1000)
        length_ms = int(float(parts[4]) * 1000)
        original_label = parts[7]
        mapped_label = mapping[original_label]
        segment = full_audio[start_ms:start_ms + length_ms]
        audio_tracks[mapped_label] = audio_tracks[mapped_label].overlay(segment, position=start_ms)

    audio_tracks[speaker_a].export("speaker_a.wav", format="wav")
    audio_tracks[speaker_b].export("speaker_b.wav", format="wav")
    print("Exported speaker_a.wav and speaker_b.wav")

# Full pipeline
def run_full_pipeline():
    convert_audio(input_wav, audio_file)
    diarize_full(audio_file, merged_rttm)
    extract_speakers_audio(audio_file, merged_rttm)
    print("Done.")

if __name__ == "__main__":
    run_full_pipeline()
