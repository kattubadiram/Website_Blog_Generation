import os
import re
from datetime import datetime
import pytz
from openai import OpenAI
from dotenv import load_dotenv

# Load OpenAI key
load_dotenv(dotenv_path=os.path.abspath("../.env"))  # adjust if .env is one level up

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def clean_market_text(text: str) -> str:
    return re.sub(r'\(\^[A-Z0-9\.\-]+\)', '', text)

def get_intro_line() -> str:
    est = pytz.timezone("America/New_York")
    now_est = datetime.now(pytz.utc).astimezone(est)
    weekday = now_est.strftime("%A")
    day_number = now_est.day
    month_name = now_est.strftime("%B")
    year = now_est.year

    def ordinal(n):
        return f"{n}{'th' if 11 <= (n % 100) <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"

    day_ord = ordinal(day_number)
    return f"Today is {weekday}, {day_ord} of {month_name} {year} Eastern Time | This news is brought to you by Preeti Capital, your trusted source for financial insights."

def build_section_prompt(market_text: str, section_index: int, total_sections: int) -> str:
    return (
        f"You are a professional financial journalist writing a long-form market blog.\n\n"
        f"MARKET SNAPSHOT:\n{market_text}\n\n"
        f"Write section {section_index + 1} of {total_sections}. Each section should be 400–500 words.\n"
        "- Create a clear, relevant heading.\n"
        "- Do not repeat information from earlier sections.\n"
        "- Use journalistic flow and analysis.\n"
        "- First section: introduce context. Final section: conclude or project outlook.\n"
    )

def generate_section(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a skilled financial blog writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_full_blog(market_text: str, total_sections: int = 10) -> str:
    market_text_clean = clean_market_text(market_text)
    blog_parts = []
    for i in range(total_sections):
        print(f"[{i+1}/{total_sections}] Generating section...")
        prompt = build_section_prompt(market_text_clean, i, total_sections)
        section = generate_section(prompt)
        blog_parts.append(section)
        full_blog = "\n\n".join(blog_parts)
        intro_line = get_intro_line()
        cleaned_blog = re.sub(r'^#+\s*', '', full_blog, flags=re.MULTILINE)  # remove markdown ## headers
        return f"{intro_line}\n\n{cleaned_blog}"
