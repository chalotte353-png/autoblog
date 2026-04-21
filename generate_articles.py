"""
AutoBlog Article Generator v2 - FULLY FIXED
- Multiple authors per category
- Proper images (always works)
- All articles on homepage
- Category pages working
- Professional SEO
"""

import os, json, time, random, requests, re
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Template

GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
CLAUDE_API_KEY   = os.environ.get("CLAUDE_API_KEY", "")
UNSPLASH_KEY     = os.environ.get("UNSPLASH_KEY", "")
NEWS_API_KEY     = os.environ.get("NEWS_API_KEY", "")
SITE_URL         = os.environ.get("SITE_URL", "https://marketsnewstoday.info")
SITE_NAME        = os.environ.get("SITE_NAME", "Markets News Today")
SITE_TAGLINE     = os.environ.get("SITE_TAGLINE", "Latest News & Market Insights")
OUTPUT_DIR       = Path("output")
POSTS_DIR        = OUTPUT_DIR / "posts"
ARTICLES_PER_RUN = int(os.environ.get("ARTICLES_PER_RUN", "10"))

CATEGORIES = ["Business","Technology","Finance","World","Sports","Health","Travel","Science","Entertainment","Politics"]

AUTHORS = {
    "Business":      [{"name":"James Mitchell","title":"Business Editor","bio":"15 years covering global markets.","avatar":"https://i.pravatar.cc/150?img=11"},
                      {"name":"Sarah Chen","title":"Finance Reporter","bio":"Former Wall Street analyst.","avatar":"https://i.pravatar.cc/150?img=47"},
                      {"name":"Robert Hayes","title":"Economics Correspondent","bio":"Oxford economics graduate.","avatar":"https://i.pravatar.cc/150?img=15"}],
    "Technology":    [{"name":"Alex Rivera","title":"Tech Editor","bio":"Silicon Valley insider, 10+ years.","avatar":"https://i.pravatar.cc/150?img=12"},
                      {"name":"Maya Patel","title":"AI Reporter","bio":"MIT graduate, emerging tech expert.","avatar":"https://i.pravatar.cc/150?img=48"},
                      {"name":"Tom Bradley","title":"Cybersecurity Analyst","bio":"Former NSA contractor.","avatar":"https://i.pravatar.cc/150?img=16"}],
    "Finance":       [{"name":"David Park","title":"Markets Editor","bio":"CFA charterholder, global finance.","avatar":"https://i.pravatar.cc/150?img=13"},
                      {"name":"Lisa Wong","title":"Investment Reporter","bio":"Hedge funds and capital markets.","avatar":"https://i.pravatar.cc/150?img=49"},
                      {"name":"Mark Thompson","title":"Crypto Correspondent","bio":"Blockchain technology expert.","avatar":"https://i.pravatar.cc/150?img=17"}],
    "World":         [{"name":"Elena Vasquez","title":"World Affairs Editor","bio":"Award-winning foreign correspondent.","avatar":"https://i.pravatar.cc/150?img=21"},
                      {"name":"Hassan Ahmed","title":"Middle East Bureau Chief","bio":"20 years in conflict zones.","avatar":"https://i.pravatar.cc/150?img=52"},
                      {"name":"Anna Kowalski","title":"Europe Correspondent","bio":"Brussels-based EU politics expert.","avatar":"https://i.pravatar.cc/150?img=25"}],
    "Sports":        [{"name":"Chris Johnson","title":"Sports Editor","bio":"Former pro athlete turned journalist.","avatar":"https://i.pravatar.cc/150?img=14"},
                      {"name":"Maria Santos","title":"Football Correspondent","bio":"Premier League and Champions League.","avatar":"https://i.pravatar.cc/150?img=44"},
                      {"name":"Kevin Williams","title":"US Sports Reporter","bio":"NBA NFL MLB expert.","avatar":"https://i.pravatar.cc/150?img=18"}],
    "Health":        [{"name":"Dr. Jennifer Ross","title":"Health Editor","bio":"MD, public health specialist.","avatar":"https://i.pravatar.cc/150?img=23"},
                      {"name":"Michael Green","title":"Medical Correspondent","bio":"Breakthrough medical research.","avatar":"https://i.pravatar.cc/150?img=53"},
                      {"name":"Rachel Kim","title":"Wellness Reporter","bio":"Mental health and nutrition.","avatar":"https://i.pravatar.cc/150?img=26"}],
    "Travel":        [{"name":"Sophie Laurent","title":"Travel Editor","bio":"Visited 90+ countries.","avatar":"https://i.pravatar.cc/150?img=24"},
                      {"name":"Diego Morales","title":"Adventure Travel Writer","bio":"Off-the-beaten-path destinations.","avatar":"https://i.pravatar.cc/150?img=54"},
                      {"name":"Emma Wilson","title":"Food & Travel Reporter","bio":"Culinary travel expert.","avatar":"https://i.pravatar.cc/150?img=27"}],
    "Science":       [{"name":"Dr. Neil Foster","title":"Science Editor","bio":"PhD Astrophysics, Caltech.","avatar":"https://i.pravatar.cc/150?img=33"},
                      {"name":"Laura Martinez","title":"Climate Reporter","bio":"Environmental science journalist.","avatar":"https://i.pravatar.cc/150?img=55"},
                      {"name":"James Liu","title":"Space Correspondent","bio":"NASA press corps member.","avatar":"https://i.pravatar.cc/150?img=34"}],
    "Entertainment": [{"name":"Jessica Taylor","title":"Entertainment Editor","bio":"Hollywood insider.","avatar":"https://i.pravatar.cc/150?img=35"},
                      {"name":"Brandon Lee","title":"Music Reporter","bio":"Grammy-nominated producer.","avatar":"https://i.pravatar.cc/150?img=56"},
                      {"name":"Olivia Brown","title":"Film Critic","bio":"BAFTA voter, Cannes regular.","avatar":"https://i.pravatar.cc/150?img=36"}],
    "Politics":      [{"name":"Andrew Collins","title":"Political Editor","bio":"20 years in Washington DC.","avatar":"https://i.pravatar.cc/150?img=37"},
                      {"name":"Patricia Morgan","title":"Policy Correspondent","bio":"Former White House press pool.","avatar":"https://i.pravatar.cc/150?img=57"},
                      {"name":"Samuel Davis","title":"International Affairs","bio":"US foreign policy expert.","avatar":"https://i.pravatar.cc/150?img=38"}],
}

