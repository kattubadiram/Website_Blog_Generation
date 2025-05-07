# blog/generate_blog.py

import json
import re
import pytz
from datetime import datetime
from openai import OpenAIError
import openai

from utils.ordinal import ordinal
from utils.logger import log_blog_to_history

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_blog(market_summary: str):
    est = pytz.timezone("America/New_York")
    now_est = datetime.now(pytz.utc).astimezone(est)
    weekday = now_est.strftime("%A")
    day_number = now_est.day
    month_name = now_est.strftime("%B")
    year = now_est.year
    day_ord = ordinal(day_number)

    today_line = f"Today is {weekday}, {day_ord} of {month_name} {year} Eastern Time | This news is brought to you by Preeti Capital, your trusted source for financial insights."

    system = {
        "role": "system",
        "content": (
            f"You are a senior financial journalist writing for institutional investors.\n\n"
            f"Start the blog post with this exact sentence:\n{today_line}\n\n"
            "Then, write a 250-word analysis of today's global market based strictly on the provided summary.\n"
            "Do not fabricate or add any external data. Maintain a professional, analytical tone.\n\n"
            "IMPORTANT FORMATTING:\n"
            "- Use only the full names of indices and companies.\n"
            "- Do NOT include symbols inside brackets.\n\n"
            "Return as JSON with 'blog', 'summary', and 'title'."
        )
    }

    clean_summary = re.sub(r'\(\^[A-Z0-9\.\-]+\)', '', market_summary)
    messages = [system, {"role": "user", "content": clean_summary}]

    try:
        resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        data = json.loads(resp.choices[0].message.content)
        blog = data["blog"].strip()
        summary = data["summary"].strip()
        title = data["title"].strip()
    except OpenAIError as e:
        print(f"Error processing AI response: {e}")
        blog = "Markets continue to adapt..."
        summary = "SUMMARY: Financial markets are experiencing..."
        title = "Market Update: Strategic Positioning in Current Economic Climate"

    log_blog_to_history(blog)
    return blog, summary, title
