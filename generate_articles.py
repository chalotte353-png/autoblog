"""
AutoBlog Article Generator
- Fetches topics from NewsAPI + Wikipedia
- Generates articles via Groq API (free)
- Creates SEO-optimized HTML files
- Updates homepage + sitemap
"""

import os
import json
import time
import random
import requests
import re
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Template

# ─── CONFIG ────────────────────────────────────────────────────────────────────
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
NEWS_API_KEY     = os.environ.get("NEWS_API_KEY", "")   # newsapi.org free key
SITE_URL         = os.environ.get("SITE_URL", "https://yoursite.com")
SITE_NAME        = os.environ.get("SITE_NAME", "YourBlog")
SITE_TAGLINE     = os.environ.get("SITE_TAGLINE", "Fresh News & Insights")
OUTPUT_DIR       = Path("output")          # built files go here
POSTS_DIR        = OUTPUT_DIR / "posts"
ARTICLES_PER_RUN = int(os.environ.get("ARTICLES_PER_RUN", "50"))  # 50 per run × 8 runs = 400/day

# Topics to pull from Wikipedia when NewsAPI quota runs out
WIKI_TOPICS = [
    "Artificial intelligence", "Climate change", "Space exploration",
    "Cryptocurrency", "Health and wellness", "Technology trends",
    "Electric vehicles", "Renewable energy", "Mental health",
    "Machine learning", "Cybersecurity", "Biotechnology",
    "Social media", "Remote work", "Personal finance",
    "Fitness", "Nutrition", "Travel", "History", "Science",
    "Economics", "Psychology", "Philosophy", "Education",
    "Environment", "Politics", "Business", "Sports",
    "Entertainment", "Culture", "Food", "Fashion",
]

# ─── HELPERS ───────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:80]


def load_published() -> set:
    p = OUTPUT_DIR / "published.json"
    if p.exists():
        return set(json.loads(p.read_text()))
    return set()


def save_published(slugs: set):
    p = OUTPUT_DIR / "published.json"
    p.write_text(json.dumps(list(slugs), indent=2))


# ─── TOPIC FETCHERS ────────────────────────────────────────────────────────────

def fetch_news_topics(count: int) -> list[dict]:
    """Fetch trending headlines from NewsAPI (ideas only, not content)."""
    if not NEWS_API_KEY:
        return []
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"language": "en", "pageSize": min(count, 100), "apiKey": NEWS_API_KEY}
        r = requests.get(url, params=params, timeout=10)
        articles = r.json().get("articles", [])
        topics = []
        for a in articles:
            title = a.get("title", "")
            desc  = a.get("description", "") or ""
            if title and "[Removed]" not in title:
                topics.append({"title": title, "hint": desc[:200]})
        return topics
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []


def fetch_wiki_summary(topic: str) -> str:
    """Get Wikipedia intro paragraph as background context."""
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + topic.replace(" ", "_")
        r = requests.get(url, timeout=10)
        data = r.json()
        return data.get("extract", "")[:800]
    except Exception:
        return ""


def build_topic_list(count: int) -> list[dict]:
    topics = fetch_news_topics(count)
    # Fill rest from Wikipedia random topics
    wiki_pool = WIKI_TOPICS.copy()
    random.shuffle(wiki_pool)
    while len(topics) < count and wiki_pool:
        t = wiki_pool.pop()
        hint = fetch_wiki_summary(t)
        topics.append({"title": t, "hint": hint})
        time.sleep(0.3)
    return topics[:count]


# ─── ARTICLE WRITER ────────────────────────────────────────────────────────────