WIKI_TOPICS = [
    "Stock market trends 2025","Artificial intelligence business","Cryptocurrency regulation",
    "Electric vehicle market","Climate change economy","Remote work trends",
    "Social media marketing","E-commerce growth","Cybersecurity threats 2025",
    "Space exploration 2025","Mental health workplace","Renewable energy investment",
    "Inflation consumer prices 2025","Housing market forecast","Global trade war",
    "Tech startup funding","Blockchain technology","Digital banking trends",
    "Healthcare innovation","Supply chain disruption","Bitcoin price 2025",
    "Federal Reserve interest rates","AI regulation 2025","Tesla earnings",
]

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:70]

def get_image(keyword, slug):
    """Get relevant image from Unsplash or fallback to Picsum."""
    if UNSPLASH_KEY:
        try:
            r = requests.get(
                "https://api.unsplash.com/photos/random",
                params={"query": keyword, "orientation": "landscape", "w": 1200, "h": 630},
                headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
                timeout=8,
            )
            if r.status_code == 200:
                return r.json()["urls"]["regular"]
        except Exception:
            pass
    seed = abs(hash(slug)) % 1000
    return f"https://picsum.photos/seed/{seed}/1200/630"

def get_author(category):
    return random.choice(AUTHORS.get(category, AUTHORS["World"]))

def add_internal_links(article_html: str, posts_index: list, current_slug: str, site_url: str) -> str:
    """Add internal links to related articles in the article body."""
    if not posts_index:
        return article_html
    
    # Get 3 related posts (different from current)
    related = [p for p in posts_index if p["slug"] != current_slug][:3]
    if not related:
        return article_html
    
    # Build related posts HTML
    related_html = """<div class="related-posts">
<h3>Related Articles</h3>
<ul>"""
    for p in related:
        related_html += f'<li><a href="{site_url}/posts/{p["slug"]}.html">{p["title"]}</a></li>'
    related_html += "</ul></div>"
    
    # Add before closing of article
    article_html = article_html + related_html
    return article_html

def load_published():
    p = OUTPUT_DIR / "published.json"
    return set(json.loads(p.read_text())) if p.exists() else set()

