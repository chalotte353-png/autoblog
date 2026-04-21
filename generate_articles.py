"""
AutoBlog v3 — Forbes-Style Layout
- Unique topics every run (no repeats)
- Unsplash real images
- Author profile pages
- Internal linking in article text
- Forbes-style templates
"""

import os, json, time, random, requests, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Template

CLAUDE_API_KEY   = os.environ.get("CLAUDE_API_KEY", "")
NEWS_API_KEY     = os.environ.get("NEWS_API_KEY", "")
UNSPLASH_KEY     = os.environ.get("UNSPLASH_KEY", "")
SITE_URL         = os.environ.get("SITE_URL", "https://marketsnewstoday.info")
SITE_NAME        = os.environ.get("SITE_NAME", "Markets News Today")
SITE_TAGLINE     = os.environ.get("SITE_TAGLINE", "Business • Finance • Technology • World")
OUTPUT_DIR       = Path("output")
POSTS_DIR        = OUTPUT_DIR / "posts"
AUTHORS_DIR      = OUTPUT_DIR / "authors"
ARTICLES_PER_RUN = int(os.environ.get("ARTICLES_PER_RUN", "10"))

CATEGORIES = ["Business","Technology","Finance","World","Sports","Health","Travel","Science","Entertainment","Politics"]

