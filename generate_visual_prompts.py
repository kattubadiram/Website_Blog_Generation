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
    "You are a professional visual prompt engineer for DALL·E image generation, specializing in financial short-form videos. Your job is to convert narration lines into single-scene, cinematic image prompts that capture the full essence, sentiment, and mood of the narration. Focus on finance, business, or economics. Use concrete nouns, vivid adjectives, symbolic props, and clear emotional tone. Keep prompts realistic and clear, under 200 words, without using text or numeric overlays.\n\n"
    "Example 1:\n"
    "Narration: 'The Federal Reserve raised rates today.'\n"
    "Prompt: A grand Federal Reserve building beneath a gray, cloudy sky, an imposing upward arrow subtly carved into its marble columns. Anxious traders stand nearby, their expressions tense, casting somber shadows. Gusts of wind ripple through flags, reinforcing the feeling of tightened economic conditions and market caution.\n\n"
    "Example 2:\n"
    "Narration: 'Tesla led the rally with a significant surge.'\n"
    "Prompt: A bright, bustling stock exchange floor bathed in optimistic sunlight, with a gleaming Tesla car prominently displayed under spotlights. Enthusiastic traders surround it, their screens awash with green, conveying excitement and renewed confidence symbolized by a bronze bull statue.\n\n"
    "Example 3:\n"
    "Narration: 'Oil prices dropped sharply, dragging energy stocks lower.'\n"
    "Prompt: A striking silhouette of an offshore oil rig at dusk, amidst rough seas and dark, stormy skies. Oil barrels plunge dramatically into turbulent waves below. Distant, fading red chart lines subtly weave into the background, illustrating declining market sentiment and concern within the energy sector.\n\n"
    "Example 4:\n"
    "Narration: 'Tech stocks rebounded after days of losses.'\n"
    "Prompt: A contemporary, glass-skyscraper-filled Silicon Valley skyline glowing softly at dawn. In the foreground, a high-tech drone rises confidently from charred circuit board remnants, symbolizing a phoenix-like recovery. Tech workers holding digital tablets look upward with cautious optimism, faint green market indicators illuminating their screens.\n\n"
    "Example 5:\n"
    "Narration: 'Pfizer climbed amid renewed interest in healthcare.'\n"
    "Prompt: A modern laboratory brightly illuminated with cool blue-white lights, showcasing a scientist holding a vial emitting a gentle blue glow, subtly branded Pfizer. Behind, a futuristic DNA helix of blue light spirals upward, while monitors embedded in sleek glass walls show signs of increasing investment enthusiasm.\n\n"
    "Example 6:\n"
    "Narration: 'Gold rose as investors sought safety.'\n"
    "Prompt: A dimly lit, secure vault filled with stacks of gleaming gold bars, softly illuminated by a single hanging lightbulb. An investor in a tailored suit steps in from a stormy exterior, umbrella dripping, looking at the gold with evident relief and security. Reflections on the polished floor subtly echo a volatile market atmosphere outside.\n"
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
