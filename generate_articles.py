import os, json, time, random, requests, re
from datetime import datetime, timezone
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────
CLAUDE_API_KEY   = os.environ.get("CLAUDE_API_KEY", "")
NEWS_API_KEY     = os.environ.get("NEWS_API_KEY", "")
UNSPLASH_KEY     = os.environ.get("UNSPLASH_KEY", "")
SITE_URL         = os.environ.get("SITE_URL", "https://marketsnewstoday.info")
SITE_NAME        = "Markets News Today"
OUTPUT_DIR       = Path("output")
POSTS_DIR        = OUTPUT_DIR / "posts"
AUTHORS_DIR      = OUTPUT_DIR / "authors"
ARTICLES_PER_RUN = int(os.environ.get("ARTICLES_PER_RUN", "10"))

CATEGORIES = ["Business","Technology","Finance","World","Sports","Health","Travel","Science","Entertainment","Politics"]

AUTHORS = {
    "Business":      [{"id":"james-mitchell","name":"James Mitchell","title":"Business Editor","bio":"15 years covering global markets and corporate strategy.","avatar":"https://i.pravatar.cc/150?img=11","twitter":"@jmitchell_biz"},
                      {"id":"sarah-chen","name":"Sarah Chen","title":"Finance Reporter","bio":"Former Wall Street analyst turned journalist.","avatar":"https://i.pravatar.cc/150?img=47","twitter":"@sarahchen_fin"},
                      {"id":"robert-hayes","name":"Robert Hayes","title":"Economics Correspondent","bio":"Oxford economics graduate, expert in market trends.","avatar":"https://i.pravatar.cc/150?img=15","twitter":"@roberthayes_econ"}],
    "Technology":    [{"id":"alex-rivera","name":"Alex Rivera","title":"Tech Editor","bio":"Silicon Valley insider with 10+ years in tech journalism.","avatar":"https://i.pravatar.cc/150?img=12","twitter":"@alexrivera_tech"},
                      {"id":"maya-patel","name":"Maya Patel","title":"AI Reporter","bio":"MIT graduate specializing in emerging technologies.","avatar":"https://i.pravatar.cc/150?img=48","twitter":"@mayapatel_ai"},
                      {"id":"tom-bradley","name":"Tom Bradley","title":"Cybersecurity Analyst","bio":"Former NSA contractor turned journalist.","avatar":"https://i.pravatar.cc/150?img=16","twitter":"@tombradley_sec"}],
    "Finance":       [{"id":"david-park","name":"David Park","title":"Markets Editor","bio":"CFA charterholder with global finance expertise.","avatar":"https://i.pravatar.cc/150?img=13","twitter":"@davidpark_mkt"},
                      {"id":"lisa-wong","name":"Lisa Wong","title":"Investment Reporter","bio":"Covers hedge funds and capital markets.","avatar":"https://i.pravatar.cc/150?img=49","twitter":"@lisawong_inv"},
                      {"id":"mark-thompson","name":"Mark Thompson","title":"Crypto Correspondent","bio":"Blockchain technology expert since 2013.","avatar":"https://i.pravatar.cc/150?img=17","twitter":"@markthompson_crypto"}],
    "World":         [{"id":"elena-vasquez","name":"Elena Vasquez","title":"World Affairs Editor","bio":"Award-winning foreign correspondent, 50+ countries.","avatar":"https://i.pravatar.cc/150?img=21","twitter":"@elenavasquez_world"},
                      {"id":"hassan-ahmed","name":"Hassan Ahmed","title":"Middle East Bureau Chief","bio":"20 years reporting from conflict zones worldwide.","avatar":"https://i.pravatar.cc/150?img=52","twitter":"@hassan_ahmed_me"},
                      {"id":"anna-kowalski","name":"Anna Kowalski","title":"Europe Correspondent","bio":"Brussels-based EU politics and diplomacy expert.","avatar":"https://i.pravatar.cc/150?img=25","twitter":"@annakowalski_eu"}],
    "Sports":        [{"id":"chris-johnson","name":"Chris Johnson","title":"Sports Editor","bio":"Former professional athlete turned journalist.","avatar":"https://i.pravatar.cc/150?img=14","twitter":"@chrisjohnson_sports"},
                      {"id":"maria-santos","name":"Maria Santos","title":"Football Correspondent","bio":"Premier League and Champions League expert.","avatar":"https://i.pravatar.cc/150?img=44","twitter":"@mariasantos_fc"},
                      {"id":"kevin-williams","name":"Kevin Williams","title":"US Sports Reporter","bio":"NBA, NFL and MLB insider access.","avatar":"https://i.pravatar.cc/150?img=18","twitter":"@kevinwilliams_us"}],
    "Health":        [{"id":"jennifer-ross","name":"Dr. Jennifer Ross","title":"Health Editor","bio":"MD with specialization in public health.","avatar":"https://i.pravatar.cc/150?img=23","twitter":"@drjenniferross"},
                      {"id":"michael-green","name":"Michael Green","title":"Medical Correspondent","bio":"Science writer covering medical research.","avatar":"https://i.pravatar.cc/150?img=53","twitter":"@michaelgreen_med"},
                      {"id":"rachel-kim","name":"Rachel Kim","title":"Wellness Reporter","bio":"Mental health and nutrition science expert.","avatar":"https://i.pravatar.cc/150?img=26","twitter":"@rachelkim_health"}],
    "Travel":        [{"id":"sophie-laurent","name":"Sophie Laurent","title":"Travel Editor","bio":"Visited 90+ countries, luxury travel expert.","avatar":"https://i.pravatar.cc/150?img=24","twitter":"@sophielaurent_travel"},
                      {"id":"diego-morales","name":"Diego Morales","title":"Adventure Travel Writer","bio":"Six continents, remote culture documentation.","avatar":"https://i.pravatar.cc/150?img=54","twitter":"@diegomorales_adv"},
                      {"id":"emma-wilson","name":"Emma Wilson","title":"Food and Travel Reporter","bio":"Culinary travel expert, 60+ countries reviewed.","avatar":"https://i.pravatar.cc/150?img=27","twitter":"@emmawilson_food"}],
    "Science":       [{"id":"neil-foster","name":"Dr. Neil Foster","title":"Science Editor","bio":"PhD Astrophysics Caltech, former NASA JPL.","avatar":"https://i.pravatar.cc/150?img=33","twitter":"@drneifoster_sci"},
                      {"id":"laura-martinez","name":"Laura Martinez","title":"Climate Reporter","bio":"Environmental science journalist.","avatar":"https://i.pravatar.cc/150?img=55","twitter":"@lauramartinez_clim"},
                      {"id":"james-liu","name":"James Liu","title":"Space Correspondent","bio":"NASA press corps, 20+ rocket launches.","avatar":"https://i.pravatar.cc/150?img=34","twitter":"@jamesliu_space"}],
    "Entertainment": [{"id":"jessica-taylor","name":"Jessica Taylor","title":"Entertainment Editor","bio":"Hollywood insider with major studio access.","avatar":"https://i.pravatar.cc/150?img=35","twitter":"@jessicataylor_ent"},
                      {"id":"brandon-lee","name":"Brandon Lee","title":"Music Reporter","bio":"Grammy-nominated producer turned journalist.","avatar":"https://i.pravatar.cc/150?img=56","twitter":"@brandonlee_music"},
                      {"id":"olivia-brown","name":"Olivia Brown","title":"Film Critic","bio":"BAFTA voter, Cannes Film Festival regular.","avatar":"https://i.pravatar.cc/150?img=36","twitter":"@oliviabrown_film"}],
    "Politics":      [{"id":"andrew-collins","name":"Andrew Collins","title":"Political Editor","bio":"20 years covering Washington DC politics.","avatar":"https://i.pravatar.cc/150?img=37","twitter":"@andrewcollins_pol"},
                      {"id":"patricia-morgan","name":"Patricia Morgan","title":"Policy Correspondent","bio":"Former White House press pool journalist.","avatar":"https://i.pravatar.cc/150?img=57","twitter":"@patriciamorgan_dc"},
                      {"id":"samuel-davis","name":"Samuel Davis","title":"International Affairs","bio":"US foreign policy and geopolitics expert.","avatar":"https://i.pravatar.cc/150?img=38","twitter":"@samueldavis_intl"}],
}

