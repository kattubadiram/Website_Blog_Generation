import os
from blog_writer import generate_full_blog

def read_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_blog(blog_text: str, filename="generated_blog.txt"):
    output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(blog_text)
    print(f"[✓] Final blog saved to {output_path}")

if __name__ == "__main__":
    # Set paths and number of sections
    market_text_path = "topics/topic_inputs/market_readable.txt"
    number_of_sections = 1  # ← change this value to control section count

    print("[→] Loading market and style text...")
    market_text = read_file(market_text_path)

    print(f"[→] Generating blog with {number_of_sections} sections...")
    blog_output = generate_full_blog(market_text, total_sections=number_of_sections)

    save_blog(blog_output)