AUTHORS = {
    "Business": [
        {"id":"james-mitchell","name":"James Mitchell","title":"Business Editor","bio":"James Mitchell has spent 15 years covering global markets, corporate strategy, and economic policy for leading financial publications. A former investment banker turned journalist, he brings insider knowledge to complex business stories.","avatar":"https://i.pravatar.cc/150?img=11","twitter":"@jmitchell_biz"},
        {"id":"sarah-chen","name":"Sarah Chen","title":"Senior Finance Reporter","bio":"Sarah Chen is a former Wall Street analyst who transitioned to journalism to make finance accessible to everyone. She specializes in equity markets, earnings analysis, and corporate governance.","avatar":"https://i.pravatar.cc/150?img=47","twitter":"@sarahchen_fin"},
        {"id":"robert-hayes","name":"Robert Hayes","title":"Economics Correspondent","bio":"Robert Hayes holds an economics degree from Oxford and has reported from major financial centers including New York, London, and Hong Kong. He covers macroeconomics, central banking, and trade policy.","avatar":"https://i.pravatar.cc/150?img=15","twitter":"@roberthayes_econ"},
    ],
    "Technology": [
        {"id":"alex-rivera","name":"Alex Rivera","title":"Tech Editor","bio":"Alex Rivera has been at the forefront of Silicon Valley coverage for over a decade, breaking stories on major tech companies, startups, and emerging technologies. Former engineer at two unicorn startups.","avatar":"https://i.pravatar.cc/150?img=12","twitter":"@alexrivera_tech"},
        {"id":"maya-patel","name":"Maya Patel","title":"AI & Innovation Reporter","bio":"Maya Patel holds a Master's from MIT in Computer Science and covers artificial intelligence, machine learning, and the societal impact of emerging technologies.","avatar":"https://i.pravatar.cc/150?img=48","twitter":"@mayapatel_ai"},
        {"id":"tom-bradley","name":"Tom Bradley","title":"Cybersecurity Analyst","bio":"Tom Bradley is a former NSA contractor turned cybersecurity journalist. He provides expert analysis on data breaches, state-sponsored hacking, and digital privacy policy.","avatar":"https://i.pravatar.cc/150?img=16","twitter":"@tombradley_sec"},
    ],
    "Finance": [
        {"id":"david-park","name":"David Park","title":"Markets Editor","bio":"David Park is a CFA charterholder with deep expertise in global financial markets. He has covered major market events including the 2008 financial crisis and the COVID-19 market crash.","avatar":"https://i.pravatar.cc/150?img=13","twitter":"@davidpark_mkt"},
        {"id":"lisa-wong","name":"Lisa Wong","title":"Investment Reporter","bio":"Lisa Wong covers hedge funds, private equity, and capital markets. Her investigative work on fund performance has earned multiple industry awards.","avatar":"https://i.pravatar.cc/150?img=49","twitter":"@lisawong_inv"},
        {"id":"mark-thompson","name":"Mark Thompson","title":"Crypto Correspondent","bio":"Mark Thompson was an early Bitcoin adopter and has covered the cryptocurrency space since 2013. He provides nuanced analysis of blockchain technology and digital asset markets.","avatar":"https://i.pravatar.cc/150?img=17","twitter":"@markthompson_crypto"},
    ],
    "World": [
        {"id":"elena-vasquez","name":"Elena Vasquez","title":"World Affairs Editor","bio":"Elena Vasquez is an award-winning foreign correspondent who has reported from over 50 countries. Based in Geneva, she covers international relations, conflict, and global diplomacy.","avatar":"https://i.pravatar.cc/150?img=21","twitter":"@elenavasquez_world"},
        {"id":"hassan-ahmed","name":"Hassan Ahmed","title":"Middle East Bureau Chief","bio":"Hassan Ahmed has spent 20 years reporting from the Middle East and Central Asia, covering conflicts, political transitions, and humanitarian crises for major international outlets.","avatar":"https://i.pravatar.cc/150?img=52","twitter":"@hassan_ahmed_me"},
        {"id":"anna-kowalski","name":"Anna Kowalski","title":"Europe Correspondent","bio":"Anna Kowalski is based in Brussels and covers European Union politics, economic policy, and the continent's evolving geopolitical landscape.","avatar":"https://i.pravatar.cc/150?img=25","twitter":"@annakowalski_eu"},
    ],
    "Sports": [
        {"id":"chris-johnson","name":"Chris Johnson","title":"Sports Editor","bio":"Chris Johnson is a former professional athlete turned award-winning sports journalist. He brings a unique insider perspective to coverage of major sporting events worldwide.","avatar":"https://i.pravatar.cc/150?img=14","twitter":"@chrisjohnson_sports"},
        {"id":"maria-santos","name":"Maria Santos","title":"Football Correspondent","bio":"Maria Santos covers football exclusively, with deep knowledge of the Premier League, Champions League, and international competitions. She has interviewed hundreds of top players and managers.","avatar":"https://i.pravatar.cc/150?img=44","twitter":"@mariasantos_fc"},
        {"id":"kevin-williams","name":"Kevin Williams","title":"US Sports Reporter","bio":"Kevin Williams covers the NBA, NFL, and MLB with insider access developed over 12 years. A former sports agent, he provides unique insight into athlete contracts and team strategy.","avatar":"https://i.pravatar.cc/150?img=18","twitter":"@kevinwilliams_us"},
    ],
    "Health": [
        {"id":"jennifer-ross","name":"Dr. Jennifer Ross","title":"Health Editor","bio":"Dr. Jennifer Ross holds an MD from Johns Hopkins and a Master's in Public Health. She translates complex medical research into accessible reporting on healthcare policy and medical breakthroughs.","avatar":"https://i.pravatar.cc/150?img=23","twitter":"@drjenniferross"},
        {"id":"michael-green","name":"Michael Green","title":"Medical Correspondent","bio":"Michael Green is a science writer specializing in clinical trials, pharmaceutical research, and breakthrough medical technologies. He has covered major health events including the COVID-19 pandemic.","avatar":"https://i.pravatar.cc/150?img=53","twitter":"@michaelgreen_med"},
        {"id":"rachel-kim","name":"Rachel Kim","title":"Wellness Reporter","bio":"Rachel Kim focuses on mental health, nutrition science, and preventive medicine. Her work bridges the gap between academic research and practical health guidance for readers.","avatar":"https://i.pravatar.cc/150?img=26","twitter":"@rachelkim_health"},
    ],
    "Travel": [
        {"id":"sophie-laurent","name":"Sophie Laurent","title":"Travel Editor","bio":"Sophie Laurent has visited over 90 countries and brings a sophisticated perspective to travel journalism. She specializes in luxury travel, sustainable tourism, and off-the-beaten-path destinations.","avatar":"https://i.pravatar.cc/150?img=24","twitter":"@sophielaurent_travel"},
        {"id":"diego-morales","name":"Diego Morales","title":"Adventure Travel Writer","bio":"Diego Morales has trekked across six continents documenting remote cultures and extreme destinations. His immersive travel writing has inspired thousands to explore the world.","avatar":"https://i.pravatar.cc/150?img=54","twitter":"@diegomorales_adv"},
        {"id":"emma-wilson","name":"Emma Wilson","title":"Food & Travel Reporter","bio":"Emma Wilson is a culinary travel expert and restaurant critic who combines gastronomy and destination reporting. She has reviewed restaurants in over 60 countries.","avatar":"https://i.pravatar.cc/150?img=27","twitter":"@emmawilson_food"},
    ],
    "Science": [
        {"id":"neil-foster","name":"Dr. Neil Foster","title":"Science Editor","bio":"Dr. Neil Foster holds a PhD in Astrophysics from Caltech and has worked at NASA's Jet Propulsion Laboratory. He makes cutting-edge science accessible to general audiences.","avatar":"https://i.pravatar.cc/150?img=33","twitter":"@drneifoster_sci"},
        {"id":"laura-martinez","name":"Laura Martinez","title":"Climate Reporter","bio":"Laura Martinez is an environmental science journalist specializing in climate change, renewable energy policy, and ecological conservation. She has reported from the Arctic to the Amazon.","avatar":"https://i.pravatar.cc/150?img=55","twitter":"@lauramartinez_clim"},
        {"id":"james-liu","name":"James Liu","title":"Space Correspondent","bio":"James Liu is a member of NASA's press corps and covers space exploration, astronomy, and the commercial space industry. He has witnessed over 20 rocket launches.","avatar":"https://i.pravatar.cc/150?img=34","twitter":"@jamesliu_space"},
    ],
    "Entertainment": [
        {"id":"jessica-taylor","name":"Jessica Taylor","title":"Entertainment Editor","bio":"Jessica Taylor is a Hollywood insider with exclusive access to major studios, networks, and talent agencies. Her celebrity interviews and industry analysis are widely read in the entertainment community.","avatar":"https://i.pravatar.cc/150?img=35","twitter":"@jessicataylor_ent"},
        {"id":"brandon-lee","name":"Brandon Lee","title":"Music & Culture Reporter","bio":"Brandon Lee is a Grammy-nominated music producer turned journalist who covers the music industry with unique insider knowledge. He specializes in emerging artists and industry trends.","avatar":"https://i.pravatar.cc/150?img=56","twitter":"@brandonlee_music"},
        {"id":"olivia-brown","name":"Olivia Brown","title":"Film Critic","bio":"Olivia Brown is a BAFTA voter and regular at the Cannes Film Festival who brings academic film theory to accessible criticism. She covers cinema from blockbusters to arthouse.","avatar":"https://i.pravatar.cc/150?img=36","twitter":"@oliviabrown_film"},
    ],
    "Politics": [
        {"id":"andrew-collins","name":"Andrew Collins","title":"Political Editor","bio":"Andrew Collins has spent 20 years covering Washington DC politics and global governance. A Pulitzer Prize finalist, he provides incisive analysis of political developments and policy impacts.","avatar":"https://i.pravatar.cc/150?img=37","twitter":"@andrewcollins_pol"},
        {"id":"patricia-morgan","name":"Patricia Morgan","title":"Policy Correspondent","bio":"Patricia Morgan is a former White House press pool journalist who now covers domestic and international policy. Her insider knowledge of the legislative process sets her work apart.","avatar":"https://i.pravatar.cc/150?img=57","twitter":"@patriciamorgan_dc"},
        {"id":"samuel-davis","name":"Samuel Davis","title":"International Affairs","bio":"Samuel Davis specializes in US foreign policy, international relations, and geopolitics. He has interviewed heads of state and senior officials across six continents.","avatar":"https://i.pravatar.cc/150?img=38","twitter":"@samueldavis_intl"},
    ],
}

