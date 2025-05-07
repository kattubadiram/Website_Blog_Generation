# video/generate_prompt.py

import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_video_prompt(summary_text):
    """Generate a 2-sentence narration script from a blog summary for short-form video."""
    try:
        print("Generating video narration prompt from blog summary...")
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional scriptwriter for short financial news videos targeted at investors. "
                        "Write exactly 2 short, impactful sentences based on the summary. Do not include any branding."
                    )
                },
                {
                    "role": "user",
                    "content": f"Write a concise 2-sentence financial narration based on this summary:\n\n{summary_text}"
                }
            ],
            temperature=0.6
        )
        pure_narration = response.choices[0].message.content.strip()
        intro = "This news is brought to you by Preeti Capital, your trusted source for financial insights."
        narration = f"{intro} {pure_narration}"

        with open("video_prompt.txt", "w") as f:
            f.write(narration)
        print("Saved video narration to video_prompt.txt")
        return narration
    except Exception as e:
        print(f"Failed to generate video narration prompt: {e}")
        return ""