WIKI_TOPICS = [
    "Stock market outlook 2026","AI revolution in business 2026","Bitcoin price analysis 2026",
    "Tesla quarterly earnings report","Federal Reserve rate decision","Climate change business impact",
    "Electric vehicle market growth","US housing market trends","Global trade policy update",
    "Tech startup funding landscape","Cybersecurity threats enterprise","Mental health workplace 2026",
    "Renewable energy investment boom","China economy latest data","India GDP growth 2026",
    "SpaceX mission update","Apple product launch 2026","Amazon business strategy",
    "Healthcare innovation breakthroughs","Supply chain global update",
]

# ── HELPERS ─────────────────────────────────────────────────────────
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:70]

def esc(s):
    return str(s).replace('"', "'").replace('<', '&lt;').replace('>', '&gt;')

def get_image(keyword, slug):
    if UNSPLASH_KEY:
        try:
            r = requests.get("https://api.unsplash.com/photos/random",
                params={"query": keyword, "orientation": "landscape"},
                headers={"Authorization": "Client-ID " + UNSPLASH_KEY}, timeout=8)
            if r.status_code == 200:
                return r.json()["urls"]["regular"]
        except Exception:
            pass
    seed = abs(hash(slug)) % 1000
    return f"https://picsum.photos/seed/{seed}/1200/630"