# ── HELPERS ────────────────────────────────────────────────────────
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:70]

def get_image(keyword, slug):
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
    seed = abs(hash(slug)) % 1000
    return f"https://picsum.photos/seed/{seed}/1200/630"

def get_author(category):
    return random.choice(AUTHORS.get(category, AUTHORS["World"]))

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

# ── UNIQUE TOPIC FETCHER ──────────────────────────────────────────
def fetch_news_topics(count):
    if not NEWS_API_KEY:
        return []
    try:
        # Use 'everything' endpoint for more variety
        r = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"language":"en","pageSize":min(count*3,100),"apiKey":NEWS_API_KEY},
            timeout=10,
        )
        topics = []
        seen = set()
        for a in r.json().get("articles",[]):
            t = a.get("title","")
            d = a.get("description","") or ""
            if t and "[Removed]" not in t:
                key = slugify(t)[:40]
                if key not in seen:
                    seen.add(key)
                    topics.append({"title":t,"hint":d[:300]})
        return topics
    except Exception as e:
        print(f"NewsAPI: {e}")
        return []

def build_topics(count, published):
    """Get fresh topics not already published."""
    news = fetch_news_topics(count * 2)
    
    # Filter out already published
    fresh = []
    for t in news:
        if slugify(t["title"])[:40] not in {s[:40] for s in published}:
            fresh.append(t)
    
    # Add varied wiki topics if needed
    wiki_varied = [
        f"Global {random.choice(['economy','markets','trade'])} outlook {datetime.now().year}",
        f"{random.choice(['AI','Machine learning','Automation'])} impact on {random.choice(['jobs','healthcare','education'])}",
        f"{random.choice(['Bitcoin','Ethereum','Crypto'])} market analysis {datetime.now().strftime('%B %Y')}",
        f"{random.choice(['Tesla','Apple','Google','Microsoft','Amazon'])} latest {random.choice(['earnings','strategy','product'])}",
        f"Federal Reserve {random.choice(['interest rates','inflation','policy'])} update",
        f"{random.choice(['Climate change','Renewable energy','Solar power'])} breakthrough {datetime.now().year}",
        f"Stock market {random.choice(['rally','correction','outlook'])} {datetime.now().strftime('%B %Y')}",
        f"{random.choice(['SpaceX','NASA','Boeing'])} {random.choice(['mission','launch','announcement'])}",
        f"Global {random.choice(['trade war','sanctions','tariffs'])} impact analysis",
        f"{random.choice(['Real estate','Housing market','Property'])} trends {datetime.now().year}",
        f"{random.choice(['Cybersecurity','Data breach','Hacking'])} threat report {datetime.now().year}",
        f"{random.choice(['Mental health','Wellness','Healthcare'])} innovation {datetime.now().year}",
        f"{random.choice(['Electric vehicles','EV','Battery technology'])} market growth",
        f"US {random.choice(['economy','GDP','unemployment'])} latest data",
        f"{random.choice(['China','India','Europe','UK'])} economy {datetime.now().strftime('%B %Y')}",
    ]
    random.shuffle(wiki_varied)
    
    while len(fresh) < count and wiki_varied:
        t = wiki_varied.pop()
        if slugify(t)[:40] not in {s[:40] for s in published}:
            fresh.append({"title":t,"hint":""})
    
    return fresh[:count]

