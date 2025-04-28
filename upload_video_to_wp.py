# ——— Embed video into latest blog post ——————————————————
def embed_video(video_url):
    auth = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }

    try:
        # Get most recent post
        posts_resp = requests.get(f"{WP_SITE_URL}/wp-json/wp/v2/posts", headers=headers)
        posts = posts_resp.json()

        if not posts:
            print("❌ No posts found.")
            return

        post_id = posts[0]['id']
        content = posts[0]['content']['rendered']

        # Append styled vertical video embed (top left)
        embed_html = f"""
<div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
  <video controls playsinline style="max-width: 320px; width: 100%; height: auto; border-radius: 8px;">
    <source src="{video_url}" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</div>
"""

        new_content = f"{embed_html.strip()}\n\n{content}"  # Video first, then content
        payload = {"content": new_content}

        update_resp = requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}",
            headers=headers,
            json=payload
        )

        if update_resp.status_code == 200:
            print("✅ Video embedded successfully into the latest post.")
        else:
            print(f"❌ Failed to embed video: {update_resp.status_code} - {update_resp.text}")

    except Exception as e:
        print(f"❌ Error embedding video: {e}")
