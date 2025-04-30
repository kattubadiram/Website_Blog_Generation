import openai
import os
from datetime import datetime
from dotenv import load_dotenv

# ——— Load credentials ———————————————————————————————
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ——— Load the 20-second voiceover script ———————————————————
def load_narration():
    with open("video_prompt.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

# ——— Split into sentences ——————————————————————————————————
def split_into_scenes(script_text):
    import re
    return [s.strip() for s in re.split(r'[.?!]\s+', script_text) if s.strip()]

# ——— Generate visual prompt for each scene —————————————————
def generate_visual_prompt(sentence):
    system_msg = (
        "You are a professional visual prompt engineer for DALL·E image generation, specializing in financial short-form videos.\n"
        "Your job is to convert narration lines into single-scene, cinematic image prompts focused on finance, business, or economics.\n"
        "Use concrete nouns and vivid adjectives. Add setting, subject, symbolic props, and emotion. Keep prompts under 200 words.\n"
        "Avoid multiple disconnected elements. No text overlays.\n\n"
        "Example 1:\n"
        "Narration: 'The Federal Reserve raised rates today.'\n"
        "Prompt: A modern Federal Reserve building under a grey sky, red downward arrows floating in the air, symbolizing rising interest rates and market anxiety.\n\n"
        "Example 2:\n"
        "Narration: 'Tesla led the rally with a 4% surge.'\n"
        "Prompt: A sunlit Wall Street trading floor glowing with green tickers, a shining Tesla logo on the main monitor, and a bronze bull statue in the foreground.\n\n"
        "Example 3:\n"
        "Narration: 'Oil prices dropped sharply, dragging energy stocks lower.'\n"
        "Prompt: A dim-lit oil rig silhouette against a stormy sea, with falling green barrels and red stock chart lines fading in the background.\n"
    )

    user_prompt = f"NARRATION: {sentence}\n\nVISUAL PROMPT:"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error generating visual prompt: {e}")
        fallback_prompt = (
            "An editorial image of a modern trading floor with glowing monitors showing stock movement, "
            "symbolic objects like a bull statue or oil barrel to reflect market themes."
        )
        print(f"⚡ Using fallback prompt instead.")
        return fallback_prompt

# ——— Save visual prompts as individual files ——————————————————
def save_individual_prompts(prompts):
    os.makedirs("visual_prompts", exist_ok=True)
    for i, prompt in enumerate(prompts, start=1):
        filename = f"visual_prompts/scene_{i}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(prompt)
    print(f"✅ Saved {len(prompts)} visual prompts in /visual_prompts")

# ——— Save to central visual prompt history ——————————————————
def save_to_history_file(prompts):
    with open("visual_prompt_history.txt", "a", encoding="utf-8") as f:
        f.write("================================================================================\n")
        f.write(f"VISUAL PROMPTS — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("================================================================================\n")
        for i, prompt in enumerate(prompts, 1):
            f.write(f"[Scene {i}] {prompt}\n\n")
    print("📝 Appended all prompts to visual_prompt_history.txt")

# ——— Main execution ————————————————————————————————
if __name__ == "__main__":
    script = load_narration()
    scenes = split_into_scenes(script)
    scenes = scenes[:5]  # ✅ Limit to first 5 scenes only

    visual_prompts = []
    for i, sentence in enumerate(scenes, start=1):
        print(f"🧠 Converting scene {i}: {sentence}")
        prompt = generate_visual_prompt(sentence)
        print(f"   → 🎨 {prompt}")
        visual_prompts.append(prompt)
    
    save_individual_prompts(visual_prompts)
    save_to_history_file(visual_prompts)
