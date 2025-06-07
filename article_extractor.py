#!/usr/bin/env python3
"""
article_extractor.py
--------------------
Utility: fetch a web article and return clean plain-text.

USAGE (from another script)
    from article_extractor import extract_article_text
    txt = extract_article_text("https://…")
"""

from __future__ import annotations
import re, textwrap
import requests
from readability import Document
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def _clean_html(html: str) -> str:
    """Strip scripts/styles, collapse whitespace."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "header", "footer", "form"]):
        tag.decompose()

    text = soup.get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return textwrap.shorten(text, width=10_000, placeholder=" …")

def extract_article_text(url: str, timeout: int = 10) -> str:
    """
    Return cleaned plain-text for the article at *url*.
    Falls back gracefully if readability fails.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
    except requests.RequestException as e:
        return f"[error] fetch failed: {e}"

    try:
        doc = Document(r.text)
        main_html = doc.summary(html_partial=True)
        text = _clean_html(main_html)
    except Exception:
        text = _clean_html(r.text)

    return text

if __name__ == "__main__":          # quick CLI test
    import sys, textwrap
    if len(sys.argv) != 2:
        sys.exit("Usage: python article_extractor.py <URL>")
    print(textwrap.fill(extract_article_text(sys.argv[1]), width=90))