def get_author(category):
    return random.choice(AUTHORS.get(category, AUTHORS["World"]))

def load_published():
    p = OUTPUT_DIR / "published.json"
    return set(json.loads(p.read_text())) if p.exists() else set()

def save_published(s):
    (OUTPUT_DIR / "published.json").write_text(json.dumps(list(s), indent=2))

def load_index():
    p = OUTPUT_DIR / "posts_index.json"
    return json.loads(p.read_text()) if p.exists() else []

def save_index(posts):
    (OUTPUT_DIR / "posts_index.json").write_text(json.dumps(posts, indent=2))

# ── BUILD ROBOTS.TXT ────────────────────────────────────────────────
def build_robots():
    """Generate robots.txt with correct SITE_URL — never use placeholder."""
    content = f"""User-agent: *
Allow: /
Disallow: /cgi-bin/

Sitemap: {SITE_URL}/sitemap.xml
"""
    (OUTPUT_DIR / "robots.txt").write_text(content)

# ── BUILD RSS FEED ───────────────────────────────────────────────────
def build_rss(posts):
    """Generate RSS 2.0 feed for Google News and aggregators."""
    sp = sorted(posts, key=lambda x: x["date_iso"], reverse=True)[:50]
    now_rfc = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = ""
    for p in sp:
        try:
            pub = datetime.fromisoformat(p["date_iso"]).strftime("%a, %d %b %Y %H:%M:%S +0000")
        except Exception:
            pub = now_rfc
        items += f"""  <item>
    <title>{esc(p["title"])}</title>
    <link>{SITE_URL}/posts/{p["slug"]}.html</link>
    <description>{esc(p.get("excerpt", p.get("meta_description", "")))}</description>
    <pubDate>{pub}</pubDate>
    <guid isPermaLink="true">{SITE_URL}/posts/{p["slug"]}.html</guid>
    <category>{esc(p.get("category","World"))}</category>
  </item>
"""
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{SITE_NAME}</title>
  <link>{SITE_URL}/</link>
  <description>Breaking news and expert analysis on business, finance, technology and world affairs.</description>
  <language>en-us</language>
  <lastBuildDate>{now_rfc}</lastBuildDate>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
{items}</channel>
</rss>"""
    (OUTPUT_DIR / "feed.xml").write_text(rss)

# ── TOPICS ──────────────────────────────────────────────────────────
def fetch_news(count):
    if not NEWS_API_KEY:
        return []
    try:
        r = requests.get("https://newsapi.org/v2/top-headlines",
            params={"language": "en", "pageSize": min(count*3, 100), "apiKey": NEWS_API_KEY}, timeout=10)
        topics, seen = [], set()
        for a in r.json().get("articles", []):
            t = a.get("title", "")
            d = a.get("description", "") or ""
            if t and "[Removed]" not in t:
                k = slugify(t)[:40]
                if k not in seen:
                    seen.add(k)
                    topics.append({"title": t, "hint": d[:300]})
        return topics
    except Exception as e:
        print(f"NewsAPI: {e}")
        return []

def is_duplicate(title_slug, published):
    """Check if a topic is already published using keyword overlap scoring.
    Catches near-duplicates like 'father-kills-8-children' vs 'louisiana-father-kills-8-children'.
    """
    # Exact match
    if title_slug in published:
        return True
    # Stopwords to ignore when comparing
    STOP = {"a","an","the","in","on","at","of","and","for","to","is","are","was","were",
            "it","its","as","by","with","from","that","this","has","have","after","over",
            "into","about","up","out","than","but","be","been","their","his","her","our"}
    words = set(title_slug.split("-")) - STOP
    if not words:
        return False
    for p in published:
        p_words = set(p.split("-")) - STOP
        if not p_words:
            continue
        overlap = len(words & p_words) / max(len(words), len(p_words))
        if overlap >= 0.6:   # 60%+ same keywords = duplicate story
            return True
    return False

def build_topics(count, published):
    news = fetch_news(count * 2)
    fresh = [t for t in news if not is_duplicate(slugify(t["title"]), published)]
    pool = WIKI_TOPICS.copy()
    random.shuffle(pool)
    while len(fresh) < count and pool:
        t = pool.pop()
        if not is_duplicate(slugify(t), published):
            fresh.append({"title": t, "hint": ""})
    return fresh[:count]

# ── WRITE ARTICLE ────────────────────────────────────────────────────
def write_article(topic, hint):
    now = datetime.now()
    prompt = (
        f"Write a professional news article dated {now.strftime('%B %d, %Y')} about: {topic}\n"
        f"Background: {hint}\n\n"
        "Respond with ONLY this XML format — no extra text:\n"
        "<article>\n"
        "<title>Compelling headline 55-70 chars</title>\n"
        "<slug>url-slug-from-title</slug>\n"
        "<meta_description>SEO description 150-158 chars</meta_description>\n"
        "<focus_keyword>primary keyword phrase</focus_keyword>\n"
        "<category>Business or Technology or Finance or World or Sports or Health or Travel or Science or Entertainment or Politics</category>\n"
        "<image_keyword>specific 3-4 word Unsplash search term</image_keyword>\n"
        "<read_time>X min read</read_time>\n"
        "<excerpt>2-3 compelling sentences</excerpt>\n"
        "<tags>tag1,tag2,tag3,tag4</tags>\n"
        "<content>\n"
        "Write minimum 900 words. Use h2, h3, p, ul, li, strong, blockquote tags only. "
        "No hr tags. No dashes (-- or —). Do NOT mention any news outlet by name. "
        "Write complete professional article with proper paragraphs.\n"
        "</content>\n"
        "</article>"
    )
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 3000,
                  "messages": [{"role": "user", "content": prompt}]}, timeout=90)
        resp = r.json()
        if "content" not in resp:
            print(f"  Claude error: {resp}")
            return None
        raw = resp["content"][0]["text"].strip()
        def x(tag):
            m = re.search(f"<{tag}>(.*?)</{tag}>", raw, re.DOTALL)
            return m.group(1).strip() if m else ""
        title = x("title")
        if not title:
            print("  Parse failed")
            return None
        cat = x("category").strip()
        if cat not in CATEGORIES:
            cat = "World"
        return {
            "title": title, "slug": slugify(title),
            "meta_description": x("meta_description"),
            "focus_keyword": x("focus_keyword"),
            "category": cat,
            "image_keyword": x("image_keyword"),
            "read_time": x("read_time") or "5 min read",
            "excerpt": x("excerpt"),
            "tags": [t.strip() for t in x("tags").split(",") if t.strip()],
            "article_html": x("content"),
        }
    except Exception as e:
        print(f"  Article error: {e}")
        return None

# ── HTML HELPERS ─────────────────────────────────────────────────────
def nav_html(prefix=""):
    d = datetime.now().strftime("%A, %B %d, %Y")
    return f"""<div class="topbar"><div class="topbar-inner">
  <span class="topbar-left">{d}</span>
  <a href="{prefix}" class="topbar-logo">Markets <span class="accent">News</span> Today</a>
  <span class="topbar-right">Business &middot; Finance &middot; Technology</span>