# ── CLAUDE WRITER ─────────────────────────────────────────────────
def write_article(topic, hint):
    now = datetime.now()
    
    

Return ONLY valid JSON (no markdown fences, no extra text):
{{
  "title": "Compelling Forbes-style headline 55-70 chars",
  "slug": "url-slug-from-title",
  "meta_description": "SEO meta description 150-158 chars",
  "focus_keyword": "primary keyword phrase",
  "category": "exactly one of: Business/Technology/Finance/World/Sports/Health/Travel/Science/Entertainment/Politics",
  "image_keyword": "3-4 word specific image search",
  "article_html": "<p>Full article minimum 900 words. Use h2 h3 p ul strong tags. Where relevant, include the internal links provided naturally in the text. Professional Forbes-style writing.</p>",
  "tags": ["tag1","tag2","tag3","tag4"],
  "read_time": "X min read",
  "excerpt": "2-3 compelling sentence summary"
}}"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key":CLAUDE_API_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-sonnet-4-6","max_tokens":3000,
                  "messages":[{"role":"user","content":prompt}]},
            timeout=60,
        )
        resp = r.json()
        if "content" not in resp:
            print(f"  Claude: {resp}")
            return None
        raw = resp["content"][0]["text"].strip()
        raw = re.sub(r"^```json\s*","",raw)
        raw = re.sub(r"\s*```$","",raw)
        data = json.loads(raw)
        data["slug"] = slugify(data["title"])
        return data
    except Exception as e:
        print(f"  ✗ Claude: {e}")
        return None

# ── TEMPLATES ─────────────────────────────────────────────────────
def get_nav(prefix=""):
    return f'''<header>
<div class="top-bar">
  <div class="top-bar-inner">
    <span class="top-bar-date">{datetime.now().strftime("%A, %B %d, %Y")}</span>
    <a href="{prefix}index.html" class="top-bar-logo">Markets<span>News</span>Today</a>
    <span class="top-bar-tagline">Business · Finance · Technology</span>
  </div>
</div>
<nav class="main-nav-bar">
  <div class="nav-inner">
    <a href="{prefix}index.html">Home</a>
    <a href="{prefix}category-business.html">Business</a>
    <a href="{prefix}category-technology.html">Technology</a>
    <a href="{prefix}category-finance.html">Finance</a>
    <a href="{prefix}category-world.html">World</a>
    <a href="{prefix}category-sports.html">Sports</a>
    <a href="{prefix}category-health.html">Health</a>
    <a href="{prefix}category-politics.html">Politics</a>
    <a href="{prefix}networth/index.html">Net Worth</a>
  </div>
</nav>
</header>'''