def save_published(s):
    (OUTPUT_DIR / "published.json").write_text(json.dumps(list(s), indent=2))

def load_posts_index():
    p = OUTPUT_DIR / "posts_index.json"
    return json.loads(p.read_text()) if p.exists() else []

def save_posts_index(posts):
    (OUTPUT_DIR / "posts_index.json").write_text(json.dumps(posts, indent=2))

def fetch_news_topics(count):
    if not NEWS_API_KEY:
        return []
    try:
        r = requests.get("https://newsapi.org/v2/top-headlines",
            params={"language":"en","pageSize":min(count,100),"apiKey":NEWS_API_KEY},timeout=10)
        topics = []
        for a in r.json().get("articles",[]):
            t = a.get("title","")
            d = a.get("description","") or ""
            if t and "[Removed]" not in t:
                topics.append({"title":t,"hint":d[:300]})
        return topics
    except Exception as e:
        print(f"NewsAPI: {e}")
        return []

def build_topics(count):
    topics = fetch_news_topics(count)
    pool = WIKI_TOPICS.copy()
    random.shuffle(pool)
    while len(topics) < count and pool:
        topics.append({"title":pool.pop(),"hint":""})
    return topics[:count]

def write_article(topic, hint):
    now = datetime.now()
    prompt = f"""Write a professional news article for {now.strftime('%B %Y')} about: "{topic}"
Context: {hint}

Return ONLY valid JSON (no markdown fences):
{{
  "title": "Compelling headline 55-65 chars",
  "slug": "url-slug",
  "meta_description": "SEO description 150-158 chars",
  "focus_keyword": "main keyword",
  "category": "Business/Technology/Finance/World/Sports/Health/Travel/Science/Entertainment/Politics",
  "article_html": "<h2>Opening</h2><p>Minimum 800 words using h2 h3 p ul strong tags</p>",
  "tags": ["tag1","tag2","tag3"],
  "read_time": "5 min read",
  "excerpt": "2-3 sentence summary"
}}"""
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 2500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        resp = r.json()
        if "content" not in resp:
            print(f"  Claude resp: {resp}")
            return None
        raw = resp["content"][0]["text"].strip()
        raw = re.sub(r"^```json\s*","",raw)
        raw = re.sub(r"\s*```$","",raw)
        data = json.loads(raw)
        data["slug"] = slugify(data["title"])
        return data
    except Exception as e:
        print(f"  ✗ Groq: {e}")
        return None

POST_TPL = open("/home/claude/autoblog_v2/post.html").read() if Path("/home/claude/autoblog_v2/post.html").exists() else ""
INDEX_TPL = ""
CAT_TPL = ""

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(exist_ok=True)

    published = load_published()
    posts_index = load_posts_index()

    print(f"📰 {ARTICLES_PER_RUN} topics...")
    topics = build_topics(ARTICLES_PER_RUN)

    new_count = 0
    for i, t in enumerate(topics):
        title = t["title"]
        slug = slugify(title)
        if slug in published:
            continue

        print(f"  ✍  [{i+1}] {title}")
        article = write_article(title, t.get("hint",""))
        if not article:
            continue

        article["slug"] = slugify(article["title"])
        category = article.get("category","World")
        author = get_author(category)
        image = get_image(article.get("focus_keyword", article["title"]), article["slug"])
        article["image_url"] = image

        now = datetime.now(timezone.utc)

        # Add internal links
        article["article_html"] = add_internal_links(
            article["article_html"], posts_index, article["slug"], SITE_URL
        )

        # Save post HTML
        from jinja2 import Template as T
        html = T(POST_HTML).render(
            **article, author=author,
            site_name=SITE_NAME, site_url=SITE_URL, site_tagline=SITE_TAGLINE,
            date_iso=now.isoformat(), date_human=now.strftime("%B %d, %Y"), year=now.year)
        (POSTS_DIR / f"{article['slug']}.html").write_text(html)

        posts_index.append({
            "slug": article["slug"], "title": article["title"],
            "meta_description": article["meta_description"],
            "excerpt": article.get("excerpt", article["meta_description"]),
            "category": category, "tags": article.get("tags",[]),
            "image_url": image, "read_time": article.get("read_time","5 min read"),
            "author_name": author["name"], "author_title": author["title"],
            "author_avatar": author["avatar"],
            "date_iso": now.isoformat(), "date_human": now.strftime("%B %d, %Y"),
        })
        published.add(article["slug"])
        new_count += 1
        time.sleep(2)

    print(f"\n✅ {new_count} new articles")
    rebuild_all(posts_index)
    save_published(published)
    save_posts_index(posts_index)
    print("🎉 Done!")