</div></div>
<nav class="navbar"><div class="navbar-inner">
  <a href="{prefix}">Home</a>
  <a href="{prefix}category-business.html">Business</a>
  <a href="{prefix}category-technology.html">Technology</a>
  <a href="{prefix}category-finance.html">Finance</a>
  <a href="{prefix}category-world.html">World</a>
  <a href="{prefix}category-sports.html">Sports</a>
  <a href="{prefix}category-health.html">Health</a>
  <a href="{prefix}category-politics.html">Politics</a>
  <a href="{prefix}networth/index.html">Net Worth</a>
</div></nav>"""

def foot_html(prefix=""):
    y = datetime.now().year
    return f"""<footer class="footer"><div class="footer-top"><div class="container"><div class="footer-grid">
  <div class="footer-brand">
    <div class="footer-logo">Markets <span class="accent">News</span> Today</div>
    <p>Your trusted source for breaking news and in-depth analysis on business, finance and world affairs.</p>
  </div>
  <div class="footer-col"><h4>Business</h4>
    <a href="{prefix}category-business.html">Business</a>
    <a href="{prefix}category-finance.html">Finance</a>
    <a href="{prefix}category-technology.html">Technology</a>
    <a href="{prefix}networth/index.html">Net Worth</a></div>
  <div class="footer-col"><h4>World</h4>
    <a href="{prefix}category-world.html">World</a>
    <a href="{prefix}category-politics.html">Politics</a>
    <a href="{prefix}category-sports.html">Sports</a>
    <a href="{prefix}category-entertainment.html">Entertainment</a></div>
  <div class="footer-col"><h4>More</h4>
    <a href="{prefix}category-health.html">Health</a>
    <a href="{prefix}category-science.html">Science</a>
    <a href="{prefix}category-travel.html">Travel</a>
    <a href="{prefix}sitemap.xml">Sitemap</a></div>
</div></div></div>
<div class="footer-btm"><div class="container">&copy; {y} Markets News Today. All rights reserved.</div></div>
</footer>"""

def head_html(title, desc, canonical, image="", prefix="", og_type="article"):
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="{prefix}favicon.ico" type="image/x-icon">
<link rel="apple-touch-icon" href="{prefix}favicon.png">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{image}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{image}">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{SITE_URL}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{prefix}style.css">
</head><body>"""

