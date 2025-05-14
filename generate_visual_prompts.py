# generate_visual_prompts_from_script.py

import openai
import os
from datetime import datetime
from dotenv import load_dotenv

# -------------------------
# Load API key from environment
# -------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# -------------------------
# Load narration script from file
# -------------------------
def load_narration():
    try:
        with open("video_prompt.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: video_prompt.txt not found.")
        return ""

# -------------------------
# Split narration into individual sentences (scenes)
# -------------------------
def split_into_scenes(script_text):
    import re
    return [s.strip() for s in re.split(r'(?<=[.?!])\s+', script_text) if s.strip()]

# -------------------------
# Convert narration sentence into a simplified iconographic visual prompt
# -------------------------
def generate_visual_prompt(sentence):
    system_msg = (
        "You are a visual prompt generator for DALL·E, focused on producing ultra-simple, clear, minimalistic image prompts for financial news narration. "
        "Each prompt must describe exactly one scene using very few elements — ideally just the core subject (like a stock symbol, asset type, or company logo) and a visual indicator of movement (like a red down arrow or green up arrow). "
        "Avoid any background storytelling, human characters, emotions, or environment descriptions. "
        "Do not include text, percentages, or numbers in the image. "
        "Your prompts should read like:\n"
        "- 'A gold bar with a green up arrow above it on a plain white background.'\n"
        "- 'The SPY ETF logo with a red down arrow next to it on a clean background.'\n"
        "- 'An oil barrel with a red down arrow.'\n"
        "- 'A Tesla car with a green up arrow.'\n"
        "- 'A stack of dollar bills with a red down arrow.'\n\n"
        "Always keep it symbolic, literal, and minimalistic. Avoid clutter."
    )

    user_prompt = f"NARRATION: {sentence}\n\nVISUAL PROMPT:"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error generating visual prompt: {e}")
        fallback_prompt = "A simple visual of a financial logo with an up or down arrow."
        print("Using fallback prompt instead.")
        return fallback_prompt

# -------------------------
# Save individual scene prompts to separate files
# -------------------------
def save_individual_prompts(prompts):
    os.makedirs("visual_prompts", exist_ok=True)
    for i, prompt in enumerate(prompts, start=1):
        filename = f"visual_prompts/scene_{i}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(prompt)
    print(f"Saved {len(prompts)} visual prompts in /visual_prompts")

# -------------------------
# Append visual prompts to a history log
# -------------------------
def save_to_history_file(prompts):
    with open("visual_prompt_history.txt", "a", encoding="utf-8") as f:
        f.write("================================================================================\n")
        f.write(f"VISUAL PROMPTS — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("================================================================================\n")
        for i, prompt in enumerate(prompts, 1):
            f.write(f"[Scene {i}] {prompt}\n\n")
    print("Appended all prompts to visual_prompt_history.txt")

# -------------------------
# Main execution block
# -------------------------
if __name__ == "__main__":
    script = load_narration()
    if not script:
        print("Script is empty. Exiting.")
    else:
        scenes = split_into_scenes(script)
        if not scenes:
             print("No complete sentences found in the script.")
        else:
            scenes = scenes[:5]  # Limit to first 5 scenes only

            visual_prompts = []
            for i, sentence in enumerate(scenes, start=1):
                print(f"Converting scene {i}: {sentence}")
                prompt = generate_visual_prompt(sentence)
                print(f"    → {prompt}")
                visual_prompts.append(prompt)

            if visual_prompts:
                save_individual_prompts(visual_prompts)
                save_to_history_file(visual_prompts)
            else:
                print("No visual prompts were generated.")