def get_footer(prefix=""):
    year = datetime.now().year
    return f'''<footer class="site-footer">
  <div class="footer-top">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <div class="footer-brand-name">Markets<span>News</span>Today</div>
          <p>Your trusted source for breaking news, in-depth analysis, and expert commentary on business, finance, technology and world affairs.</p>
        </div>
        <div class="footer-col">
          <h4>Business</h4>
          <a href="{prefix}category-business.html">Business News</a>
          <a href="{prefix}category-finance.html">Finance</a>
          <a href="{prefix}category-technology.html">Technology</a>
          <a href="{prefix}networth/index.html">Net Worth</a>
        </div>
        <div class="footer-col">
          <h4>World</h4>
          <a href="{prefix}category-world.html">World News</a>
          <a href="{prefix}category-politics.html">Politics</a>
          <a href="{prefix}category-sports.html">Sports</a>
          <a href="{prefix}category-entertainment.html">Entertainment</a>
        </div>
        <div class="footer-col">
          <h4>More</h4>
          <a href="{prefix}category-health.html">Health</a>
          <a href="{prefix}category-science.html">Science</a>
          <a href="{prefix}category-travel.html">Travel</a>
          <a href="{prefix}sitemap.xml">Sitemap</a>
        </div>
      </div>
    </div>
  </div>
  <div class="footer-bottom">
    <div class="container">
      <p>&copy; {year} Markets News Today. All rights reserved. Content is for informational purposes only.</p>
    </div>
  </div>
</footer>'''

POST_TPL = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} | {{ site_name }}</title>
<meta name="description" content="{{ meta_description }}">
<meta name="keywords" content="{{ focus_keyword }}, {{ tags|join(', ') }}">
<meta name="author" content="{{ author.name }}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{{ site_url }}/posts/{{ slug }}.html">
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ meta_description }}">
<meta property="og:image" content="{{ image_url }}">
<meta property="og:url" content="{{ site_url }}/posts/{{ slug }}.html">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Article","headline":"{{ title }}","description":"{{ meta_description }}","image":"{{ image_url }}","datePublished":"{{ date_iso }}","dateModified":"{{ date_iso }}","author":{"@type":"Person","name":"{{ author.name }}","url":"{{ site_url }}/authors/{{ author.id }}.html"},"publisher":{"@type":"Organization","name":"{{ site_name }}","url":"{{ site_url }}"},"mainEntityOfPage":{"@type":"WebPage","@id":"{{ site_url }}/posts/{{ slug }}.html"}}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="../style.css">
</head>
<body>
{{ nav }}
<div class="breaking-bar">
  <div class="breaking-inner">
    <span class="breaking-label">Latest</span>
    <span class="breaking-text">{{ title }}</span>
  </div>
</div>
<div class="post-wrap">
  <div class="container post-layout">
    <article class="post-main">
      <div class="post-header">
        <a href="../category-{{ category|lower }}.html" class="cat-badge">{{ category }}</a>
        <h1>{{ title }}</h1>
        <p class="post-desc">{{ excerpt }}</p>
        <div class="post-meta-bar">
          <img src="{{ author.avatar }}" alt="{{ author.name }}" class="author-avatar">
          <div>
            <a href="../authors/{{ author.id }}.html" class="author-link">{{ author.name }}</a>
            <div class="author-title-text">{{ author.title }}</div>
          </div>
          <span class="meta-sep">·</span>
          <time datetime="{{ date_iso }}">{{ date_human }}</time>
          <span class="meta-sep">·</span>
          <span>{{ read_time }}</span>
        </div>
      </div>
      <figure class="post-hero-img">
        <img src="{{ image_url }}" alt="{{ title }}" loading="eager" width="820" height="461">
        <figcaption class="post-hero-caption">Photo credit: Unsplash</figcaption>
      </figure>
      <div class="post-body">{{ article_html }}</div>
      <div class="post-tags-wrap">{% for tag in tags %}<a href="../index.html" class="tag">{{ tag }}</a>{% endfor %}</div>
      <div class="author-card">
        <img src="{{ author.avatar }}" alt="{{ author.name }}" class="author-card-img">
        <div>
          <div class="author-card-name">{{ author.name }}</div>
          <div class="author-card-role">{{ author.title }}</div>
          <p class="author-card-bio">{{ author.bio }}</p>
          <a href="../authors/{{ author.id }}.html" class="cat-badge" style="margin-top:10px;display:inline-block">View Profile →</a>
        </div>
      </div>
    </article>
    <aside>
      <div class="sidebar-widget">
        <div class="sidebar-widget-title">Trending Now</div>
        {{ sidebar_html }}
      </div>
    </aside>
  </div>