def byline_html(p, prefix=""):
    return f"""<div class="byline">
  <img src="{p.get('author_avatar','')}" alt="{esc(p.get('author_name',''))}">
  <strong><a href="{prefix}authors/{p.get('author_id','staff')}.html" style="color:inherit">{esc(p.get('author_name',''))}</a></strong>
  <span class="sep">&middot;</span>
  <time>{p.get('date_human','')}</time>
  <span class="sep">&middot;</span>
  <span>{p.get('read_time','5 min read')}</span>
</div>"""

# ── BUILD POST ───────────────────────────────────────────────────────
def build_post(data, author, all_posts, now):
    slug = data["slug"]
    cat = data["category"]
    
    # Related: same category first
    same = [p for p in all_posts if p["slug"] != slug and p.get("category") == cat][:3]
    if len(same) < 3:
        other = [p for p in all_posts if p["slug"] != slug and p.get("category") != cat]
        same += other[:3 - len(same)]
    
    related_items = "".join(
        f'<li><a href="{SITE_URL}/posts/{p["slug"]}.html">{esc(p["title"])}</a></li>'
        for p in same[:3]
    )
    related_html = f'<div class="post-related"><h3>Related Articles</h3><ul>{related_items}</ul></div>' if related_items else ""
    
    tags_html = "".join(f'<a href="{SITE_URL}/index.html" class="tag">{esc(t)}</a>' for t in data.get("tags", []))
    
    # Sidebar trending
    sidebar_items = "".join(
        f'''<a href="{SITE_URL}/posts/{p["slug"]}.html" class="sw-item">
          <div class="sw-item-img"><img src="{p["image_url"]}" alt="{esc(p["title"][:40])}" loading="lazy"></div>
          <div><h4>{esc(p["title"][:52])}{"..." if len(p["title"])>52 else ""}</h4>
          <div class="sw-item-date">{p.get("date_human","")}</div></div></a>'''
        for p in [x for x in all_posts if x["slug"] != slug][:6]
    )
    
    schema = json.dumps({
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": data["title"], "image": data["image_url"],
        "datePublished": now.isoformat(),
        "dateModified": now.isoformat(),
        "articleSection": cat,
        "wordCount": len(re.sub(r'<[^>]+>', '', data.get("article_html","")).split()),
        "keywords": ", ".join(data.get("tags", [])),
        "author": {"@type": "Person", "name": author["name"], "url": f"{SITE_URL}/authors/{author['id']}.html"},
        "publisher": {"@type": "NewsMediaOrganization", "name": SITE_NAME, "url": SITE_URL}
    })

    breadcrumb = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": cat, "item": f"{SITE_URL}/category-{cat.lower()}.html"},
            {"@type": "ListItem", "position": 3, "name": data["title"]}
        ]
    })
    
    return f"""{head_html(data["title"] + " | " + SITE_NAME, data["meta_description"],
        SITE_URL + "/posts/" + slug + ".html", data["image_url"], "../")}
<script type="application/ld+json">{schema}</script>
<script type="application/ld+json">{breadcrumb}</script>
{nav_html("../")}
<div class="post-wrap"><div class="container post-grid">
<article>
  <div class="post-hdr">
    <a href="../category-{cat.lower()}.html" class="label">{cat}</a>
    <h1>{esc(data["title"])}</h1>
    <div class="desc">{esc(data.get("excerpt", data["meta_description"]))}</div>
    <div class="post-meta-bar">
      <img src="{author["avatar"]}" alt="{esc(author["name"])}">
      <div><div class="name"><a href="../authors/{author["id"]}.html" style="color:inherit">{esc(author["name"])}</a></div>
      <div class="role">{esc(author["title"])}</div></div>
      <span class="sep">&middot;</span>
      <time>{now.strftime("%B %d, %Y")}</time>
      <span class="sep">&middot;</span>
      <span class="read">{data.get("read_time","5 min read")}</span>
    </div>
  </div>
  <div class="post-hero"><img src="{data["image_url"]}" alt="{esc(data["title"])}" loading="eager"></div>
  <div class="post-body">{data["article_html"]}</div>
  {related_html}
  <div class="post-tags">{tags_html}</div>
  <div class="author-box">
    <img src="{author["avatar"]}" alt="{esc(author["name"])}">
    <div>
      <div class="author-box-name">{esc(author["name"])}</div>
      <div class="author-box-role">{esc(author["title"])}</div>
      <div class="author-box-bio">{esc(author["bio"])}</div>
    </div>
  </div>
</article>
<aside class="sidebar">
  <div class="sw"><div class="sw-title">Trending Now</div>{sidebar_items}</div>
</aside>
</div></div>
{foot_html("../")}
</body></html>"""

