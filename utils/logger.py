# utils/logger.py

from datetime import datetime
import pytz

def log_blog_to_history(blog_content: str):
    """Append the blog content to a history log with a timestamp."""
    ts = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York')).strftime("%Y-%m-%d %H:%M:%S %Z")
    divider = "=" * 80
    entry = f"\n\n{divider}\nBLOG ENTRY - {ts}\n{divider}\n\n{blog_content}\n"
    with open("blog_history.txt", "a") as f:
        f.write(entry)
    print("Logged to blog_history.txt")