</div>
{{ footer }}
</body></html>'''

INDEX_TPL = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ site_name }} — {{ site_tagline }}</title>
<meta name="description" content="Breaking news and in-depth analysis on business, finance, technology and world affairs.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{{ site_url }}/">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"{{ site_name }}","url":"{{ site_url }}"}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="style.css">
</head>
<body>
{{ nav }}
{% if posts %}
<section class="top-stories">
  <div class="container">
    <div class="section-label"><span class="section-label-text">Top Stories</span><div class="section-label-line"></div><span class="section-label-sub">{{ today }}</span></div>
    <div class="top-stories-grid">
      <a href="posts/{{ posts[0].slug }}.html" class="hero-story">
        <div class="hero-story-img"><img src="{{ posts[0].image_url }}" alt="{{ posts[0].title }}" loading="eager"></div>
        <a href="category-{{ posts[0].category|lower }}.html" class="cat-badge">{{ posts[0].category }}</a>
        <h1>{{ posts[0].title }}</h1>
        <p>{{ posts[0].excerpt }}</p>
        <div class="hero-meta">
          <img src="{{ posts[0].author_avatar }}" alt="{{ posts[0].author_name }}" class="hero-avatar">
          <a href="authors/{{ posts[0].author_id }}.html" class="author-link">{{ posts[0].author_name }}</a>
          <span class="dot">·</span><span>{{ posts[0].date_human }}</span>
          <span class="dot">·</span><span>{{ posts[0].read_time }}</span>
        </div>
      </a>
      <div class="sidebar-stories">
        {% for post in posts[1:5] %}
        <a href="posts/{{ post.slug }}.html" class="sidebar-story">
          <div class="sidebar-story-img"><img src="{{ post.image_url }}" alt="{{ post.title }}" loading="lazy"></div>
          <div>
            <span class="cat-badge">{{ post.category }}</span>
            <h3>{{ post.title }}</h3>
            <div class="sidebar-story-meta">{{ post.author_name }} · {{ post.date_human }}</div>
          </div>
        </a>
        {% endfor %}
      </div>
    </div>
  </div>
</section>
{% endif %}
<div class="container main-layout">
  <main>
    <div class="section-label"><span class="section-label-text">Latest News</span><div class="section-label-line"></div></div>
    <div class="news-grid-3">
      {% for post in posts[5:] %}
      <article class="news-card">
        <a href="posts/{{ post.slug }}.html" class="news-card-img"><img src="{{ post.image_url }}" alt="{{ post.title }}" loading="lazy"></a>
        <a href="category-{{ post.category|lower }}.html" class="cat-badge">{{ post.category }}</a>
        <h3><a href="posts/{{ post.slug }}.html">{{ post.title }}</a></h3>
        <p>{{ post.excerpt[:110] }}...</p>
        <div class="news-card-meta">
          <img src="{{ post.author_avatar }}" alt="{{ post.author_name }}" class="news-card-avatar">
          <a href="authors/{{ post.author_id }}.html" class="author-link" style="font-size:.73rem">{{ post.author_name }}</a>
          <span class="dot">·</span><time>{{ post.date_human }}</time>
        </div>
      </article>
      {% endfor %}
    </div>
  </main>
  <aside>
    <div class="sidebar-widget">
      <div class="sidebar-widget-title">Most Read</div>
      {% for post in posts[:6] %}
      <a href="posts/{{ post.slug }}.html" class="sidebar-post">
        <div class="sidebar-post-img"><img src="{{ post.image_url }}" alt="{{ post.title }}" loading="lazy"></div>
        <div><h4>{{ post.title[:60] }}{% if post.title|length > 60 %}...{% endif %}</h4>
        <div class="sidebar-post-date">{{ post.date_human }}</div></div>
      </a>
      {% endfor %}
    </div>
    <div class="sidebar-widget">
      <div class="sidebar-widget-title">Categories</div>
      {% for cat in categories %}
      <a href="category-{{ cat|lower }}.html" class="sidebar-post" style="display:block;padding:8px 0;border-bottom:1px solid var(--border)">
        <span style="font-size:.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px">{{ cat }}</span>
      </a>
      {% endfor %}
    </div>
  </aside>
</div>
{{ footer }}
</body></html>'''