# ── BUILD HOMEPAGE ────────────────────────────────────────────────────
def build_homepage(posts):
    sp = sorted(posts, key=lambda x: x["date_iso"], reverse=True)
    for p in sp:
        if not p.get("excerpt"): p["excerpt"] = p.get("meta_description", "")
        if not p.get("author_name"): p["author_name"] = "Staff Reporter"
        if not p.get("author_avatar"): p["author_avatar"] = "https://i.pravatar.cc/150?img=10"
        if not p.get("author_id"): p["author_id"] = "staff"

    # Hero
    hero_html = ""
    if sp:
        h = sp[0]
        sides = ""
        for p in sp[1:5]:
            sides += f"""<a href="posts/{p["slug"]}.html" class="hero-side-item">
              <div class="label">{p["category"]}</div>
              <h3>{esc(p["title"])}</h3>
              <div class="hero-side-meta">{esc(p.get("author_name",""))} &middot; {p.get("date_human","")}</div>
            </a>"""
        hero_html = f"""<section class="hero"><div class="container">
<div class="hero-grid">
  <a href="posts/{h["slug"]}.html" class="hero-main">
    <div class="hero-main-img"><img src="{h["image_url"]}" alt="{esc(h["title"])}" loading="eager"></div>
    <div class="hero-main-body">
      <div class="label">{h["category"]}</div>
      <h1>{esc(h["title"])}</h1>
      <p>{esc(h.get("excerpt","")[:180])}</p>
      {byline_html(h)}
    </div>
  </a>
  <div class="hero-side">{sides}</div>
</div>
</div></section>"""

    # Category sections
    cat_html = ""
    for cat in CATEGORIES:
        cp = [p for p in sp if p.get("category","").lower() == cat.lower()]
        if not cp: continue
        lead = cp[0]
        smalls = ""
        for p in cp[1:3]:
            smalls += f"""<a href="posts/{p["slug"]}.html" class="cat-small">
              <div class="cat-small-img"><img src="{p["image_url"]}" alt="{esc(p["title"][:40])}" loading="lazy"></div>
              <div>
                <div class="label">{p["category"]}</div>
                <h3>{esc(p["title"])}</h3>
                <div class="cat-small-meta">{esc(p.get("author_name",""))} &middot; {p.get("date_human","")}</div>
              </div>
            </a>"""
        cat_html += f"""<div class="cat-block">
  <div class="section-title">
    <h2>{cat}</h2><div class="line"></div>
    <a href="category-{cat.lower()}.html">More {cat} &rarr;</a>
  </div>
  <div class="cat-grid">
    <a href="posts/{lead["slug"]}.html" class="cat-lead">
      <div class="cat-lead-img"><img src="{lead["image_url"]}" alt="{esc(lead["title"][:40])}" loading="lazy"></div>
      <div class="cat-lead-body">
        <div class="label">{lead["category"]}</div>
        <h2>{esc(lead["title"])}</h2>
        <p>{esc(lead.get("excerpt","")[:130])}...</p>
        {byline_html(lead)}
      </div>
    </a>
    <div class="cat-smalls">{smalls}</div>
  </div>
</div>"""

    # Sidebar
    sw_items = "".join(
        f"""<a href="posts/{p["slug"]}.html" class="sw-item">
          <div class="sw-item-img"><img src="{p["image_url"]}" alt="{esc(p["title"][:40])}" loading="lazy"></div>
          <div><h4>{esc(p["title"][:52])}{"..." if len(p["title"])>52 else ""}</h4>
          <div class="sw-item-date">{p.get("date_human","")}</div></div></a>"""
        for p in sp[:7]
    )
    sw_cats = "".join(
        f'<a href="category-{c.lower()}.html" class="sw-cat"><span>{c}</span><span>&rarr;</span></a>'
        for c in CATEGORIES
    )

    site_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": SITE_URL,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint", "urlTemplate": f"{SITE_URL}/search?q={{search_term_string}}"},
            "query-input": "required name=search_term_string"
        }
    })
    org_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "NewsMediaOrganization",
        "name": SITE_NAME,
        "url": SITE_URL,
        "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/favicon.png"}
    })

    html = f"""{head_html(SITE_NAME + " — Business, Finance & World News",
        "Breaking news and expert analysis on business, finance, technology and world affairs.",
        SITE_URL + "/", sp[0]["image_url"] if sp else "", "", "website")}
<script type="application/ld+json">{site_schema}</script>
<script type="application/ld+json">{org_schema}</script>
{nav_html()}
{hero_html}
<div class="container"><div class="main-wrap">
  <main>{cat_html}</main>
  <aside class="sidebar">
    <div class="sw"><div class="sw-title">Most Read</div>{sw_items}</div>
    <div class="sw"><div class="sw-title">Sections</div>{sw_cats}</div>
  </aside>
</div></div>
{foot_html()}
</body></html>"""
    (OUTPUT_DIR / "index.html").write_text(html)

