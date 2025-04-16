# 📝 Automated Blog Posting to WordPress Using ChatGPT API

## 1. Project Overview

This project automates the creation and publishing of a daily blog post using OpenAI's ChatGPT API and posts it directly to a WordPress site using the REST API.

**Key Features:**

- Automatically runs every day at 6:00 AM MST
- Generates a \~250-word news-style blog post
- Posts it to a WordPress blog using WordPress credentials and application password
- Can be expanded with prompt rotation, post deletion, and image generation

**Technologies Used:**

- Python
- OpenAI API
- WordPress REST API
- GitHub Actions

---

## 2. Setup Instructions

### 2.1. Prerequisites

- OpenAI account with API access: [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
- A WordPress website (self-hosted or WP.com with REST support)
- An application password generated for your WP account
- A GitHub account
- Python 3.11+ installed locally

### 2.2. Local Setup

```bash
mkdir daily-wordpress-bot
cd daily-wordpress-bot
python3 -m venv venv
source venv/bin/activate
pip install requests python-dotenv
```

### 2.3. Create `.env` File (For Local Testing Only)

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx
WP_USERNAME=your_wp_username
WP_APP_PASSWORD=your_wp_app_password
WP_SITE_URL=https://yourdomain.com
```

### 2.4. Create `.gitignore`

```
.env
venv/
```

---

## 3. Core Files and Code

### 3.1. `daily_blog.py`

```python
import requests
import datetime
import base64
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL = os.getenv("WP_SITE_URL")

PROMPT = "Write a 250-word news-style blog post about the latest in business news. Make it informative, engaging, and easy to understand."

def generate_blog():
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0.7
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

def post_to_wordpress(title, content):
    auth = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    data = {
        "title": title,
        "content": content,
        "status": "publish"
    }
    response = requests.post(f"{WP_SITE_URL}/wp-json/wp/v2/posts", headers=headers, json=data)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    blog = generate_blog()
    today = datetime.date.today().strftime("%Y-%m-%d")
    title = f"{today} – Daily Business News"
    result = post_to_wordpress(title, blog)
    print("✅ Blog posted:", result['link'])
```

---

## 4. GitHub Repository Setup

### 4.1. Creating a Clean GitHub Repo

```bash
git init
git remote add origin https://github.com/yourusername/daily-wordpress-bot.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

### 4.2. Add Secrets in GitHub

- Go to `Settings > Secrets > Actions` in your repo
- Add the following secrets:
  - `OPENAI_API_KEY`
  - `WP_USERNAME`
  - `WP_APP_PASSWORD`
  - `WP_SITE_URL`

---

## 5. GitHub Actions Workflow

### 5.1. File: `.github/workflows/post_blog.yml`

```yaml
name: Post Blog to WordPress

on:
  schedule:
    - cron: "0 13 * * *"  # 6 AM MST (Arizona)
  workflow_dispatch:

jobs:
  post-blog:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests python-dotenv

      - name: Run blog script
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          WP_USERNAME: ${{ secrets.WP_USERNAME }}
          WP_APP_PASSWORD: ${{ secrets.WP_APP_PASSWORD }}
          WP_SITE_URL: ${{ secrets.WP_SITE_URL }}
        run: python daily_blog.py
```

---

## 6. Testing and Validation

### 6.1. Local Testing

```bash
python daily_blog.py
```

### 6.2. Manual GitHub Run

- Go to `Actions` tab → `Post Blog to WordPress`
- Click `Run workflow`

---

## 7. Deployment Behavior

- Posts are created every day at 6:00 AM MST
- Blogs appear directly on WordPress front page
- Includes post title and content

---

## 8. Future Enhancements

- 🧹 Automatically delete yesterday's blog post
- 🖼 Add featured images via DALL·E or Unsplash
- 🔁 Rotate prompts by topic
- 🧠 Add error logging + retry logic
- 📊 Add analytics tracking or summary

---

## ✅ Done!

You now have a fully automated content pipeline from OpenAI to WordPress. No cron jobs. No servers. Just clean AI-powered blogging every morning.

