"""
Image utility module for selecting and handling financial blog images.
This module contains functions for content-aware image selection.
"""
import os
import random
import requests
import time

def get_advanced_content_aware_image(blog_text: str, summary_text: str, title: str) -> str:
    """
    Select the most appropriate financial image based on detailed analysis of the blog post content.
    Aims for at least 75% confidence in relevance, particularly to the title.
    """ 
    # Define a comprehensive set of financial image categories with high-quality images
    image_categories = {
        # Federal Reserve & Monetary Policy
        "federal_reserve": [
            "https://images.unsplash.com/photo-1589758438368-0ad531db3366?q=80&w=1024",  # Federal Reserve building
            "https://images.unsplash.com/photo-1554672408-17407e0322ce?q=80&w=1024"     # Central bank concept
        ],
        
        # Interest Rates & Rate Changes
        "interest_rates": [
            "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=1024",  # Rate chart
            "https://images.unsplash.com/photo-1591696205602-2f950c417cb9?q=80&w=1024"   # Interest rate concept - FIXED URL
        ],
        
        # Market Decline & Bearish News
        "market_decline": [
            "https://images.unsplash.com/photo-1563986768494-4dee2763ff3f?q=80&w=1024",  # Downward chart
            "https://images.unsplash.com/photo-1574607383476-f517f260d30b?q=80&w=1024"   # Bear market concept
        ],
        
        # Market Growth & Bullish News
        "market_growth": [
            "https://images.unsplash.com/photo-1535320903710-d993d3d77d29?q=80&w=1024",  # Bull statue
            "https://images.unsplash.com/photo-1560221328-12fe60f83ab8?q=80&w=1024"     # Upward graph
        ],
        
        # Market Volatility & Uncertainty
        "market_volatility": [
            "https://images.unsplash.com/photo-1611923246944-beca9a3e8a08?q=80&w=1024",  # Volatile chart
            "https://images.unsplash.com/photo-1569025690938-a00729c9e1f9?q=80&w=1024"   # Market uncertainty
        ],
        
        # Inflation & Consumer Prices
        "inflation": [
            "https://images.unsplash.com/photo-1574700765469-92d15a8dd4c1?q=80&w=1024",  # Money printing
            "https://images.unsplash.com/photo-1563013544-824ae1b704d3?q=80&w=1024"     # Price tags
        ],
        
        # Economic Growth & GDP
        "economic_growth": [
            "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1024",    # City growth
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=1024"  # Economic development
        ],
        
        # Recession & Economic Downturn
        "recession": [
            "https://images.unsplash.com/photo-1587613863965-74d82b39ef79?q=80&w=1024",  # Empty street
            "https://images.unsplash.com/photo-1612010167102-d1e8f83833e1?q=80&w=1024"   # Closed sign
        ],
        
        # Banking & Finance Industry
        "banking": [
            "https://images.unsplash.com/photo-1601597111158-2fceff292cdc?q=80&w=1024",  # Bank building
            "https://images.unsplash.com/photo-1541199249251-f713e6145474?q=80&w=1024"   # Banking concept
        ],
        
        # Stocks & Equities
        "stocks": [
            "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=1024",  # Stock chart
            "https://images.unsplash.com/photo-1496262967815-132206202600?q=80&w=1024"   # Stock exchange visualization
        ],
        
        # Bonds & Treasury Markets
        "bonds": [
            "https://images.unsplash.com/photo-1591696205602-2f950c417cb9?q=80&w=1024",  # Yield curve concept - FIXED URL
            "https://images.unsplash.com/photo-1518183214770-9cffbec0d3e4?q=80&w=1024"   # Treasury bond concept
        ],
        
        # Housing & Real Estate
        "housing": [
            "https://images.unsplash.com/photo-1480074568708-e7b720bb3f09?q=80&w=1024",  # Houses
            "https://images.unsplash.com/photo-1560518883-ce09059eeffa?q=80&w=1024"     # Real estate
        ],
        
        # Tech Sector & Innovation
        "technology": [
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1024",  # Tech visualization
            "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1024"   # Tech with charts
        ],
        
        # Energy Markets & Oil
        "energy": [
            "https://images.unsplash.com/photo-1559297434-fae8a1916a79?q=80&w=1024",    # Oil industry
            "https://images.unsplash.com/photo-1518186285589-2f7649de83e0?q=80&w=1024"  # Energy market
        ],
        
        # Cryptocurrency & Digital Assets
        "cryptocurrency": [
            "https://images.unsplash.com/photo-1516245834210-c4c142787335?q=80&w=1024",  # Bitcoin
            "https://images.unsplash.com/photo-1625215081729-7d3f89777fbc?q=80&w=1024"   # Crypto trading
        ],
        
        # Global Markets & International Trade
        "global_markets": [
            "https://images.unsplash.com/photo-1542744173-8659239b7312?q=80&w=1024",     # Global business
            "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=1024"   # International finance
        ],
        
        # Financial Analysis & Reports
        "financial_analysis": [
            "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1024",    # Analysis charts
            "https://images.unsplash.com/photo-1551836022-aadb801c60e9?q=80&w=1024"     # Financial reports
        ],
        
        # Investment Strategy & Portfolio Management
        "investment": [
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=1024",  # Investment growth
            "https://images.unsplash.com/photo-1604594849809-dfedbc827105?q=80&w=1024"   # Portfolio management
        ],
        
        # General Finance (Default Category)
        "general_finance": [
            "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1024",  # Financial chart
            "https://images.unsplash.com/photo-1607921007061-35cf093a049a?q=80&w=1024"   # Financial concept
        ]
    }
    
    # Define comprehensive keywords for each category
    category_keywords = {
        "federal_reserve": [
            "federal reserve", "fed", "central bank", "jerome powell", "powell", 
            "fomc", "federal open market committee", "fed chair", "federal reserve chair",
            "fed policy", "monetary policy committee", "central banking"
        ],
        "interest_rates": [
            "interest rate", "rates", "rate hike", "rate cut", "rate decision", "basis point",
            "interest rate decision", "borrowing costs", "lending rate", "prime rate", 
            "discount rate", "bank rate", "rate adjustment", "rate change"
        ],
        "market_decline": [
            "decline", "drop", "fall", "plunge", "bearish", "bear market", "downturn", 
            "sell-off", "correction", "crash", "slump", "tumbled", "losses", "negative",
            "lower", "descending", "downward", "dropped", "plummeted"
        ],
        "market_growth": [
            "growth", "surge", "rally", "bullish", "bull market", "upturn", "upward", 
            "gains", "positive", "increase", "climb", "rising", "rose", "soared",
            "jumped", "higher", "ascending", "expanded", "improved"
        ],
        "market_volatility": [
            "volatility", "fluctuation", "turbulence", "uncertain", "uncertainty", 
            "unstable", "erratic", "swings", "oscillation", "wavering", "choppy",
            "shaky", "oscillating", "jitters", "turmoil", "unpredictable", "gyrations"
        ],
        "inflation": [
            "inflation", "consumer price", "cpi", "price increases", "rising prices", 
            "cost of living", "inflationary", "price stability", "hyperinflation",
            "deflation", "stagflation", "core inflation", "price pressures", "price index",
            "inflated", "pricing pressures", "price hikes"
        ],
        "economic_growth": [
            "economic growth", "gdp", "gross domestic product", "expansion", "output", 
            "productivity", "economic activity", "economic health", "robust growth",
            "economic rebound", "economic recovery", "economy grows", "growth rate"
        ],
        "recession": [
            "recession", "economic downturn", "contraction", "depression", "slump", 
            "economic crisis", "negative growth", "slowdown", "shrinking economy",
            "economic decline", "recessionary", "economic slump", "hard landing"
        ],
        "banking": [
            "bank", "banking", "commercial bank", "investment bank", "lender", "credit", 
            "deposit", "banking sector", "banking system", "financial institution",
            "banks", "creditor", "retail banking", "bank earnings", "financial services"
        ],
        "stocks": [
            "stock", "equity", "shares", "stock market", "nasdaq", "dow jones", "s&p", 
            "s&p 500", "nyse", "ipo", "public offering", "listed", "equity market",
            "shareholders", "stockholders", "equities", "stock exchange", "traders"
        ],
        "bonds": [
            "bond", "treasury", "yield", "debt securities", "fixed income", "coupon", 
            "government bonds", "corporate bonds", "municipal bonds", "t-bill",
            "sovereign debt", "treasury bills", "treasury notes", "debt instruments",
            "bond market", "bond yield", "yield curve", "junk bonds", "high yield bonds"
        ],
        "housing": [
            "housing", "real estate", "property", "home prices", "mortgage", "housing market", 
            "home sales", "real estate market", "residential", "commercial property",
            "home builders", "housing sector", "rent", "rental", "housing bubble",
            "property values", "home ownership", "real estate sector", "construction"
        ],
        "technology": [
            "tech", "technology", "ai", "artificial intelligence", "digital", "innovation", 
            "startup", "software", "hardware", "semiconductor", "computing", "internet", "tech stocks",
            "big tech", "technology sector", "tech industry", "silicon valley", "tech giants"
        ],
        "energy": [
            "energy", "oil", "gas", "crude", "petroleum", "energy market", "opec", 
            "oil prices", "natural gas", "energy sector", "fuel", "barrel", "wti",
            "brent crude", "energy stocks", "renewable energy", "fossil fuels"
        ],
        "cryptocurrency": [
            "crypto", "cryptocurrency", "bitcoin", "ethereum", "digital currency", 
            "blockchain", "token", "coin", "defi", "decentralized finance", "mining",
            "nft", "wallet", "altcoin", "crypto market", "crypto exchange", "digital assets"
        ],
        "global_markets": [
            "global", "international", "overseas", "world markets", "international trade", 
            "foreign exchange", "forex", "emerging markets", "global economy", "trade",
            "global economic", "worldwide", "cross-border", "global investors", "geopolitical"
        ],
        "financial_analysis": [
            "analysis", "analyst", "research", "report", "forecast", "projection", 
            "estimate", "financial statement", "earnings", "performance metrics", "assessment",
            "evaluation", "financial model", "valuation", "financial data", "fundamental analysis"
        ],
        "investment": [
            "investment", "portfolio", "investor", "capital", "asset allocation", "diversification", 
            "wealth management", "mutual fund", "etf", "hedge fund", "private equity", "venture capital",
            "risk management", "asset class", "risk-adjusted", "investment strategy", "pension",
            "fund manager", "allocation", "institutional investors", "risk tolerance"
        ]
    }
    
    # Combine all text for analysis, with title repeated for emphasis
    all_text = f"{title} {title} {title} {summary_text} {blog_text}".lower()
    title_lower = title.lower()
    
    # Score each category based on keyword matches with title receiving more weight
    category_scores = {"general_finance": 5}  # Give general finance a base score
    total_keywords_found = 0
    
    # First, analyze the title specifically
    for category, keywords in category_keywords.items():
        title_score = 0
        for keyword in keywords:
            if keyword in title_lower:
                title_score += 10  # Heavy weight for title matches
                total_keywords_found += 1
        
        if title_score > 0:
            category_scores[category] = category_scores.get(category, 0) + title_score
    
    # Then analyze the full text
    for category, keywords in category_keywords.items():
        full_text_score = 0
        for keyword in keywords:
            if keyword in all_text:
                full_text_score += 1  # Lower weight for general content
                total_keywords_found += 1
        
        category_scores[category] = category_scores.get(category, 0) + full_text_score
    
    # Select the category with the highest score
    sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    best_category = sorted_categories[0][0]
    best_score = sorted_categories[0][1]
    
    # Calculate confidence (how dominant the top category is)
    # Compare to second best if available
    second_best_score = sorted_categories[1][1] if len(sorted_categories) > 1 else 0
    confidence = best_score / (best_score + second_best_score) if (best_score + second_best_score) > 0 else 0
    
    # If confidence is too low, look for strong keyword matches in title
    if confidence < 0.75:
        print(f"⚠️ Low confidence ({confidence:.2f}) for category '{best_category}', checking title keywords...")
        
        # Look for direct keyword matches in title
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                # If we find a direct match in the title, use this category
                if keyword in title_lower and len(keyword) > 4:  # Only consider substantial keywords
                    best_category = category
                    print(f"✅ Direct title match: '{keyword}' → selecting category '{best_category}'")
                    confidence = 0.85  # Assume high confidence for direct title matches
                    break
            if confidence >= 0.75:
                break
    
    # Final fallback - if confidence is still too low, use general finance
    if confidence < 0.75:
        print(f"⚠️ Confidence still too low ({confidence:.2f}), falling back to general finance")
        best_category = "general_finance"
    
    # Pick an image from the best category
    selected_image = random.choice(image_categories[best_category])
    
    print(f"✅ Selected image for category '{best_category}' with {confidence:.2f} confidence")
    
    # Add additional fallback to ensure image works
    try:
        # Try making a HEAD request to check if the image exists
        response = requests.head(selected_image, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️ Selected image URL is not accessible: {e}")
        # Fall back to a guaranteed working image
        selected_image = "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1024"
        print(f"⚠️ Falling back to guaranteed working image: {selected_image}")
    
    return selected_image


def download_image(url: str) -> bytes:
    """Download image from URL and return the binary data"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"❌ Failed to download image: {e}")
        # If download fails, return empty bytes
        return b''


def upload_image_to_wordpress(image_url: str, wp_username: str, wp_password: str, wp_site_url: str) -> dict:
    """Upload an image to WordPress media library from URL"""
    try:
        # First try to download the image
        img_data = download_image(image_url)
        if not img_data:
            raise Exception("Failed to download image")
            
        # Generate a unique filename to avoid caching issues
        timestamp = int(time.time())
        filename = f"finance_header_{timestamp}.jpg"
        
        # Upload to WordPress
        media = requests.post(
            f"{wp_site_url}/wp-json/wp/v2/media",
            auth=(wp_username, wp_password),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            files={"file": (filename, img_data, "image/jpeg")}
        )
        media.raise_for_status()
        
        # Return the media object
        media_obj = media.json()
        print(f"✅ Uploaded image to WordPress with ID: {media_obj.get('id', 'unknown')}")
        return media_obj
    except Exception as e:
        print(f"❌ Failed to upload image to WordPress: {e}")
        # Return dummy data to allow the process to continue
        return {"id": 0, "source_url": ""}