# ── BUILD CATEGORIES ──────────────────────────────────────────────────
def build_categories(posts):
    sp = sorted(posts, key=lambda x: x["date_iso"], reverse=True)
    for cat in CATEGORIES:
        cp = [p for p in sp if p.get("category","").lower() == cat.lower()]
        cards = ""
        for p in cp:
            cards += f"""<a href="posts/{p["slug"]}.html" class="cat-page-card">
  <div class="cat-page-card-img"><img src="{p["image_url"]}" alt="{esc(p["title"][:40])}" loading="lazy"></div>
  <div class="cat-page-card-body">
    <div class="label">{p["category"]}</div>
    <h2>{esc(p["title"])}</h2>
    <p>{esc(p.get("excerpt","")[:110])}...</p>
    {byline_html(p)}
  </div>
</a>"""
        empty = '<div class="empty-state">No articles yet. Check back soon!</div>' if not cp else ""
        sw_cats = "".join(
            f'<a href="category-{c.lower()}.html" class="sw-cat{"" if c!=cat else ""}" style="{"color:var(--red)" if c==cat else ""}"><span>{c}</span><span>&rarr;</span></a>'
            for c in CATEGORIES
        )
        html = f"""{head_html(cat + " News | " + SITE_NAME,
            f"Latest {cat} news, analysis and expert commentary.",
            SITE_URL + "/category-" + cat.lower() + ".html", "", "")}
{nav_html()}
<div class="container">
  <div class="cat-page-hdr">
    <div class="label">Section</div>
    <h1>{cat}</h1>
    <p>Latest {cat} news, analysis and expert commentary</p>
  </div>
  <div class="main-wrap">
    <main>
      <div class="cat-page-grid">{cards}</div>
      {empty}
    </main>
    <aside class="sidebar">
      <div class="sw"><div class="sw-title">All Sections</div>{sw_cats}</div>
    </aside>
  </div>
</div>
{foot_html()}
</body></html>"""
        (OUTPUT_DIR / f"category-{cat.lower()}.html").write_text(html)

# ── BUILD AUTHORS ─────────────────────────────────────────────────────
def build_authors(posts):
    AUTHORS_DIR.mkdir(exist_ok=True)
    all_authors = {a["id"]: a for cat_list in AUTHORS.values() for a in cat_list}
    for aid, author in all_authors.items():
        ap = sorted([p for p in posts if p.get("author_id") == aid], key=lambda x: x["date_iso"], reverse=True)
        cards = "".join(
            f"""<a href="../posts/{p["slug"]}.html" class="cat-page-card">
  <div class="cat-page-card-img"><img src="{p["image_url"]}" alt="{esc(p["title"][:40])}" loading="lazy"></div>
  <div class="cat-page-card-body">
    <div class="label">{p["category"]}</div>
    <h2>{esc(p["title"])}</h2>
    <p>{esc(p.get("excerpt","")[:110])}...</p>
    <div class="byline"><time>{p.get("date_human","")}</time></div>
  </div>
</a>""" for p in ap
        )
        schema = json.dumps({"@context":"https://schema.org","@type":"Person","name":author["name"],
            "jobTitle":author["title"],"image":author["avatar"],
            "url":f"{SITE_URL}/authors/{aid}.html",
            "worksFor":{"@type":"Organization","name":SITE_NAME}})
        html = f"""{head_html(author["name"] + " — " + author["title"] + " | " + SITE_NAME,
            author["bio"], SITE_URL + "/authors/" + aid + ".html", author["avatar"], "../")}
<script type="application/ld+json">{schema}</script>
{nav_html("../")}
<div class="container author-profile">
  <div class="author-profile-hdr">
    <img src="{author["avatar"]}" alt="{esc(author["name"])}">
    <div>
      <div class="author-profile-name">{esc(author["name"])}</div>
      <div class="author-profile-role">{esc(author["title"])}</div>
      <div class="author-profile-bio">{esc(author["bio"])}</div>
      <div style="margin-top:8px;font-size:12px;color:#999">{author["twitter"]}</div>
    </div>
  </div>
  <div class="section-title"><h2>Articles by {esc(author["name"])}</h2><div class="line"></div></div>
  <div class="cat-page-grid">{cards if cards else '<p style="color:#999;padding:40px 0">No articles published yet.</p>'}</div>
</div>
{foot_html("../")}
</body></html>"""
        (AUTHORS_DIR / f"{aid}.html").write_text(html)