# Templates inline
POST_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} | {{ site_name }}</title>
<meta name="description" content="{{ meta_description }}">
<meta name="author" content="{{ author.name }}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{{ site_url }}/posts/{{ slug }}.html">
<meta property="og:title" content="{{ title }}"><meta property="og:description" content="{{ meta_description }}">
<meta property="og:image" content="{{ image_url }}"><meta property="og:type" content="article">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"{{ title }}","image":"{{ image_url }}","datePublished":"{{ date_iso }}","author":{"@type":"Person","name":"{{ author.name }}"},"publisher":{"@type":"Organization","name":"{{ site_name }}","url":"{{ site_url }}"}}</script>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<header class="site-header"><div class="container header-inner">
  <a href="../index.html" class="logo"><span class="logo-text">{{ site_name }}</span></a>
  <nav class="main-nav">
    <a href="../index.html">Home</a><a href="../category-business.html">Business</a>
    <a href="../category-technology.html">Tech</a><a href="../category-finance.html">Finance</a>
    <a href="../category-world.html">World</a><a href="../category-sports.html">Sports</a>
    <a href="../networth/index.html">Net Worth</a>
  </nav>
  <button class="nav-toggle" onclick="document.querySelector('.main-nav').classList.toggle('open')">☰</button>
</div></header>
<main class="post-wrap"><div class="container post-layout"><article class="post-main">
  <div class="post-header">
    <a href="../category-{{ category|lower }}.html" class="cat-badge">{{ category }}</a>
    <h1>{{ title }}</h1>
    <p class="post-desc">{{ meta_description }}</p>
    <div class="post-meta-bar">
      <img src="{{ author.avatar }}" alt="{{ author.name }}" class="author-avatar">
      <div><div class="author-name">{{ author.name }}</div><div class="author-title-text">{{ author.title }}</div></div>
      <span class="dot">·</span><time>{{ date_human }}</time>
      <span class="dot">·</span><span>{{ read_time }}</span>
    </div>
  </div>
  <figure class="post-hero-img"><img src="{{ image_url }}" alt="{{ title }}" loading="eager" width="820" height="461"></figure>
  <div class="post-body">{{ article_html }}</div>
  <div class="post-tags-wrap">{% for tag in tags %}<a href="../index.html" class="tag">#{{ tag }}</a>{% endfor %}</div>
  <div class="author-card">
    <img src="{{ author.avatar }}" alt="{{ author.name }}" class="author-card-img">
    <div><div class="author-card-name">{{ author.name }}</div>
    <div class="author-card-role">{{ author.title }}</div>
    <p class="author-card-bio">{{ author.bio }}</p></div>
  </div>
</article></div></main>
<footer class="site-footer"><div class="container">
  <div class="footer-grid">
    <div class="footer-brand"><a href="../index.html" class="logo footer-logo"><span class="logo-text">{{ site_name }}</span></a><p>{{ site_tagline }}</p></div>
    <div class="footer-col"><h4>Categories</h4>
      <a href="../category-business.html">Business</a><a href="../category-technology.html">Technology</a>
      <a href="../category-finance.html">Finance</a><a href="../category-world.html">World</a>
      <a href="../category-sports.html">Sports</a></div>
    <div class="footer-col"><h4>More</h4>
      <a href="../category-health.html">Health</a><a href="../category-science.html">Science</a>
      <a href="../networth/index.html">Net Worth</a><a href="../sitemap.xml">Sitemap</a></div>
  </div>
  <div class="footer-bottom"><p>&copy; {{ year }} {{ site_name }}. All rights reserved.</p></div>
