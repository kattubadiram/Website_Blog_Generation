# wordpress/post_to_wp.py

import requests
import os

WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")

def post_to_wordpress(title: str, content: str, featured_media: int):
    """Publish the blog post to WordPress with the given title, content, and featured image."""
    try:
        payload = {
            "title": title,
            "content": content,
            "status": "publish",
            "featured_media": featured_media
        }
        resp = requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/posts",
            auth=(WP_USERNAME, WP_APP_PASSWORD),
            json=payload
        )
        resp.raise_for_status()
        print("Published post (status", resp.status_code, ")")
    except requests.RequestException as e:
        print(f"Failed to post to WordPress: {e}")
