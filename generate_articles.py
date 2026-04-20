"""
AutoBlog Article Generator - FULL VERSION
- Latest news topics from NewsAPI
- Groq API for article writing
- Featured images from Unsplash (free)
- Proper slug consistency
- Full SEO: title, meta, schema, OG tags
- Beautiful design with logo, menu, categories, footer
"""

import os, json, time, random, requests, re
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Template

# ── CONFIG ─────────────────────────────────────────────────────────────────────
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
NEWS_API_KEY     = os.environ.get("NEWS_API_KEY", "")
UNSPLASH_KEY     = os.environ.get("UNSPLASH_KEY", "")   # optional, free
SITE_URL         = os.environ.get("SITE_URL", "https://marketsnewstoday.info")
SITE_NAME        = os.environ.get("SITE_NAME", "Markets News Today")
SITE_TAGLINE     = os.environ.get("SITE_TAGLINE", "Latest News & Market Insights")
OUTPUT_DIR       = Path("output")
POSTS_DIR        = OUTPUT_DIR / "posts"
ARTICLES_PER_RUN = int(os.environ.get("ARTICLES_PER_RUN", "10"))

CATEGORIES = ["Business","Technology","Finance","World","Sports","Health","Travel","Science","Entertainment","Politics"]

WIKI_TOPICS = [
    "Stock market trends 2025","Artificial intelligence business","Cryptocurrency regulation",
    "Electric vehicle market","Climate change economy","Remote work trends",
    "Social media marketing","E-commerce growth","Cybersecurity threats",
    "Space exploration 2025","Mental health workplace","Renewable energy investment",
    "Inflation consumer prices","Housing market forecast","Global trade war",
    "Tech startup funding","Blockchain technology","Digital banking",
    "Healthcare innovation","Supply chain disruption",
]

# ── HELPERS ────────────────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:70]

def load_published() -> set:
    p = OUTPUT_DIR / "published.json"
    return set(json.loads(p.read_text())) if p.exists() else set()

def save_published(slugs: set):
    (OUTPUT_DIR / "published.json").write_text(json.dumps(list(slugs), indent=2))

def load_posts_index() -> list:
    p = OUTPUT_DIR / "posts_index.json"
    return json.loads(p.read_text()) if p.exists() else []

def save_posts_index(posts: list):
    (OUTPUT_DIR / "posts_index.json").write_text(json.dumps(posts, indent=2))

# ── UNSPLASH IMAGE ─────────────────────────────────────────────────────────────
def get_image(keyword: str) -> str:
    """Get free image URL from Unsplash or fallback to placeholder."""
    if UNSPLASH_KEY:
        try:
            r = requests.get(
                "https://api.unsplash.com/photos/random",
                params={"query": keyword, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
                timeout=8,
            )
            if r.status_code == 200:
                return r.json()["urls"]["regular"]
        except Exception:
            pass
    # Fallback: Picsum random image based on keyword hash
    seed = abs(hash(keyword)) % 1000
    return f"https://picsum.photos/seed/{seed}/1200/600"

# ── TOPIC FETCHERS ─────────────────────────────────────────────────────────────
def fetch_news_topics(count: int) -> list[dict]:
    if not NEWS_API_KEY:
        return []
    try:
        r = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"language": "en", "pageSize": min(count, 100), "apiKey": NEWS_API_KEY},
            timeout=10,
        )
        topics = []
        for a in r.json().get("articles", []):
            title = a.get("title", "")
            desc  = a.get("description", "") or ""
            if title and "[Removed]" not in title:
                topics.append({"title": title, "hint": desc[:300]})
        return topics
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []

def build_topic_list(count: int) -> list[dict]:
    topics = fetch_news_topics(count)
    pool = WIKI_TOPICS.copy()
    random.shuffle(pool)
    while len(topics) < count and pool:
        topics.append({"title": pool.pop(), "hint": ""})
    return topics[:count]