# ── BUILD SITEMAP ─────────────────────────────────────────────────────
def build_sitemap(posts):
    seen_slugs = set()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             f'  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>']
    for cat in CATEGORIES:
        lines.append(f'  <url><loc>{SITE_URL}/category-{cat.lower()}.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>')
    # Networth section
    lines.append(f'  <url><loc>{SITE_URL}/networth/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    nw_index = OUTPUT_DIR / "networth_index.json"
    if nw_index.exists():
        try:
            for profile in json.loads(nw_index.read_text()):
                nw_slug = profile.get("slug", "")
                if nw_slug and nw_slug not in seen_slugs:
                    seen_slugs.add(nw_slug)
                    lines.append(f'  <url><loc>{SITE_URL}/networth/{nw_slug}.html</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>')
        except Exception:
            pass
    seen_slugs.clear()
    # Posts — deduplicated
    for p in posts:
        if p["slug"] in seen_slugs:
            print(f"  Sitemap: skipping duplicate slug {p['slug']}")
            continue
        seen_slugs.add(p["slug"])
        lines.append(f'  <url><loc>{SITE_URL}/posts/{p["slug"]}.html</loc><lastmod>{p["date_iso"][:10]}</lastmod><priority>0.8</priority></url>')
    lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines))

# ── MAIN ──────────────────────────────────────────────────────────────
def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(exist_ok=True)
    AUTHORS_DIR.mkdir(exist_ok=True)

    published = load_published()
    posts_index = load_index()

    # Deduplicate posts_index — remove any duplicate slugs that crept in previously
    seen = set()
    deduped = []
    for p in posts_index:
        if p["slug"] not in seen:
            seen.add(p["slug"])
            deduped.append(p)
        else:
            print(f"  Removing duplicate from index: {p['slug']}")
    posts_index = deduped

    print(f"Getting {ARTICLES_PER_RUN} topics...")
    topics = build_topics(ARTICLES_PER_RUN, published)

    new_count = 0
    for i, t in enumerate(topics):
        title = t["title"]
        slug = slugify(title)
        if slug in published:
            continue
        print(f"  Writing [{i+1}/{len(topics)}] {title}")
        article = write_article(title, t.get("hint", ""))
        if not article:
            continue
        article["slug"] = slugify(article["title"])
        # Double check new slug not already published
        if is_duplicate(article["slug"], published):
            print(f"  Skipping duplicate: {article['slug']}")
            continue
        category = article.get("category", "World")
        author = get_author(category)
        img_kw = article.get("image_keyword") or " ".join(article["title"].split()[:4])
        image = get_image(img_kw, article["slug"])
        article["image_url"] = image
        now = datetime.now(timezone.utc)
        
        html = build_post(article, author, posts_index, now)
        (POSTS_DIR / f"{article['slug']}.html").write_text(html)
        
        posts_index.append({
            "slug": article["slug"], "title": article["title"],
            "meta_description": article["meta_description"],
            "excerpt": article.get("excerpt", article["meta_description"]),
            "category": category, "tags": article.get("tags", []),
            "image_url": image, "read_time": article.get("read_time", "5 min read"),
            "author_name": author["name"], "author_title": author["title"],
            "author_avatar": author["avatar"], "author_id": author["id"],
            "date_iso": now.isoformat(), "date_human": now.strftime("%B %d, %Y"),
        })
        published.add(article["slug"])
        new_count += 1
        time.sleep(2)

    print(f"Generated {new_count} new articles")

    # Rebuild ALL existing posts with new template
    print("Rebuilding all posts with latest template...")
    rebuilt = 0
    for p in posts_index:
        try:
            cat = p.get("category", "World")
            if cat not in CATEGORIES: cat = "World"
            auth_list = AUTHORS.get(cat, AUTHORS["World"])
            author = next((a for a in auth_list if a["id"] == p.get("author_id", "")), auth_list[0])
            post_file = POSTS_DIR / f"{p['slug']}.html"
            if post_file.exists():
                existing = post_file.read_text()
                m = re.search(r'<div class="post-body">(.*?)</div>\s*(?:<div class="post-related"|<div class="post-tags")', existing, re.DOTALL)
                if m:
                    body = m.group(1).strip()
                    data = {**p, "article_html": body}
                    try:
                        now2 = datetime.fromisoformat(p["date_iso"])
                    except:
                        now2 = datetime.now(timezone.utc)
                    post_file.write_text(build_post(data, author, posts_index, now2))
                    rebuilt += 1
        except Exception:
            pass
    print(f"Rebuilt {rebuilt} existing posts")

    build_homepage(posts_index)
    build_categories(posts_index)
    build_authors(posts_index)
    build_sitemap(posts_index)
    build_robots()
    build_rss(posts_index)
    save_published(published)
    save_index(posts_index)
    print("Done!")

if __name__ == "__main__":
    main()
