import openai
import os
from datetime import datetime
from dotenv import load_dotenv
import re

# ——— Load credentials ———————————————————————————————
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ——— Load the narration script ——————————————————————————
def load_narration():
    with open("video_prompt.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

# ——— Split narration into scenes/sentences ————————————————————
def split_into_scenes(script_text):
    return [s.strip() for s in re.split(r'[.?!]\s+', script_text) if s.strip()]

# ——— Step 1: Sentiment Classification ———————————————————————
def classify_sentiment(sentence):
    """Classify the emotional tone of a sentence as bullish, bearish, volatile, or neutral."""
    system_msg = (
        "You are a financial sentiment classifier. Based on the narration below, respond ONLY with one word:\n"
        "bullish, bearish, volatile, or neutral — no punctuation or explanation.\n"
        "Think about financial context like rising markets = bullish, falling tech = bearish, VIX up = volatile, stable news = neutral."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": sentence}
            ],
            temperature=0.0
        )
        sentiment = response.choices[0].message.content.strip().lower()
        if sentiment in {"bullish", "bearish", "volatile", "neutral"}:
            return sentiment
        else:
            return "neutral"
    except Exception as e:
        print(f"⚠️ Sentiment fallback: {e}")
        return "neutral"

# ——— Steps 2–4: Generate visual prompt based on sentiment ———————————
def generate_visual_prompt(sentence, sentiment):
    system_msg = (
        "You are a visual prompt engineer using a 5-step system to generate DALL·E prompts.\n"
        "Use the provided sentiment to choose the appropriate mood and setting.\n\n"
        f"Sentiment: {sentiment.upper()}\n\n"
        "Steps:\n"
        "1. Extract key financial entities and tone.\n"
        "2. Choose a scene type (e.g., trading floor, commodities chart, bond market, currency desk).\n"
        "3. Assign symbolic visual elements (charts, arrows, graphs, tickers, metals, oil barrels).\n"
        "4. Match lighting, mood, and composition to sentiment (stormy, glowing, anxious, confident).\n"
        "5. Output a single, clean, DALL·E 3–compatible image prompt. Avoid people unless necessary.\n\n"
        f"Narration: {sentence}\n\n"
        "Output a single detailed prompt below:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_msg}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error generating prompt: {e}")
        fallback = (
            "A stylized digital trading board with mixed green and red tickers, candlestick charts, and currency symbols under ambient lighting."
        )
        print("⚡ Using fallback.")
        return fallback

# ——— Save per-scene prompt ———————————————————————————————
def save_individual_prompts(prompts):
    folder = f"visual_prompts/{datetime.now().strftime('%Y-%m-%d_%H%M')}"
    os.makedirs(folder, exist_ok=True)
    for i, prompt in enumerate(prompts, 1):
        with open(f"{folder}/scene_{i}.txt", "w", encoding="utf-8") as f:
            f.write(prompt)
    print(f"✅ Saved {len(prompts)} prompts in {folder}")

# ——— Log full batch to history ———————————————————————————————
def save_to_history_file(prompts):
    with open("visual_prompt_history.txt", "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write(f"VISUAL PROMPTS — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n")
        for i, prompt in enumerate(prompts, 1):
            f.write(f"[Scene {i}] {prompt}\n\n")
    print("📝 Prompts appended to visual_prompt_history.txt")

# ——— Main Execution ———————————————————————————————————————————
if __name__ == "__main__":
    script = load_narration()
    scenes = split_into_scenes(script)
    scenes = scenes[:5]  # Optional: limit to first 5 lines

    visual_prompts = []
    for i, sentence in enumerate(scenes, start=1):
        print(f"\n🧠 Scene {i}: {sentence}")
        sentiment = classify_sentiment(sentence)
        print(f"   → 📊 Sentiment: {sentiment}")
        prompt = generate_visual_prompt(sentence, sentiment)
        print(f"   → 🎨 Prompt: {prompt}")
        visual_prompts.append(prompt)

    save_individual_prompts(visual_prompts)
    save_to_history_file(visual_prompts)