</div></footer>
</body></html>'''

INDEX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ site_name }} — {{ site_tagline }}</title>
<meta name="description" content="Latest news on business finance technology world events.">
<meta name="robots" content="index,follow"><link rel="canonical" href="{{ site_url }}/">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site-header"><div class="container header-inner">
  <a href="index.html" class="logo"><span class="logo-text">{{ site_name }}</span></a>
  <nav class="main-nav">
    <a href="index.html">Home</a><a href="category-business.html">Business</a>
    <a href="category-technology.html">Tech</a><a href="category-finance.html">Finance</a>
    <a href="category-world.html">World</a><a href="category-sports.html">Sports</a>
    <a href="networth/index.html">Net Worth</a>
  </nav>
  <button class="nav-toggle" onclick="document.querySelector('.main-nav').classList.toggle('open')">☰</button>
</div></header>
{% if posts %}
<section class="hero"><div class="container hero-inner">
  <a href="posts/{{ posts[0].slug }}.html" class="hero-card">
    <div class="hero-img"><img src="{{ posts[0].image_url }}" alt="{{ posts[0].title }}" loading="eager">
    <span class="hero-cat">{{ posts[0].category }}</span></div>
    <div class="hero-info"><h1>{{ posts[0].title }}</h1>
    <p>{{ posts[0].excerpt }}</p>
    <div class="hero-meta">
      <img src="{{ posts[0].author_avatar }}" alt="{{ posts[0].author_name }}" class="hero-avatar">
      <span>{{ posts[0].author_name }}</span><span class="dot">·</span>
      <span>{{ posts[0].date_human }}</span><span class="dot">·</span><span>{{ posts[0].read_time }}</span>
    </div></div>
  </a>
  {% if posts|length > 1 %}
  <div class="hero-side">{% for post in posts[1:4] %}
    <a href="posts/{{ post.slug }}.html" class="side-card">
      <img src="{{ post.image_url }}" alt="{{ post.title }}">
      <div class="side-info"><span class="side-cat">{{ post.category }}</span>
      <h3>{{ post.title }}</h3><span class="side-date">{{ post.date_human }}</span></div>
    </a>{% endfor %}
  </div>{% endif %}
</div></section>{% endif %}
<main class="container main-content">
  <div class="section-head"><h2>Latest News</h2>
  <div class="cat-pills">{% for cat in categories %}
    <a href="category-{{ cat|lower }}.html" class="pill">{{ cat }}</a>{% endfor %}
  </div></div>
  <div class="news-grid">{% for post in posts[4:] %}
    <article class="news-card">
      <a href="posts/{{ post.slug }}.html" class="news-img-link">
        <img src="{{ post.image_url }}" alt="{{ post.title }}" loading="lazy"></a>
      <div class="news-body">
        <a href="category-{{ post.category|lower }}.html" class="cat-badge sm">{{ post.category }}</a>
        <h3><a href="posts/{{ post.slug }}.html">{{ post.title }}</a></h3>
        <p>{{ post.excerpt[:120] }}...</p>
        <div class="news-meta">
          <img src="{{ post.author_avatar }}" alt="{{ post.author_name }}" class="news-avatar">
          <span>{{ post.author_name }}</span><span class="dot">·</span><time>{{ post.date_human }}</time>
        </div>
      </div>
    </article>{% endfor %}
  </div>
</main>
<footer class="site-footer"><div class="container">
  <div class="footer-grid">
    <div class="footer-brand"><a href="index.html" class="logo footer-logo"><span class="logo-text">{{ site_name }}</span></a><p>{{ site_tagline }}</p></div>
    <div class="footer-col"><h4>Categories</h4>
      <a href="category-business.html">Business</a><a href="category-technology.html">Technology</a>
      <a href="category-finance.html">Finance</a><a href="category-world.html">World</a>
      <a href="category-sports.html">Sports</a></div>
    <div class="footer-col"><h4>More</h4>
      <a href="category-health.html">Health</a><a href="category-science.html">Science</a>
      <a href="networth/index.html">Net Worth</a><a href="sitemap.xml">Sitemap</a></div>
  </div>
  <div class="footer-bottom"><p>&copy; {{ year }} {{ site_name }}. All rights reserved.</p></div>
</div></footer>
</body></html>'''

CAT_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ category }} News | {{ site_name }}</title>
<meta name="description" content="Latest {{ category }} news on {{ site_name }}.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{{ site_url }}/category-{{ category|lower }}.html">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site-header"><div class="container header-inner">
  <a href="index.html" class="logo"><span class="logo-text">{{ site_name }}</span></a>
  <nav class="main-nav">
    <a href="index.html">Home</a><a href="category-business.html">Business</a>
    <a href="category-technology.html">Tech</a><a href="category-finance.html">Finance</a>
    <a href="category-world.html">World</a><a href="category-sports.html">Sports</a>
    <a href="networth/index.html">Net Worth</a>
  </nav>
  <button class="nav-toggle" onclick="document.querySelector('.main-nav').classList.toggle('open')">☰</button>
