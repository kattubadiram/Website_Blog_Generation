# blog/save_local.py

def save_local(blog: str, summary: str):
    """Save the blog content and summary to local text files."""
    try:
        with open("blog_summary.txt", "w") as f:
            f.write(summary)
        with open("blog_post.txt", "w") as f:
            f.write(blog + "\n\n" + summary)
        print("Saved locally")
    except IOError as e:
        print(f"Failed to save local files: {e}")
