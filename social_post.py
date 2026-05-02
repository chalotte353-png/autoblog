"""
Social Media Auto Poster — Twitter/X
Har run ke baad latest posts tweet karta hai
"""

import os
import json
import requests
from pathlib import Path
from requests_oauthlib import OAuth1

# Twitter API Keys
CONSUMER_KEY        = os.environ["TWITTER_CONSUMER_KEY"]
CONSUMER_SECRET     = os.environ["TWITTER_CONSUMER_SECRET"]
ACCESS_TOKEN        = os.environ["TWITTER_ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["TWITTER_ACCESS_SECRET"]

SITE_URL   = os.environ.get("SITE_URL", "https://marketsnewstoday.info")
OUTPUT_DIR = Path("output")

POSTED_FILE = OUTPUT_DIR / "social_posted.json"

def load_posted():
    try:
        return set(json.loads(POSTED_FILE.read_text()))
    except:
        return set()

def save_posted(posted):
    POSTED_FILE.write_text(json.dumps(list(posted)))

def load_latest_posts(limit=3):
    try:
        posts = json.loads((OUTPUT_DIR / "posts_index.json").read_text())
        # Sort by date — latest first
        posts = sorted(posts, key=lambda x: x.get("date_iso",""), reverse=True)
        return posts[:limit]
    except:
        return []

def tweet(text):
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        auth=auth,
        json={"text": text},
        headers={"Content-Type": "application/json"}
    )
    return r.status_code == 201, r.json()

def make_tweet_text(post):
    title = post.get("title", "")
    slug  = post.get("slug", "")
    cat   = post.get("category", "")
    url   = f"{SITE_URL}/posts/{slug}.html"

    # Category hashtags
    cat_tags = {
        "Crypto":        "#Crypto #Bitcoin",
        "Stocks":        "#Stocks #StockMarket",
        "Forex":         "#Forex #Trading",
        "Finance":       "#Finance #Economy",
        "Markets":       "#Markets #Trading",
        "Technology":    "#Tech #AI",
        "Business":      "#Business",
        "Politics":      "#Politics #News",
        "World":         "#WorldNews #Breaking",
        "Sports":        "#Sports",
        "Entertainment": "#Entertainment",
        "Health":        "#Health",
        "Science":       "#Science",
        "Travel":        "#Travel",
    }
    tags = cat_tags.get(cat, "#News")

    # Max tweet = 280 chars
    tweet = f"{title}\n\n{url}\n\n{tags}"
    if len(tweet) > 280:
        max_title = 280 - len(url) - len(tags) - 6
        title = title[:max_title] + "..."
        tweet = f"{title}\n\n{url}\n\n{tags}"

    return tweet

def main():
    posted = load_posted()
    posts  = load_latest_posts(limit=2)

    if not posts:
        print("No posts found!")
        return

    new_posted = 0
    for post in posts:
        slug = post.get("slug", "")
        if slug in posted:
            print(f"  Already posted: {slug}")
            continue

        text = make_tweet_text(post)
        print(f"  Tweeting: {post.get('title','')[:60]}")
        print(f"  Text: {text[:100]}...")

        ok, resp = tweet(text)
        if ok:
            posted.add(slug)
            new_posted += 1
            print(f"  ✅ Tweeted!")
        else:
            print(f"  ❌ Error: {resp}")

    save_posted(posted)
    print(f"\nDone! {new_posted} new tweets")

if __name__ == "__main__":
    main()