# ── GROQ ARTICLE WRITER ────────────────────────────────────────────────────────
def write_article(topic: str, hint: str) -> dict | None:
    now = datetime.now()
    prompt = f"""Write a fresh, current news article for {now.strftime('%B %Y')} about: "{topic}"

Context: {hint}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "title": "Compelling news headline 55-65 chars",
  "slug": "url-slug-max-60-chars",
  "meta_description": "SEO description exactly 150-158 chars",
  "focus_keyword": "main keyword",
  "category": "one of: Business/Technology/Finance/World/Sports/Health/Travel/Science/Entertainment/Politics",
  "image_keyword": "2-3 word image search term",
  "article_html": "<h2>Introduction heading</h2><p>Full article minimum 900 words using h2, h3, p, ul, strong tags. Make it current, engaging, factual.</p>",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "read_time": "5 min read"
}}

IMPORTANT:
- slug must exactly match the title converted to lowercase-with-hyphens
- Article must sound like it was written TODAY in {now.strftime('%B %Y')}
- Minimum 900 words
- No copied content"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "max_tokens": 2500,
                "temperature": 0.8,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        raw = r.json()["choices"][0]["message"]["content"].strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        # FORCE slug to match title — this fixes the 404 issue
        data["slug"] = slugify(data["title"])
        return data
    except Exception as e:
        print(f"  ✗ Groq error: {e}")
        return None

# ── HTML TEMPLATES ─────────────────────────────────────────────────────────────
POST_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} | {{ site_name }}</title>
<meta name="description" content="{{ meta_description }}">
<meta name="keywords" content="{{ focus_keyword }}, {{ tags|join(', ') }}">
<meta name="robots" content="index, follow">
<meta name="author" content="{{ site_name }}">
<link rel="canonical" href="{{ site_url }}/posts/{{ slug }}.html">
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ meta_description }}">
<meta property="og:image" content="{{ image_url }}">
<meta property="og:url" content="{{ site_url }}/posts/{{ slug }}.html">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ title }}">
<meta name="twitter:description" content="{{ meta_description }}">
<meta name="twitter:image" content="{{ image_url }}">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Article","headline":"{{ title }}","description":"{{ meta_description }}","image":"{{ image_url }}","datePublished":"{{ date_iso }}","dateModified":"{{ date_iso }}","author":{"@type":"Organization","name":"{{ site_name }}"},"publisher":{"@type":"Organization","name":"{{ site_name }}","url":"{{ site_url }}"},"mainEntityOfPage":{"@type":"WebPage","@id":"{{ site_url }}/posts/{{ slug }}.html"}}
</script>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<header class="site-header">
  <div class="container header-inner">
    <a href="../index.html" class="logo">
      <span class="logo-icon">📈</span>
      <span class="logo-text">{{ site_name }}</span>
    </a>
    <nav class="main-nav">
      <a href="../index.html">Home</a>
      <a href="../category-business.html">Business</a>
      <a href="../category-technology.html">Tech</a>
      <a href="../category-finance.html">Finance</a>
      <a href="../category-world.html">World</a>
      <a href="../networth/index.html">Net Worth</a>
    </nav>
  </div>
</header>

<main class="container post-page">
  <div class="post-header">
    <div class="post-header-meta">
      <a href="../category-{{ category|lower }}.html" class="category">{{ category }}</a>
      <span class="dot">·</span>
      <time datetime="{{ date_iso }}">{{ date_human }}</time>
      <span class="dot">·</span>
      <span class="read-time">{{ read_time }}</span>
    </div>
    <h1>{{ title }}</h1>
    <p class="post-excerpt">{{ meta_description }}</p>
  </div>
  <div class="post-featured-img">
    <img src="{{ image_url }}" alt="{{ title }}" loading="lazy" width="1200" height="600">
  </div>
  <article class="post-content">
    {{ article_html }}
  </article>
  <div class="post-footer">
    <div class="post-tags">
      {% for tag in tags %}<a href="../index.html" class="tag">#{{ tag }}</a>{% endfor %}
    </div>
  </div>
</main>

<footer class="site-footer">
  <div class="container footer-inner">
    <div class="footer-brand">
      <span class="logo-icon">📈</span>
      <span class="logo-text">{{ site_name }}</span>
      <p>{{ site_tagline }}</p>
    </div>
    <div class="footer-links">
      <a href="../index.html">Home</a>
      <a href="../networth/index.html">Net Worth</a>
      <a href="../sitemap.xml">Sitemap</a>
    </div>
    <p class="footer-copy">&copy; {{ year }} {{ site_name }}. All rights reserved.</p>
  </div>
</footer>
</body>
</html>'''

INDEX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ site_name }} — {{ site_tagline }}</title>
<meta name="description" content="{{ site_tagline }} — Latest news on business, finance, technology, world events and more.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{{ site_url }}/">
<meta property="og:title" content="{{ site_name }}">
<meta property="og:description" content="{{ site_tagline }}">
<meta property="og:url" content="{{ site_url }}/">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"WebSite","name":"{{ site_name }}","url":"{{ site_url }}","description":"{{ site_tagline }}"}
</script>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site-header">
  <div class="container header-inner">
    <a href="index.html" class="logo">
      <span class="logo-icon">📈</span>
      <span class="logo-text">{{ site_name }}</span>
    </a>
    <nav class="main-nav">
      <a href="index.html">Home</a>
      <a href="category-business.html">Business</a>
      <a href="category-technology.html">Tech</a>
      <a href="category-finance.html">Finance</a>
      <a href="category-world.html">World</a>
      <a href="networth/index.html">Net Worth</a>
    </nav>
  </div>
</header>

{% if posts %}
<div class="hero-post">
  <div class="container">
    <a href="posts/{{ posts[0].slug }}.html" class="hero-link">
      <div class="hero-img-wrap">
        <img src="{{ posts[0].image_url }}" alt="{{ posts[0].title }}" loading="eager">
      </div>
      <div class="hero-content">
        <span class="category">{{ posts[0].category }}</span>
        <h1>{{ posts[0].title }}</h1>
        <p>{{ posts[0].meta_description }}</p>
        <span class="hero-meta">{{ posts[0].date_human }} · {{ posts[0].read_time }}</span>
      </div>
    </a>
  </div>
</div>
{% endif %}

<main class="container">
  <div class="section-header">
    <h2>Latest Articles</h2>
    <div class="cat-filter">
      {% for cat in categories %}
      <a href="category-{{ cat|lower }}.html" class="cat-btn">{{ cat }}</a>
      {% endfor %}
    </div>
  </div>

  <div class="post-grid">
    {% for post in posts[1:] %}
    <article class="post-card">
      <a href="posts/{{ post.slug }}.html" class="card-img-link">
        <img src="{{ post.image_url }}" alt="{{ post.title }}" loading="lazy" width="400" height="220">
      </a>
      <div class="card-body">
        <div class="card-meta">
          <a href="category-{{ post.category|lower }}.html" class="category">{{ post.category }}</a>
          <time>{{ post.date_human }}</time>
        </div>
        <h3><a href="posts/{{ post.slug }}.html">{{ post.title }}</a></h3>
        <p>{{ post.meta_description[:100] }}...</p>
        <a href="posts/{{ post.slug }}.html" class="read-more">Read More →</a>
      </div>
    </article>
    {% endfor %}
  </div>
</main>

<footer class="site-footer">
  <div class="container footer-inner">
    <div class="footer-brand">
      <span class="logo-icon">📈</span>
      <span class="logo-text">{{ site_name }}</span>
      <p>{{ site_tagline }}</p>
    </div>
    <div class="footer-links">
      <a href="index.html">Home</a>
      <a href="networth/index.html">Net Worth</a>
      <a href="sitemap.xml">Sitemap</a>
    </div>
    <p class="footer-copy">&copy; {{ year }} {{ site_name }}. All rights reserved.</p>
  </div>
</footer>
</body>
</html>'''

CATEGORY_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ category }} News | {{ site_name }}</title>
<meta name="description" content="Latest {{ category }} news and updates on {{ site_name }}.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{{ site_url }}/category-{{ category|lower }}.html">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site-header">
  <div class="container header-inner">
    <a href="index.html" class="logo">
      <span class="logo-icon">📈</span>
      <span class="logo-text">{{ site_name }}</span>
    </a>
    <nav class="main-nav">
      <a href="index.html">Home</a>
      <a href="category-business.html">Business</a>
      <a href="category-technology.html">Tech</a>
      <a href="category-finance.html">Finance</a>
      <a href="category-world.html">World</a>
      <a href="networth/index.html">Net Worth</a>
    </nav>
  </div>
</header>
<main class="container">
  <div class="cat-page-header">
    <h1>{{ category }} News</h1>
    <p>Latest {{ category }} articles and updates</p>
  </div>
  <div class="post-grid">
    {% for post in posts %}
    <article class="post-card">
      <a href="posts/{{ post.slug }}.html" class="card-img-link">
        <img src="{{ post.image_url }}" alt="{{ post.title }}" loading="lazy" width="400" height="220">
      </a>
      <div class="card-body">
        <div class="card-meta">
          <span class="category">{{ post.category }}</span>
          <time>{{ post.date_human }}</time>
        </div>
        <h3><a href="posts/{{ post.slug }}.html">{{ post.title }}</a></h3>
        <p>{{ post.meta_description[:100] }}...</p>
        <a href="posts/{{ post.slug }}.html" class="read-more">Read More →</a>
      </div>
    </article>
    {% endfor %}
  </div>
</main>
<footer class="site-footer">
  <div class="container footer-inner">
    <div class="footer-brand">
      <span class="logo-icon">📈</span>
      <span class="logo-text">{{ site_name }}</span>
      <p>{{ site_tagline }}</p>
    </div>
    <p class="footer-copy">&copy; {{ year }} {{ site_name }}. All rights reserved.</p>
  </div>
</footer>
</body>
</html>'''

# ── BUILDERS ───────────────────────────────────────────────────────────────────
def build_post(data: dict) -> str:
    now = datetime.now(timezone.utc)
    return Template(POST_HTML).render(
        **data, site_name=SITE_NAME, site_url=SITE_URL, site_tagline=SITE_TAGLINE,
        date_iso=now.isoformat(), date_human=now.strftime("%B %d, %Y"), year=now.year,
    )

def rebuild_homepage(posts: list):
    tpl = Template(INDEX_HTML)
    html = tpl.render(
        posts=sorted(posts, key=lambda x: x["date_iso"], reverse=True)[:50],
        categories=CATEGORIES, site_name=SITE_NAME,
        site_url=SITE_URL, site_tagline=SITE_TAGLINE, year=datetime.now().year,
    )
    (OUTPUT_DIR / "index.html").write_text(html)

def rebuild_categories(posts: list):
    for cat in CATEGORIES:
        cat_posts = [p for p in posts if p.get("category","").lower() == cat.lower()]
        html = Template(CATEGORY_HTML).render(
            posts=sorted(cat_posts, key=lambda x: x["date_iso"], reverse=True),
            category=cat, site_name=SITE_NAME, site_url=SITE_URL,
            site_tagline=SITE_TAGLINE, year=datetime.now().year,
        )
        (OUTPUT_DIR / f"category-{cat.lower()}.html").write_text(html)

def rebuild_sitemap(posts: list):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             f'  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>']
    for cat in CATEGORIES:
        lines.append(f'  <url><loc>{SITE_URL}/category-{cat.lower()}.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>')
    for p in posts:
        lines.append(f'  <url><loc>{SITE_URL}/posts/{p["slug"]}.html</loc><lastmod>{p["date_iso"][:10]}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>')
    lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines))

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(exist_ok=True)

    published   = load_published()
    posts_index = load_posts_index()

    print(f"📰 Fetching {ARTICLES_PER_RUN} topics...")
    topics = build_topic_list(ARTICLES_PER_RUN)

    new_count = 0
    for i, topic_data in enumerate(topics):
        title = topic_data["title"]
        slug  = slugify(title)

        if slug in published:
            print(f"  ↷ Skip: {title}")
            continue

        print(f"  ✍  [{i+1}/{len(topics)}] {title}")
        article = write_article(title, topic_data.get("hint", ""))
        if not article:
            continue

        # Force correct slug
        article["slug"] = slugify(article["title"])

        # Get featured image
        image_url = get_image(article.get("image_keyword", article["focus_keyword"]))
        article["image_url"] = image_url

        # Save post HTML
        now = datetime.now(timezone.utc)
        html = build_post(article)
        (POSTS_DIR / f"{article['slug']}.html").write_text(html)

        # Add to index
        posts_index.append({
            "slug":             article["slug"],
            "title":            article["title"],
            "meta_description": article["meta_description"],
            "category":         article.get("category", "World"),
            "tags":             article.get("tags", []),
            "image_url":        image_url,
            "read_time":        article.get("read_time", "5 min read"),
            "date_iso":         now.isoformat(),
            "date_human":       now.strftime("%B %d, %Y"),
        })
        published.add(article["slug"])
        new_count += 1
        time.sleep(1.2)

    print(f"\n✅ Generated {new_count} articles")
    print("🏠 Rebuilding homepage...")
    rebuild_homepage(posts_index)
    print("📂 Rebuilding categories...")
    rebuild_categories(posts_index)
    print("🗺  Rebuilding sitemap...")
    rebuild_sitemap(posts_index)
    save_published(published)
    save_posts_index(posts_index)
    print("🎉 Done!")

if __name__ == "__main__":
    main()
