# main.py

import os
import pytz
from datetime import datetime

from market_snapshot_fetcher import get_market_snapshot, append_snapshot_to_log, summarize_market_snapshot
from blog.generate_blog import generate_blog
from blog.save_local import save_local
from video.generate_prompt import generate_video_prompt
from wordpress.post_to_wp import post_to_wordpress
import image_utils

def main():
    try:
        print("Fetching market snapshot...")
        snapshot = get_market_snapshot()
        append_snapshot_to_log(snapshot)
        market_summary = summarize_market_snapshot(snapshot)

        print("Generating blog content...")
        blog_text, summary_text, base_title = generate_blog(market_summary)

        print("Fetching and uploading blog poster via Unsplash...")
        media_obj = image_utils.fetch_and_upload_blog_poster(blog_text)
        media_id = media_obj.get("id", 0)
        media_src = media_obj.get("source_url", "")

        save_local(blog_text, summary_text)
        video_prompt = generate_video_prompt(summary_text)

        est_now = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York'))
        ts_readable = est_now.strftime("%A, %B %d, %Y %H:%M")
        final_title = f"{ts_readable} EST  |  {base_title}"

        header_html = (
            '<div style="display:flex; align-items:center; margin-bottom:20px;">'
            f'<div style="flex:1;"><img src="{media_src}" style="width:100%; height:auto;" /></div>'
            '<div style="flex:1; display:flex; flex-direction:column; justify-content:center; padding-left:20px;">'
            f'<div style="color:#666; font-size:12px; margin-bottom:8px;">{ts_readable} EST</div>'
            f'<h1 style="margin:0; font-size:24px;">{base_title}</h1>'
            '</div>'
            '</div>'
        )

        post_body = f'<div>{blog_text}</div>'

        print("Publishing to WordPress...")
        post_to_wordpress(final_title, post_body, featured_media=media_id)

        print("Done")

    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
