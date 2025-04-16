import openai
import os
from dotenv import load_dotenv

# Load credentials
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Read summary from file
def read_summary():
    with open("blog_summary.txt", "r") as file:
        return file.read()

# Generate short video script
def generate_video_script(summary_text):
    prompt = (
        "Convert the following 250-word blog summary into a 30-second social media video script. "
        "Use a casual, engaging tone. Include a brief hook at the beginning, 2-3 main points, and a call-to-action.\n\n"
        f"SUMMARY:\n{summary_text}"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You write scripts for social media videos."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8
    )

    script = response.choices[0].message.content.strip()

    # Save script
    with open("video_script.txt", "w") as f:
        f.write(script)

    print("\n✅ 30-second video script generated and saved as 'video_script.txt'.")

# Main
if __name__ == "__main__":
    summary = read_summary()
    generate_video_script(summary)