CAT_TPL = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ category }} News | {{ site_name }}</title>
<meta name="description" content="Latest {{ category }} news, analysis and expert commentary on {{ site_name }}.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{{ site_url }}/category-{{ category|lower }}.html">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="style.css">
</head>
<body>
{{ nav }}
<div class="container">
  <div class="cat-header">
    <div class="cat-header-label">Section</div>
    <h1>{{ category }}</h1>
    <p>Latest {{ category }} news, analysis and expert commentary</p>
  </div>
  {% if posts %}
  <div class="main-layout">
    <main>
      <div class="news-grid-3">
        {% for post in posts %}
        <article class="news-card">
          <a href="posts/{{ post.slug }}.html" class="news-card-img"><img src="{{ post.image_url }}" alt="{{ post.title }}" loading="lazy"></a>
          <a href="category-{{ post.category|lower }}.html" class="cat-badge">{{ post.category }}</a>
          <h3><a href="posts/{{ post.slug }}.html">{{ post.title }}</a></h3>
          <p>{{ post.excerpt[:110] }}...</p>
          <div class="news-card-meta">
            <img src="{{ post.author_avatar }}" alt="{{ post.author_name }}" class="news-card-avatar">
            <a href="authors/{{ post.author_id }}.html" class="author-link" style="font-size:.73rem">{{ post.author_name }}</a>
            <span class="dot">·</span><time>{{ post.date_human }}</time>
          </div>
        </article>
        {% endfor %}
      </div>
    </main>
    <aside>
      <div class="sidebar-widget">
        <div class="sidebar-widget-title">All Sections</div>
        {% for cat in categories %}
        <a href="category-{{ cat|lower }}.html" class="sidebar-post" style="display:block;padding:8px 0;border-bottom:1px solid var(--border)">
          <span style="font-size:.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px">{{ cat }}</span>
        </a>
        {% endfor %}
      </div>
    </aside>
  </div>
  {% else %}
  <div class="empty-cat"><p>No articles in {{ category }} yet. Check back soon!</p><a href="index.html" class="btn-back">← Back to Home</a></div>
  {% endif %}
</div>
{{ footer }}
</body></html>'''

AUTHOR_TPL = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ author.name }} — {{ author.title }} | {{ site_name }}</title>
<meta name="description" content="{{ author.bio[:155] }}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{{ site_url }}/authors/{{ author.id }}.html">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="../style.css">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Person","name":"{{ author.name }}","jobTitle":"{{ author.title }}","description":"{{ author.bio }}","image":"{{ author.avatar }}","url":"{{ site_url }}/authors/{{ author.id }}.html","worksFor":{"@type":"Organization","name":"{{ site_name }}"}}
</script>
</head>
<body>
{{ nav }}
<div class="container author-profile">
  <div class="author-profile-header">
    <img src="{{ author.avatar }}" alt="{{ author.name }}" class="author-profile-img">
    <div>
      <div class="author-profile-name">{{ author.name }}</div>
      <div class="author-profile-role">{{ author.title }}</div>
      <p class="author-profile-bio">{{ author.bio }}</p>
      <div style="margin-top:10px;font-size:.8rem;color:var(--text3)">{{ author.twitter }}</div>
    </div>
  </div>
  {% if posts %}
  <div class="section-label"><span class="section-label-text">Articles by {{ author.name }}</span><div class="section-label-line"></div></div>
  <div class="news-grid-3">
    {% for post in posts %}
    <article class="news-card">
      <a href="../posts/{{ post.slug }}.html" class="news-card-img"><img src="{{ post.image_url }}" alt="{{ post.title }}" loading="lazy"></a>
      <a href="../category-{{ post.category|lower }}.html" class="cat-badge">{{ post.category }}</a>
      <h3><a href="../posts/{{ post.slug }}.html">{{ post.title }}</a></h3>
      <p>{{ post.excerpt[:100] }}...</p>
      <div class="news-card-meta"><time>{{ post.date_human }}</time><span class="dot">·</span><span>{{ post.read_time }}</span></div>
    </article>
    {% endfor %}
  </div>
  {% else %}
  <p style="color:var(--text2);padding:40px 0">No articles published yet.</p>
  {% endif %}
</div>
{{ footer }}
</body></html>'''

# ── BUILDERS ──────────────────────────────────────────────────────
def build_sidebar(posts, count=5):
    html = ""
    for p in posts[:count]:
        html += f'''<a href="{SITE_URL}/posts/{p["slug"]}.html" class="sidebar-post">
  <div class="sidebar-post-img"><img src="{p["image_url"]}" alt="{p["title"]}" loading="lazy"></div>
  <div><h4>{p["title"][:55]}{"..." if len(p["title"])>55 else ""}</h4>
  <div class="sidebar-post-date">{p["date_human"]}</div></div>
</a>'''
    return html

def build_post_html(data, author, posts_index):
    now = datetime.now(timezone.utc)
    sidebar = build_sidebar([p for p in posts_index if p["slug"] != data["slug"]])
    return Template(POST_TPL).render(
        **data, author=author, sidebar_html=sidebar,
        nav=get_nav("../"), footer=get_footer("../"),
        site_name=SITE_NAME, site_url=SITE_URL,
        date_iso=now.isoformat(), date_human=now.strftime("%B %d, %Y"), year=now.year,
    )

