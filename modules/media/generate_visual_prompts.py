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
    # Split by sentence-ending punctuation followed by space
    return [s.strip() for s in re.split(r'(?<=[.?!])\s+', script_text) if s.strip()]


# -------------------------
# Convert narration sentence into a DALL·E-style visual prompt
# -------------------------
def generate_visual_prompt(sentence):
    system_msg = (
        "You are a professional visual prompt engineer for DALL·E image generation, specializing in high-quality, cinematic, Sci-Fi/VFX themed financial short-form videos. "
        "Your job is to convert narration lines into single-scene, visually stunning image prompts that capture the full essence, sentiment, and mood of the narration. "
        "Focus on finance, business, or economics within a futuristic or enhanced reality setting. "
        "Use concrete nouns, vivid adjectives, symbolic props, and clear emotional tone. "
        "Ensure symbolic elements like market indicators or futuristic objects are integrated logically, not randomly placed. Avoid depictions of real animals used purely as abstract symbols (like bulls or bears). "
        "Keep prompts highly detailed, cinematic, and under 200 words, without using text or numeric overlays.\n\n"
        "Example 1:\n"
        "Narration: 'The Federal Reserve raised rates today.'\n"
        "Prompt: A grand, futuristic Federal Reserve building beneath a dark, swirling nebula, an imposing upward energy beam integrated into its sleek, chrome columns. Anxious cyborg traders stand nearby, their expressions illuminated by holographic displays, casting long, neon shadows. Powerful gusts of cosmic wind ripple through metallic flags, reinforcing the feeling of tightened economic conditions and market caution. Cinematic wide shot.\n\n"
        "Example 2:\n"
        "Narration: 'Tesla led the rally with a significant surge.'\n"
        "Prompt: A bright, bustling stock exchange floor bathed in optimistic, otherworldly light, with a gleaming Tesla Cybertruck prominently displayed under pulsating laser spotlights. Enthusiastic traders surround it, their faces lit by vibrant holographic tickers, conveying excitement and renewed confidence. High-energy cinematic scene.\n\n"
        "Example 3:\n"
        "Narration: 'Oil prices dropped sharply, dragging energy stocks lower.'\n"
        "Prompt: A striking silhouette of an offshore oil rig at dusk, amidst rough, bioluminescent seas and dark, swirling storm clouds. Oil barrels plunge dramatically into turbulent waves below, leaving trails of energy. Distant, fading red holographic chart lines subtly weave into the background, illustrating declining market sentiment and concern within the energy sector. Dramatic wide shot.\n\n"
        "Example 4:\n"
        "Narration: 'Tech stocks rebounded after days of losses.'\n"
        "Prompt: A contemporary, glass-skyscraper-filled Silicon Valley skyline glowing softly at dawn with holographic projections. In the foreground, a high-tech drone rises confidently from charred circuit board remnants, symbolizing a phoenix-like recovery. Tech workers holding digital tablets look upward with cautious optimism, faint green market indicators illuminating their screens. Optimistic dawn lighting, cinematic angle.\n\n"
        "Example 5:\n"
        "Narration: 'Pfizer climbed amid renewed interest in healthcare.'\n"
        "Prompt: A modern, futuristic laboratory brightly illuminated with cool, blue-white neon lights, showcasing a scientist holding a vial emitting a gentle blue glow, subtly branded Pfizer. Behind, a futuristic DNA helix of blue light spirals upward, while monitors embedded in sleek glass walls show signs of increasing investment enthusiasm. Clean, high-tech aesthetic, cinematic lighting.\n\n"
        "Example 6:\n"
        "Narration: 'Gold rose as investors sought safety.'\n"
        "Prompt: A dimly lit, secure, Sci-Fi vault filled with stacks of gleaming gold bars, softly illuminated by a single, hovering light orb. An investor in a tailored suit steps in from a stormy, holographic exterior, looking at the gold with evident relief and security. Reflections on the polished floor subtly echo a volatile market atmosphere outside. Secure, tense atmosphere, cinematic composition.\n"
    )

    user_prompt = f"NARRATION: {sentence}\n\nVISUAL PROMPT:"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4 # Keep temperature relatively low for consistent prompt style
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error generating visual prompt: {e}")
        # Fallback prompt updated to match the new Sci-Fi/VFX theme if API fails
        fallback_prompt = (
            "A high-quality, cinematic image of a futuristic trading floor with glowing holographic monitors displaying abstract market trends, "
            "incorporating Sci-Fi elements and a clear emotional tone related to finance. Avoid text overlays."
        )
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
