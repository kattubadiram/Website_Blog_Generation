import openai
import os
from datetime import datetime
from dotenv import load_dotenv

# ——— Load credentials —————————————————————————————
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ——— Initialize OpenAI client —————————————————————————
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ——— Read the 100‑word blog summary ——————————————————————
def read_summary():
    with open("blog_summary.txt", "r", encoding="utf-8") as file:
        return file.read().strip()

# ——— Ensure a file exists —————————————————————————————
def ensure_file(path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8"):
            pass

# ——— Generate and save 20‑second voiceover script —————————————————
def generate_voiceover_script(summary: str) -> str:
    prompt_text = (
        "You are a professional financial news writer. "
        "Using the following 100-word market summary, write a short voiceover script "
        "that sounds like a 20-second news segment. Use clear, concise, journalistic language. "
        "The script should:\n"
        "  • Convey the same key data and takeaways from the summary\n"
        "  • Be spoken in 20 seconds or less (around 60–70 words)\n"
        "  • Be engaging, but professional — like a business news anchor\n"
        "  • Avoid fluff, filler, or repetition\n\n"
        f"SUMMARY:\n{summary}\n\n"
        "Now write the 20-second voiceover script:"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a voiceover scriptwriter for financial news."},
            {"role": "user", "content": prompt_text}
        ],
        temperature=0.6
    )

    voiceover_script = response.choices[0].message.content.strip()

    # — Save to history file —
    history_path = "video_prompt_history.txt"
    ensure_file(history_path)
    with open(history_path, "a", encoding="utf-8") as hist:
        hist.write("================================================================================\n")
        hist.write(f"VOICEOVER SCRIPT — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        hist.write("================================================================================\n")
        hist.write(voiceover_script + "\n\n")

    # — Save to latest prompt file —
    latest_path = "video_prompt.txt"
    ensure_file(latest_path)
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(voiceover_script)

    print("\n✅ 20‑second voiceover script generated and saved.")
    return voiceover_script

# ——— Main execution ————————————————————————————————
if __name__ == "__main__":
    summary = read_summary()
    generate_voiceover_script(summary)