def rebuild_homepage(posts):
    sorted_posts = sorted(posts, key=lambda x: x["date_iso"], reverse=True)
    for p in sorted_posts:
        if not p.get("excerpt"): p["excerpt"] = p.get("meta_description","")
        if not p.get("author_name"): p["author_name"] = "Staff Reporter"
        if not p.get("author_avatar"): p["author_avatar"] = "https://i.pravatar.cc/150?img=10"
        if not p.get("author_id"): p["author_id"] = "staff"
    html = Template(INDEX_TPL).render(
        posts=sorted_posts[:50], categories=CATEGORIES,
        site_name=SITE_NAME, site_url=SITE_URL, site_tagline=SITE_TAGLINE,
        nav=get_nav(), footer=get_footer(),
        today=datetime.now().strftime("%B %d, %Y"), year=datetime.now().year,
    )
    (OUTPUT_DIR / "index.html").write_text(html)

def rebuild_categories(posts):
    sorted_posts = sorted(posts, key=lambda x: x["date_iso"], reverse=True)
    for cat in CATEGORIES:
        cat_posts = [p for p in sorted_posts if p.get("category","").lower() == cat.lower()]
        html = Template(CAT_TPL).render(
            posts=cat_posts, category=cat, categories=CATEGORIES,
            site_name=SITE_NAME, site_url=SITE_URL,
            nav=get_nav(), footer=get_footer(), year=datetime.now().year,
        )
        (OUTPUT_DIR / f"category-{cat.lower()}.html").write_text(html)

def rebuild_author_pages(posts):
    AUTHORS_DIR.mkdir(exist_ok=True)
    # Collect all authors
    all_authors = {}
    for cat_authors in AUTHORS.values():
        for a in cat_authors:
            all_authors[a["id"]] = a
    
    # Build author pages
    for author_id, author in all_authors.items():
        author_posts = [p for p in posts if p.get("author_id") == author_id]
        author_posts = sorted(author_posts, key=lambda x: x["date_iso"], reverse=True)
        html = Template(AUTHOR_TPL).render(
            author=author, posts=author_posts,
            site_name=SITE_NAME, site_url=SITE_URL,
            nav=get_nav("../"), footer=get_footer("../"),
            year=datetime.now().year,
        )
        (AUTHORS_DIR / f"{author_id}.html").write_text(html)

def rebuild_sitemap(posts):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             f'  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>']
    for cat in CATEGORIES:
        lines.append(f'  <url><loc>{SITE_URL}/category-{cat.lower()}.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>')
    for p in posts:
        lines.append(f'  <url><loc>{SITE_URL}/posts/{p["slug"]}.html</loc><lastmod>{p["date_iso"][:10]}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>')
    lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines))

# ── MAIN ──────────────────────────────────────────────────────────
def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(exist_ok=True)

    published   = load_published()
    posts_index = load_posts_index()

    print(f"📰 Getting {ARTICLES_PER_RUN} unique topics...")
    topics = build_topics(ARTICLES_PER_RUN, published)

    new_count = 0
    for i, t in enumerate(topics):
        title = t["title"]
        slug  = slugify(title)
        if slug in published:
            continue

        print(f"  ✍  [{i+1}/{len(topics)}] {title}")
        
        # Pass existing posts for internal linking
        related = random.sample(posts_index, min(3, len(posts_index))) if posts_index else []
        
        article = write_article(title, t.get("hint",""))
        if not article:
            continue

        article["slug"] = slugify(article["title"])
        category = article.get("category","World")
        author   = get_author(category)
        image    = get_image(article.get("image_keyword", article["focus_keyword"]), article["slug"])
        article["image_url"] = image

        now = datetime.now(timezone.utc)
        
        # Build and save post HTML
        html = build_post_html(article, author, posts_index)
        (POSTS_DIR / f"{article['slug']}.html").write_text(html)

        posts_index.append({
            "slug":          article["slug"],
            "title":         article["title"],
            "meta_description": article["meta_description"],
            "excerpt":       article.get("excerpt", article["meta_description"]),
            "category":      category,
            "tags":          article.get("tags",[]),
            "image_url":     image,
            "read_time":     article.get("read_time","5 min read"),
            "author_name":   author["name"],
            "author_title":  author["title"],
            "author_avatar": author["avatar"],
            "author_id":     author["id"],
            "date_iso":      now.isoformat(),
            "date_human":    now.strftime("%B %d, %Y"),
        })
        published.add(article["slug"])
        new_count += 1
        time.sleep(2)

    print(f"\n✅ {new_count} new articles generated")
    print("🏠 Rebuilding all pages...")
    rebuild_homepage(posts_index)
    rebuild_categories(posts_index)
    rebuild_author_pages(posts_index)
    rebuild_sitemap(posts_index)
    save_published(published)
    save_posts_index(posts_index)
    print("🎉 Done!")

if __name__ == "__main__":
    main()