def write_article(topic: str, hint: str) -> dict | None:
    """Call Claude API to write a full SEO article. Returns structured dict."""
    prompt = f"""Write a comprehensive, original, SEO-optimized blog article about: "{topic}"

Background context (do NOT copy — use only as inspiration):
{hint}

Return ONLY valid JSON (no markdown fences) with these exact keys:
{{
  "title": "Compelling SEO title (55-60 chars)",
  "slug": "url-friendly-slug",
  "meta_description": "SEO meta description 150-160 chars",
  "focus_keyword": "main keyword phrase",
  "article_html": "<article body as HTML — use <h2>, <h3>, <p>, <ul>, <strong> tags only — minimum 800 words>",
  "tags": ["tag1", "tag2", "tag3"],
  "category": "one category name"
}}

Rules:
- 100% original, do not copy from anywhere
- Minimum 800 words in article_html
- Use H2 and H3 subheadings
- Include a conclusion section
- Natural keyword usage, no stuffing
- Engaging, human-sounding tone"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
            timeout=60,
        )
        raw = r.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return data
    except Exception as e:
        print(f"  ✗ Groq error for '{topic}': {e}")
        return None


# ─── HTML BUILDER ──────────────────────────────────────────────────────────────

POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} | {{ site_name }}</title>
<meta name="description" content="{{ meta_description }}">
<meta name="keywords" content="{{ focus_keyword }}, {{ tags|join(', ') }}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{{ site_url }}/posts/{{ slug }}.html">
<!-- Open Graph -->
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ meta_description }}">
<meta property="og:url" content="{{ site_url }}/posts/{{ slug }}.html">
<meta property="og:type" content="article">
<!-- Schema.org -->
<script type="application/ld+json">
{
  "@context":"https://schema.org",
  "@type":"Article",
  "headline":"{{ title }}",
  "description":"{{ meta_description }}",
  "datePublished":"{{ date_iso }}",
  "publisher":{"@type":"Organization","name":"{{ site_name }}","url":"{{ site_url }}"}
}
</script>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<header class="site-header">
  <div class="container">
    <a href="../index.html" class="logo">{{ site_name }}</a>
    <nav><a href="../index.html">Home</a></nav>
  </div>
</header>
<main class="container post-page">
  <article>
    <div class="post-meta">
      <span class="category">{{ category }}</span>
      <time datetime="{{ date_iso }}">{{ date_human }}</time>
    </div>
    <h1>{{ title }}</h1>
    <div class="post-body">
      {{ article_html }}
    </div>
    <div class="post-tags">
      {% for tag in tags %}<span class="tag">{{ tag }}</span>{% endfor %}
    </div>
  </article>
</main>
<footer class="site-footer">
  <div class="container">
    <p>&copy; {{ year }} {{ site_name }}. All rights reserved.</p>
  </div>
</footer>
</body>
</html>"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ site_name }} — {{ site_tagline }}</title>
<meta name="description" content="{{ site_tagline }}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{{ site_url }}/">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site-header">
  <div class="container">
    <a href="index.html" class="logo">{{ site_name }}</a>
    <p class="tagline">{{ site_tagline }}</p>
  </div>
</header>
<main class="container">
  <div class="post-grid">
    {% for post in posts %}
    <article class="post-card">
      <div class="post-card-meta">
        <span class="category">{{ post.category }}</span>
        <time>{{ post.date_human }}</time>
      </div>
      <h2><a href="posts/{{ post.slug }}.html">{{ post.title }}</a></h2>
      <p>{{ post.meta_description }}</p>
      <a href="posts/{{ post.slug }}.html" class="read-more">Read More →</a>
    </article>
    {% endfor %}
  </div>
</main>
<footer class="site-footer">
  <div class="container">
    <p>&copy; {{ year }} {{ site_name }}. All rights reserved.</p>
  </div>
</footer>
</body>
</html>"""


def build_post_html(data: dict) -> str:
    now = datetime.now(timezone.utc)
    tpl = Template(POST_TEMPLATE)
    return tpl.render(
        **data,
        site_name=SITE_NAME,
        site_url=SITE_URL,
        date_iso=now.isoformat(),
        date_human=now.strftime("%B %d, %Y"),
        year=now.year,
    )


def load_posts_index() -> list[dict]:
    p = OUTPUT_DIR / "posts_index.json"
    if p.exists():
        return json.loads(p.read_text())
    return []


def save_posts_index(posts: list[dict]):
    p = OUTPUT_DIR / "posts_index.json"
    p.write_text(json.dumps(posts, indent=2))


def rebuild_homepage(posts: list[dict]):
    tpl = Template(INDEX_TEMPLATE)
    html = tpl.render(
        posts=sorted(posts, key=lambda x: x["date_iso"], reverse=True)[:100],
        site_name=SITE_NAME,
        site_url=SITE_URL,
        site_tagline=SITE_TAGLINE,
        year=datetime.now().year,
    )
    (OUTPUT_DIR / "index.html").write_text(html)


def rebuild_sitemap(posts: list[dict]):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             f'  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>']
    for p in posts:
        lines.append(
            f'  <url><loc>{SITE_URL}/posts/{p["slug"]}.html</loc>'
            f'<lastmod>{p["date_iso"][:10]}</lastmod>'
            f'<changefreq>monthly</changefreq><priority>0.8</priority></url>'
        )
    lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines))


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(exist_ok=True)

    published = load_published()
    posts_index = load_posts_index()

    print(f"📰 Fetching {ARTICLES_PER_RUN} topics...")
    topics = build_topic_list(ARTICLES_PER_RUN)

    new_count = 0
    for i, topic_data in enumerate(topics):
        title = topic_data["title"]
        slug  = slugify(title)

        if slug in published:
            print(f"  ↷ Skip (exists): {title}")
            continue

        print(f"  ✍  [{i+1}/{len(topics)}] Writing: {title}")
        article = write_article(title, topic_data.get("hint", ""))
        if not article:
            continue

        # Ensure slug is consistent
        article["slug"] = slugify(article.get("slug", slug))

        # Save HTML post file
        html = build_post_html(article)
        (POSTS_DIR / f"{article['slug']}.html").write_text(html)

        # Update index
        now = datetime.now(timezone.utc)
        posts_index.append({
            "slug": article["slug"],
            "title": article["title"],
            "meta_description": article["meta_description"],
            "category": article.get("category", "General"),
            "tags": article.get("tags", []),
            "date_iso": now.isoformat(),
            "date_human": now.strftime("%B %d, %Y"),
        })
        published.add(article["slug"])
        new_count += 1

        # Be nice to the API
        time.sleep(1.5)

    print(f"\n✅ Generated {new_count} new articles")

    # Rebuild homepage + sitemap
    print("🏠 Rebuilding homepage...")
    rebuild_homepage(posts_index)
    print("🗺  Rebuilding sitemap...")
    rebuild_sitemap(posts_index)

    # Persist state
    save_published(published)
    save_posts_index(posts_index)

    print("🎉 Done!")


if __name__ == "__main__":
    main()