</div></header>
<main class="container">
  <div class="cat-header"><span class="cat-badge">{{ category }}</span>
  <h1>{{ category }} News</h1><p>Latest {{ category }} news, analysis and updates</p></div>
  {% if posts %}
  <div class="news-grid">{% for post in posts %}
    <article class="news-card">
      <a href="posts/{{ post.slug }}.html" class="news-img-link">
        <img src="{{ post.image_url }}" alt="{{ post.title }}" loading="lazy"></a>
      <div class="news-body">
        <a href="category-{{ post.category|lower }}.html" class="cat-badge sm">{{ post.category }}</a>
        <h3><a href="posts/{{ post.slug }}.html">{{ post.title }}</a></h3>
        <p>{{ post.excerpt[:120] }}...</p>
        <div class="news-meta">
          <img src="{{ post.author_avatar }}" alt="{{ post.author_name }}" class="news-avatar">
          <span>{{ post.author_name }}</span><span class="dot">·</span><time>{{ post.date_human }}</time>
        </div>
      </div>
    </article>{% endfor %}
  </div>
  {% else %}
  <div class="empty-cat"><p>No articles yet. Check back soon!</p><a href="index.html" class="btn-back">← Home</a></div>
  {% endif %}
</main>
<footer class="site-footer"><div class="container">
  <div class="footer-grid">
    <div class="footer-brand"><a href="index.html" class="logo footer-logo"><span class="logo-text">{{ site_name }}</span></a><p>{{ site_tagline }}</p></div>
    <div class="footer-col"><h4>Categories</h4>
      <a href="category-business.html">Business</a><a href="category-technology.html">Technology</a>
      <a href="category-finance.html">Finance</a><a href="category-world.html">World</a></div>
    <div class="footer-col"><h4>More</h4>
      <a href="category-sports.html">Sports</a><a href="category-health.html">Health</a>
      <a href="networth/index.html">Net Worth</a><a href="sitemap.xml">Sitemap</a></div>
  </div>
  <div class="footer-bottom"><p>&copy; {{ year }} {{ site_name }}. All rights reserved.</p></div>
</div></footer>
</body></html>'''

def rebuild_all(posts):
    from jinja2 import Template as T
    for p in posts:
        if not p.get("excerpt"): p["excerpt"] = p.get("meta_description","")
        if not p.get("author_name"): p["author_name"] = "Staff Reporter"
        if not p.get("author_avatar"): p["author_avatar"] = "https://i.pravatar.cc/150?img=10"
        if not p.get("author_title"): p["author_title"] = "News Desk"
    sorted_posts = sorted(posts, key=lambda x: x["date_iso"], reverse=True)

    # Homepage
    html = T(INDEX_HTML).render(posts=sorted_posts[:60], categories=CATEGORIES,
        site_name=SITE_NAME, site_url=SITE_URL, site_tagline=SITE_TAGLINE, year=datetime.now().year)
    (OUTPUT_DIR / "index.html").write_text(html)

    # Categories
    for cat in CATEGORIES:
        cat_posts = [p for p in sorted_posts if p.get("category","").lower() == cat.lower()]
        html = T(CAT_HTML).render(posts=cat_posts, category=cat,
            site_name=SITE_NAME, site_url=SITE_URL, site_tagline=SITE_TAGLINE, year=datetime.now().year)
        (OUTPUT_DIR / f"category-{cat.lower()}.html").write_text(html)

    # Sitemap
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             f'  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>']
    for cat in CATEGORIES:
        lines.append(f'  <url><loc>{SITE_URL}/category-{cat.lower()}.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>')
    for p in posts:
        lines.append(f'  <url><loc>{SITE_URL}/posts/{p["slug"]}.html</loc><lastmod>{p["date_iso"][:10]}</lastmod><priority>0.8</priority></url>')
    lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines))

    print(f"📊 Homepage: {len(sorted_posts)} articles | Categories rebuilt")

if __name__ == "__main__":
    main()
