import os
import datetime

LOG_FILE = "blog_history.txt"

def log_blog(blog_content):
    """
    Append blog content to a text file with date and time
    
    Args:
        blog_content (str): The blog content to log
    """
    # Get current date and time
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the entry with timestamp and separator
    entry = f"\n\n{'=' * 80}\n"
    entry += f"BLOG ENTRY - {timestamp}\n"
    entry += f"{'=' * 80}\n\n"
    entry += blog_content
    entry += "\n\n"
    
    # Append to log file
    with open(LOG_FILE, 'a') as f:
        f.write(entry)
    
    print(f"✅ Blog content logged to {LOG_FILE}")
