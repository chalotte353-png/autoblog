import os, json, time, random, requests, re
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Template

CLAUDE_API_KEY   = os.environ.get("CLAUDE_API_KEY", "")
NEWS_API_KEY     = os.environ.get("NEWS_API_KEY", "")
UNSPLASH_KEY     = os.environ.get("UNSPLASH_KEY", "")
SITE_URL         = os.environ.get("SITE_URL", "https://marketsnewstoday.info")
SITE_NAME        = os.environ.get("SITE_NAME", "Markets News Today")
SITE_TAGLINE     = os.environ.get("SITE_TAGLINE", "Business - Finance - Technology - World")
OUTPUT_DIR       = Path("output")
POSTS_DIR        = OUTPUT_DIR / "posts"
AUTHORS_DIR      = OUTPUT_DIR / "authors"
ARTICLES_PER_RUN = int(os.environ.get("ARTICLES_PER_RUN", "10"))

CATEGORIES = ["Business","Technology","Finance","World","Sports","Health","Travel","Science","Entertainment","Politics"]

AUTHORS = {
    "Business": [
        {"id":"james-mitchell","name":"James Mitchell","title":"Business Editor","bio":"15 years covering global markets and corporate strategy.","avatar":"https://i.pravatar.cc/150?img=11","twitter":"@jmitchell_biz"},
        {"id":"sarah-chen","name":"Sarah Chen","title":"Senior Finance Reporter","bio":"Former Wall Street analyst turned journalist.","avatar":"https://i.pravatar.cc/150?img=47","twitter":"@sarahchen_fin"},
        {"id":"robert-hayes","name":"Robert Hayes","title":"Economics Correspondent","bio":"Oxford economics graduate, expert in market trends.","avatar":"https://i.pravatar.cc/150?img=15","twitter":"@roberthayes_econ"},
    ],
    "Technology": [
        {"id":"alex-rivera","name":"Alex Rivera","title":"Tech Editor","bio":"Silicon Valley insider with 10+ years in tech journalism.","avatar":"https://i.pravatar.cc/150?img=12","twitter":"@alexrivera_tech"},
        {"id":"maya-patel","name":"Maya Patel","title":"AI Reporter","bio":"MIT graduate specializing in emerging technologies.","avatar":"https://i.pravatar.cc/150?img=48","twitter":"@mayapatel_ai"},
        {"id":"tom-bradley","name":"Tom Bradley","title":"Cybersecurity Analyst","bio":"Former NSA contractor turned journalist.","avatar":"https://i.pravatar.cc/150?img=16","twitter":"@tombradley_sec"},
    ],
    "Finance": [
        {"id":"david-park","name":"David Park","title":"Markets Editor","bio":"CFA charterholder with global finance expertise.","avatar":"https://i.pravatar.cc/150?img=13","twitter":"@davidpark_mkt"},
        {"id":"lisa-wong","name":"Lisa Wong","title":"Investment Reporter","bio":"Covers hedge funds and capital markets.","avatar":"https://i.pravatar.cc/150?img=49","twitter":"@lisawong_inv"},
        {"id":"mark-thompson","name":"Mark Thompson","title":"Crypto Correspondent","bio":"Blockchain technology expert since 2013.","avatar":"https://i.pravatar.cc/150?img=17","twitter":"@markthompson_crypto"},
    ],
    "World": [
        {"id":"elena-vasquez","name":"Elena Vasquez","title":"World Affairs Editor","bio":"Award-winning foreign correspondent, 50+ countries.","avatar":"https://i.pravatar.cc/150?img=21","twitter":"@elenavasquez_world"},
        {"id":"hassan-ahmed","name":"Hassan Ahmed","title":"Middle East Bureau Chief","bio":"20 years reporting from conflict zones worldwide.","avatar":"https://i.pravatar.cc/150?img=52","twitter":"@hassan_ahmed_me"},
        {"id":"anna-kowalski","name":"Anna Kowalski","title":"Europe Correspondent","bio":"Brussels-based EU politics and diplomacy expert.","avatar":"https://i.pravatar.cc/150?img=25","twitter":"@annakowalski_eu"},
    ],
    "Sports": [
        {"id":"chris-johnson","name":"Chris Johnson","title":"Sports Editor","bio":"Former professional athlete turned journalist.","avatar":"https://i.pravatar.cc/150?img=14","twitter":"@chrisjohnson_sports"},
        {"id":"maria-santos","name":"Maria Santos","title":"Football Correspondent","bio":"Premier League and Champions League expert.","avatar":"https://i.pravatar.cc/150?img=44","twitter":"@mariasantos_fc"},
        {"id":"kevin-williams","name":"Kevin Williams","title":"US Sports Reporter","bio":"NBA, NFL and MLB insider access.","avatar":"https://i.pravatar.cc/150?img=18","twitter":"@kevinwilliams_us"},
    ],
    "Health": [
        {"id":"jennifer-ross","name":"Dr. Jennifer Ross","title":"Health Editor","bio":"MD with specialization in public health.","avatar":"https://i.pravatar.cc/150?img=23","twitter":"@drjenniferross"},
        {"id":"michael-green","name":"Michael Green","title":"Medical Correspondent","bio":"Science writer covering medical research.","avatar":"https://i.pravatar.cc/150?img=53","twitter":"@michaelgreen_med"},
        {"id":"rachel-kim","name":"Rachel Kim","title":"Wellness Reporter","bio":"Mental health and nutrition science expert.","avatar":"https://i.pravatar.cc/150?img=26","twitter":"@rachelkim_health"},
    ],
    "Travel": [
        {"id":"sophie-laurent","name":"Sophie Laurent","title":"Travel Editor","bio":"Visited 90+ countries, luxury travel expert.","avatar":"https://i.pravatar.cc/150?img=24","twitter":"@sophielaurent_travel"},
        {"id":"diego-morales","name":"Diego Morales","title":"Adventure Travel Writer","bio":"Six continents, remote culture documentation.","avatar":"https://i.pravatar.cc/150?img=54","twitter":"@diegomorales_adv"},
        {"id":"emma-wilson","name":"Emma Wilson","title":"Food and Travel Reporter","bio":"Culinary travel expert, 60+ countries reviewed.","avatar":"https://i.pravatar.cc/150?img=27","twitter":"@emmawilson_food"},
    ],
    "Science": [
        {"id":"neil-foster","name":"Dr. Neil Foster","title":"Science Editor","bio":"PhD Astrophysics Caltech, former NASA JPL.","avatar":"https://i.pravatar.cc/150?img=33","twitter":"@drneifoster_sci"},
        {"id":"laura-martinez","name":"Laura Martinez","title":"Climate Reporter","bio":"Environmental science journalist.","avatar":"https://i.pravatar.cc/150?img=55","twitter":"@lauramartinez_clim"},
        {"id":"james-liu","name":"James Liu","title":"Space Correspondent","bio":"NASA press corps, 20+ rocket launches.","avatar":"https://i.pravatar.cc/150?img=34","twitter":"@jamesliu_space"},
    ],
    "Entertainment": [
        {"id":"jessica-taylor","name":"Jessica Taylor","title":"Entertainment Editor","bio":"Hollywood insider with major studio access.","avatar":"https://i.pravatar.cc/150?img=35","twitter":"@jessicataylor_ent"},
        {"id":"brandon-lee","name":"Brandon Lee","title":"Music Reporter","bio":"Grammy-nominated producer turned journalist.","avatar":"https://i.pravatar.cc/150?img=56","twitter":"@brandonlee_music"},
        {"id":"olivia-brown","name":"Olivia Brown","title":"Film Critic","bio":"BAFTA voter, Cannes Film Festival regular.","avatar":"https://i.pravatar.cc/150?img=36","twitter":"@oliviabrown_film"},
    ],
    "Politics": [
        {"id":"andrew-collins","name":"Andrew Collins","title":"Political Editor","bio":"20 years covering Washington DC politics.","avatar":"https://i.pravatar.cc/150?img=37","twitter":"@andrewcollins_pol"},
        {"id":"patricia-morgan","name":"Patricia Morgan","title":"Policy Correspondent","bio":"Former White House press pool journalist.","avatar":"https://i.pravatar.cc/150?img=57","twitter":"@patriciamorgan_dc"},
        {"id":"samuel-davis","name":"Samuel Davis","title":"International Affairs","bio":"US foreign policy and geopolitics expert.","avatar":"https://i.pravatar.cc/150?img=38","twitter":"@samueldavis_intl"},
    ],
}

WIKI_TOPICS = [
    "Stock market outlook May 2026","AI revolution in business 2026","Bitcoin price analysis 2026",
    "Tesla quarterly earnings report","Federal Reserve rate decision","Climate change business impact",
    "Electric vehicle market growth","US housing market trends","Global trade policy update",
    "Tech startup funding landscape","Cybersecurity threats enterprise","Mental health workplace 2026",
    "Renewable energy investment boom","China economy latest data","India GDP growth 2026",
    "SpaceX mission update","Apple product launch 2026","Amazon business strategy",
    "Healthcare innovation breakthroughs","Supply chain global update",
]

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
                headers={"Authorization": "Client-ID " + UNSPLASH_KEY},
                timeout=8,
            )
            if r.status_code == 200:
                return r.json()["urls"]["regular"]
        except Exception:
            pass
    seed = abs(hash(slug)) % 1000
    return "https://picsum.photos/seed/" + str(seed) + "/1200/630"

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

def fetch_news_topics(count):
    if not NEWS_API_KEY:
        return []
    try:
        r = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"language": "en", "pageSize": min(count * 3, 100), "apiKey": NEWS_API_KEY},
            timeout=10,
        )
        topics = []
        seen = set()
        for a in r.json().get("articles", []):
            t = a.get("title", "")
            d = a.get("description", "") or ""
            if t and "[Removed]" not in t:
                key = slugify(t)[:40]
                if key not in seen:
                    seen.add(key)
                    topics.append({"title": t, "hint": d[:300]})
        return topics
    except Exception as e:
        print("NewsAPI: " + str(e))
        return []

def build_topics(count, published):
    news = fetch_news_topics(count * 2)
    fresh = []
    published_short = {s[:40] for s in published}
    for t in news:
        if slugify(t["title"])[:40] not in published_short:
            fresh.append(t)
    pool = WIKI_TOPICS.copy()
    random.shuffle(pool)
    while len(fresh) < count and pool:
        t = pool.pop()
        if slugify(t)[:40] not in published_short:
            fresh.append({"title": t, "hint": ""})
    return fresh[:count]

def write_article(topic, hint):
    now = datetime.now()
    prompt = """Write a professional Forbes-quality news article dated """ + now.strftime("%B %d, %Y") + """ about this topic: """ + topic + """

Background: """ + hint + """

Respond using EXACTLY this XML format:
<article>
<title>Compelling headline 55-70 chars</title>
<slug>url-slug-from-title</slug>
<meta_description>SEO description 150-158 chars</meta_description>
<focus_keyword>primary keyword phrase</focus_keyword>
<category>Business or Technology or Finance or World or Sports or Health or Travel or Science or Entertainment or Politics</category>
<image_keyword>3-4 word image search</image_keyword>
<read_time>X min read</read_time>
<excerpt>2-3 sentence compelling summary</excerpt>
<tags>tag1,tag2,tag3</tags>
<content>
FULL ARTICLE HTML HERE - minimum 900 words - use h2 h3 p ul strong tags - professional Forbes-style writing
</content>
</article>"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 3000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=90,
        )
        resp = r.json()
        if "content" not in resp:
            print("  Claude error: " + str(resp))
            return None
        raw = resp["content"][0]["text"].strip()

        def extract(tag):
            m = re.search(r"<" + tag + r">(.*?)</" + tag + r">", raw, re.DOTALL)
            return m.group(1).strip() if m else ""

        title = extract("title")
        if not title:
            print("  Could not parse response")
            return None

        tags_str = extract("tags")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        data = {
            "title": title,
            "slug": slugify(title),
            "meta_description": extract("meta_description"),
            "focus_keyword": extract("focus_keyword"),
            "category": extract("category").strip(),
            "image_keyword": extract("image_keyword"),
            "read_time": extract("read_time") or "5 min read",
            "excerpt": extract("excerpt"),
            "tags": tags,
            "article_html": extract("content"),
        }
        return data
    except Exception as e:
        print("  Article error: " + str(e))
        return None

def get_nav(prefix=""):
    year = datetime.now().year
    return (
        '<header>'
        '<div class="top-bar"><div class="top-bar-inner">'
        '<span class="top-bar-date">' + datetime.now().strftime("%A, %B %d, %Y") + '</span>'
        '<a href="' + prefix + 'index.html" class="top-bar-logo">Markets<span>News</span>Today</a>'
        '<span class="top-bar-tagline">Business - Finance - Technology</span>'
        '</div></div>'
        '<nav class="main-nav-bar"><div class="nav-inner">'
        '<a href="' + prefix + 'index.html">Home</a>'
        '<a href="' + prefix + 'category-business.html">Business</a>'
        '<a href="' + prefix + 'category-technology.html">Technology</a>'
        '<a href="' + prefix + 'category-finance.html">Finance</a>'
        '<a href="' + prefix + 'category-world.html">World</a>'
        '<a href="' + prefix + 'category-sports.html">Sports</a>'
        '<a href="' + prefix + 'category-health.html">Health</a>'
        '<a href="' + prefix + 'category-politics.html">Politics</a>'
        '<a href="' + prefix + 'networth/index.html">Net Worth</a>'
        '</div></nav></header>'
    )

def get_footer(prefix=""):
    year = datetime.now().year
    return (
        '<footer class="site-footer">'
        '<div class="footer-top"><div class="container"><div class="footer-grid">'
        '<div class="footer-brand">'
        '<div class="footer-brand-name">Markets<span>News</span>Today</div>'
        '<p>Your trusted source for breaking news and expert analysis.</p>'
        '</div>'
        '<div class="footer-col"><h4>Business</h4>'
        '<a href="' + prefix + 'category-business.html">Business</a>'
        '<a href="' + prefix + 'category-finance.html">Finance</a>'
        '<a href="' + prefix + 'category-technology.html">Technology</a>'
        '<a href="' + prefix + 'networth/index.html">Net Worth</a>'
        '</div>'
        '<div class="footer-col"><h4>World</h4>'
        '<a href="' + prefix + 'category-world.html">World</a>'
        '<a href="' + prefix + 'category-politics.html">Politics</a>'
        '<a href="' + prefix + 'category-sports.html">Sports</a>'
        '<a href="' + prefix + 'category-entertainment.html">Entertainment</a>'
        '</div>'
        '<div class="footer-col"><h4>More</h4>'
        '<a href="' + prefix + 'category-health.html">Health</a>'
        '<a href="' + prefix + 'category-science.html">Science</a>'
        '<a href="' + prefix + 'category-travel.html">Travel</a>'
        '<a href="' + prefix + 'sitemap.xml">Sitemap</a>'
        '</div>'
        '</div></div></div>'
        '<div class="footer-bottom"><div class="container">'
        '<p>&copy; ' + str(year) + ' Markets News Today. All rights reserved.</p>'
        '</div></div>'
        '</footer>'
    )

def build_sidebar(posts, current_slug="", count=5):
    html = ""
    for p in [x for x in posts if x["slug"] != current_slug][:count]:
        title = p["title"][:55] + ("..." if len(p["title"]) > 55 else "")
        html += (
            '<a href="' + SITE_URL + '/posts/' + p["slug"] + '.html" class="sidebar-post">'
            '<div class="sidebar-post-img"><img src="' + p["image_url"] + '" alt="' + title + '" loading="lazy"></div>'
            '<div><h4>' + title + '</h4>'
            '<div class="sidebar-post-date">' + p["date_human"] + '</div></div>'
            '</a>'
        )
    return html

def build_related(posts, current_slug, count=3):
    related = [p for p in posts if p["slug"] != current_slug][:count]
    if not related:
        return ""
    html = '<div class="related-posts"><h3>Related Articles</h3><ul>'
    for p in related:
        html += '<li><a href="' + SITE_URL + '/posts/' + p["slug"] + '.html">' + p["title"] + '</a></li>'
    html += "</ul></div>"
    return html

def build_post_html(data, author, posts_index, now):
    sidebar = build_sidebar(posts_index, data["slug"])
    related = build_related(posts_index, data["slug"])
    schema = (
        '{"@context":"https://schema.org","@type":"Article",'
        '"headline":"' + data["title"] + '",'
        '"image":"' + data["image_url"] + '",'
        '"datePublished":"' + now.isoformat() + '",'
        '"author":{"@type":"Person","name":"' + author["name"] + '","url":"' + SITE_URL + '/authors/' + author["id"] + '.html"},'
        '"publisher":{"@type":"Organization","name":"' + SITE_NAME + '","url":"' + SITE_URL + '"}}'
    )
    tags_html = "".join(['<a href="' + SITE_URL + '/index.html" class="tag">' + t + '</a>' for t in data.get("tags", [])])
    html = (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + data["title"] + ' | ' + SITE_NAME + '</title>'
        '<meta name="description" content="' + data["meta_description"] + '">'
        '<meta name="author" content="' + author["name"] + '">'
        '<meta name="robots" content="index,follow">'
        '<link rel="canonical" href="' + SITE_URL + '/posts/' + data["slug"] + '.html">'
        '<meta property="og:title" content="' + data["title"] + '">'
        '<meta property="og:description" content="' + data["meta_description"] + '">'
        '<meta property="og:image" content="' + data["image_url"] + '">'
        '<meta property="og:type" content="article">'
        '<script type="application/ld+json">' + schema + '</script>'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link rel="stylesheet" href="../style.css">'
        '</head><body>'
        + get_nav("../") +
        '<div class="post-wrap"><div class="container post-layout"><article class="post-main">'
        '<div class="post-header">'
        '<a href="../category-' + data["category"].lower() + '.html" class="cat-badge">' + data["category"] + '</a>'
        '<h1>' + data["title"] + '</h1>'
        '<p class="post-desc">' + data.get("excerpt", data["meta_description"]) + '</p>'
        '<div class="post-meta-bar">'
        '<img src="' + author["avatar"] + '" alt="' + author["name"] + '" class="author-avatar">'
        '<div><a href="../authors/' + author["id"] + '.html" class="author-link">' + author["name"] + '</a>'
        '<div class="author-title-text">' + author["title"] + '</div></div>'
        '<span class="meta-sep">·</span>'
        '<time datetime="' + now.isoformat() + '">' + now.strftime("%B %d, %Y") + '</time>'
        '<span class="meta-sep">·</span>'
        '<span>' + data.get("read_time", "5 min read") + '</span>'
        '</div></div>'
        '<figure class="post-hero-img">'
        '<img src="' + data["image_url"] + '" alt="' + data["title"] + '" loading="eager" width="820" height="461">'
        '</figure>'
        '<div class="post-body">' + data["article_html"] + '</div>'
        + related +
        '<div class="post-tags-wrap">' + tags_html + '</div>'
        '<div class="author-card">'
        '<img src="' + author["avatar"] + '" alt="' + author["name"] + '" class="author-card-img">'
        '<div><div class="author-card-name">' + author["name"] + '</div>'
        '<div class="author-card-role">' + author["title"] + '</div>'
        '<p class="author-card-bio">' + author["bio"] + '</p>'
        '<a href="../authors/' + author["id"] + '.html" class="cat-badge" style="margin-top:10px;display:inline-block">View Profile</a>'
        '</div></div>'
        '</article>'
        '<aside><div class="sidebar-widget"><div class="sidebar-widget-title">Trending Now</div>' + sidebar + '</div></aside>'
        '</div></div>'
        + get_footer("../") +
        '</body></html>'
    )
    return html

def rebuild_homepage(posts):
    sorted_posts = sorted(posts, key=lambda x: x["date_iso"], reverse=True)
    for p in sorted_posts:
        if not p.get("excerpt"): p["excerpt"] = p.get("meta_description", "")
        if not p.get("author_name"): p["author_name"] = "Staff Reporter"
        if not p.get("author_avatar"): p["author_avatar"] = "https://i.pravatar.cc/150?img=10"
        if not p.get("author_id"): p["author_id"] = "staff"

    hero = sorted_posts[0] if sorted_posts else None
    sidebar_posts = sorted_posts[1:5] if len(sorted_posts) > 1 else []
    grid_posts = sorted_posts[5:] if len(sorted_posts) > 5 else []

    hero_html = ""
    if hero:
        sidebar_items = ""
        for p in sidebar_posts:
            sidebar_items += (
                '<a href="posts/' + p["slug"] + '.html" class="sidebar-story">'
                '<div class="sidebar-story-img"><img src="' + p["image_url"] + '" alt="' + p["title"] + '" loading="lazy"></div>'
                '<div><span class="cat-badge">' + p["category"] + '</span>'
                '<h3>' + p["title"] + '</h3>'
                '<div class="sidebar-story-meta">' + p["author_name"] + ' · ' + p["date_human"] + '</div></div>'
                '</a>'
            )
        hero_html = (
            '<section class="top-stories"><div class="container">'
            '<div class="section-label"><span class="section-label-text">Top Stories</span>'
            '<div class="section-label-line"></div>'
            '<span class="section-label-sub">' + datetime.now().strftime("%B %d, %Y") + '</span></div>'
            '<div class="top-stories-grid">'
            '<a href="posts/' + hero["slug"] + '.html" class="hero-story">'
            '<div class="hero-story-img"><img src="' + hero["image_url"] + '" alt="' + hero["title"] + '" loading="eager"></div>'
            '<a href="category-' + hero["category"].lower() + '.html" class="cat-badge">' + hero["category"] + '</a>'
            '<h1>' + hero["title"] + '</h1>'
            '<p>' + hero["excerpt"] + '</p>'
            '<div class="hero-meta">'
            '<img src="' + hero["author_avatar"] + '" alt="' + hero["author_name"] + '" class="hero-avatar">'
            '<a href="authors/' + hero.get("author_id","staff") + '.html" class="author-link">' + hero["author_name"] + '</a>'
            '<span class="dot">·</span><span>' + hero["date_human"] + '</span>'
            '</div></a>'
            '<div class="sidebar-stories">' + sidebar_items + '</div>'
            '</div></div></section>'
        )

    grid_html = ""
    for p in grid_posts:
        excerpt = p.get("excerpt", p.get("meta_description",""))[:110]
        grid_html += (
            '<article class="news-card">'
            '<a href="posts/' + p["slug"] + '.html" class="news-card-img">'
            '<img src="' + p["image_url"] + '" alt="' + p["title"] + '" loading="lazy"></a>'
            '<a href="category-' + p["category"].lower() + '.html" class="cat-badge">' + p["category"] + '</a>'
            '<h3><a href="posts/' + p["slug"] + '.html">' + p["title"] + '</a></h3>'
            '<p>' + excerpt + '...</p>'
            '<div class="news-card-meta">'
            '<img src="' + p["author_avatar"] + '" alt="' + p["author_name"] + '" class="news-card-avatar">'
            '<a href="authors/' + p.get("author_id","staff") + '.html" class="author-link" style="font-size:.73rem">' + p["author_name"] + '</a>'
            '<span class="dot">·</span><time>' + p["date_human"] + '</time>'
            '</div></article>'
        )

    sidebar_widget = ""
    for p in sorted_posts[:6]:
        title = p["title"][:55] + ("..." if len(p["title"]) > 55 else "")
        sidebar_widget += (
            '<a href="posts/' + p["slug"] + '.html" class="sidebar-post">'
            '<div class="sidebar-post-img"><img src="' + p["image_url"] + '" alt="' + title + '" loading="lazy"></div>'
            '<div><h4>' + title + '</h4><div class="sidebar-post-date">' + p["date_human"] + '</div></div>'
            '</a>'
        )

    cat_widget = ""
    for cat in CATEGORIES:
        cat_widget += '<a href="category-' + cat.lower() + '.html" style="display:block;padding:8px 0;border-bottom:1px solid var(--border);font-size:.82rem;font-weight:700;text-transform:uppercase">' + cat + '</a>'

    schema = '{"@context":"https://schema.org","@type":"WebSite","name":"' + SITE_NAME + '","url":"' + SITE_URL + '"}'

    html = (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + SITE_NAME + ' - ' + SITE_TAGLINE + '</title>'
        '<meta name="description" content="Breaking news and analysis on business, finance, technology and world affairs.">'
        '<meta name="robots" content="index,follow"><link rel="canonical" href="' + SITE_URL + '/">'
        '<script type="application/ld+json">' + schema + '</script>'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link rel="stylesheet" href="style.css">'
        '</head><body>'
        + get_nav() + hero_html +
        '<div class="container main-layout"><main>'
        '<div class="section-label"><span class="section-label-text">Latest News</span><div class="section-label-line"></div></div>'
        '<div class="news-grid-3">' + grid_html + '</div>'
        '</main><aside>'
        '<div class="sidebar-widget"><div class="sidebar-widget-title">Most Read</div>' + sidebar_widget + '</div>'
        '<div class="sidebar-widget"><div class="sidebar-widget-title">Sections</div>' + cat_widget + '</div>'
        '</aside></div>'
        + get_footer() +
        '</body></html>'
    )
    (OUTPUT_DIR / "index.html").write_text(html)

def rebuild_categories(posts):
    sorted_posts = sorted(posts, key=lambda x: x["date_iso"], reverse=True)
    for cat in CATEGORIES:
        cat_posts = [p for p in sorted_posts if p.get("category","").lower() == cat.lower()]
        grid_html = ""
        for p in cat_posts:
            excerpt = p.get("excerpt", p.get("meta_description",""))[:110]
            grid_html += (
                '<article class="news-card">'
                '<a href="posts/' + p["slug"] + '.html" class="news-card-img">'
                '<img src="' + p["image_url"] + '" alt="' + p["title"] + '" loading="lazy"></a>'
                '<a href="category-' + p["category"].lower() + '.html" class="cat-badge">' + p["category"] + '</a>'
                '<h3><a href="posts/' + p["slug"] + '.html">' + p["title"] + '</a></h3>'
                '<p>' + excerpt + '...</p>'
                '<div class="news-card-meta">'
                '<img src="' + p.get("author_avatar","") + '" alt="' + p.get("author_name","") + '" class="news-card-avatar">'
                '<span style="font-size:.73rem">' + p.get("author_name","Staff") + '</span>'
                '<span class="dot">·</span><time>' + p["date_human"] + '</time>'
                '</div></article>'
            )
        empty = '<div class="empty-cat"><p>No articles yet. Check back soon!</p><a href="index.html" class="btn-back">Back to Home</a></div>' if not cat_posts else ""
        cat_widget = ""
        for c in CATEGORIES:
            cat_widget += '<a href="category-' + c.lower() + '.html" style="display:block;padding:8px 0;border-bottom:1px solid var(--border);font-size:.82rem;font-weight:700;text-transform:uppercase">' + c + '</a>'
        html = (
            '<!DOCTYPE html><html lang="en"><head>'
            '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + cat + ' News | ' + SITE_NAME + '</title>'
            '<meta name="description" content="Latest ' + cat + ' news and analysis on ' + SITE_NAME + '.">'
            '<meta name="robots" content="index,follow">'
            '<link rel="canonical" href="' + SITE_URL + '/category-' + cat.lower() + '.html">'
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link rel="stylesheet" href="style.css">'
            '</head><body>'
            + get_nav() +
            '<div class="container">'
            '<div class="cat-header"><div class="cat-header-label">Section</div>'
            '<h1>' + cat + '</h1>'
            '<p>Latest ' + cat + ' news, analysis and expert commentary</p></div>'
            '<div class="main-layout"><main>'
            '<div class="news-grid-3">' + grid_html + '</div>' + empty +
            '</main><aside>'
            '<div class="sidebar-widget"><div class="sidebar-widget-title">All Sections</div>' + cat_widget + '</div>'
            '</aside></div></div>'
            + get_footer() +
            '</body></html>'
        )
        (OUTPUT_DIR / ("category-" + cat.lower() + ".html")).write_text(html)

def rebuild_author_pages(posts):
    AUTHORS_DIR.mkdir(exist_ok=True)
    all_authors = {}
    for cat_authors in AUTHORS.values():
        for a in cat_authors:
            all_authors[a["id"]] = a

    for author_id, author in all_authors.items():
        author_posts = sorted([p for p in posts if p.get("author_id") == author_id], key=lambda x: x["date_iso"], reverse=True)
        grid_html = ""
        for p in author_posts:
            excerpt = p.get("excerpt", p.get("meta_description",""))[:100]
            grid_html += (
                '<article class="news-card">'
                '<a href="../posts/' + p["slug"] + '.html" class="news-card-img">'
                '<img src="' + p["image_url"] + '" alt="' + p["title"] + '" loading="lazy"></a>'
                '<a href="../category-' + p["category"].lower() + '.html" class="cat-badge">' + p["category"] + '</a>'
                '<h3><a href="../posts/' + p["slug"] + '.html">' + p["title"] + '</a></h3>'
                '<p>' + excerpt + '...</p>'
                '<div class="news-card-meta"><time>' + p["date_human"] + '</time></div>'
                '</article>'
            )
        schema = (
            '{"@context":"https://schema.org","@type":"Person",'
            '"name":"' + author["name"] + '",'
            '"jobTitle":"' + author["title"] + '",'
            '"description":"' + author["bio"] + '",'
            '"image":"' + author["avatar"] + '",'
            '"url":"' + SITE_URL + '/authors/' + author["id"] + '.html",'
            '"worksFor":{"@type":"Organization","name":"' + SITE_NAME + '"}}'
        )
        html = (
            '<!DOCTYPE html><html lang="en"><head>'
            '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + author["name"] + ' - ' + author["title"] + ' | ' + SITE_NAME + '</title>'
            '<meta name="description" content="' + author["bio"] + '">'
            '<meta name="robots" content="index,follow">'
            '<link rel="canonical" href="' + SITE_URL + '/authors/' + author["id"] + '.html">'
            '<script type="application/ld+json">' + schema + '</script>'
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link rel="stylesheet" href="../style.css">'
            '</head><body>'
            + get_nav("../") +
            '<div class="container author-profile">'
            '<div class="author-profile-header">'
            '<img src="' + author["avatar"] + '" alt="' + author["name"] + '" class="author-profile-img">'
            '<div><div class="author-profile-name">' + author["name"] + '</div>'
            '<div class="author-profile-role">' + author["title"] + '</div>'
            '<p class="author-profile-bio">' + author["bio"] + '</p>'
            '<div style="margin-top:8px;font-size:.8rem;color:var(--text3)">' + author["twitter"] + '</div>'
            '</div></div>'
            '<div class="section-label"><span class="section-label-text">Articles by ' + author["name"] + '</span><div class="section-label-line"></div></div>'
            '<div class="news-grid-3">' + grid_html + '</div>'
            '</div>'
            + get_footer("../") +
            '</body></html>'
        )
        (AUTHORS_DIR / (author_id + ".html")).write_text(html)

def rebuild_sitemap(posts):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '<url><loc>' + SITE_URL + '/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>',
    ]
    for cat in CATEGORIES:
        lines.append('<url><loc>' + SITE_URL + '/category-' + cat.lower() + '.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>')
    for p in posts:
        lines.append('<url><loc>' + SITE_URL + '/posts/' + p["slug"] + '.html</loc><lastmod>' + p["date_iso"][:10] + '</lastmod><priority>0.8</priority></url>')
    lines.append('</urlset>')
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines))

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(exist_ok=True)
    AUTHORS_DIR.mkdir(exist_ok=True)

    published   = load_published()
    posts_index = load_posts_index()

    print("Getting " + str(ARTICLES_PER_RUN) + " unique topics...")
    topics = build_topics(ARTICLES_PER_RUN, published)

    new_count = 0
    for i, t in enumerate(topics):
        title = t["title"]
        slug  = slugify(title)
        if slug in published:
            continue

        print("  Writing [" + str(i+1) + "/" + str(len(topics)) + "] " + title)
        article = write_article(title, t.get("hint", ""))
        if not article:
            continue

        article["slug"] = slugify(article["title"])
        category = article.get("category", "World")
        author   = get_author(category)
        image    = get_image(article.get("image_keyword", article["focus_keyword"]), article["slug"])
        article["image_url"] = image

        now = datetime.now(timezone.utc)
        html = build_post_html(article, author, posts_index, now)
        (POSTS_DIR / (article["slug"] + ".html")).write_text(html)

        posts_index.append({
            "slug":             article["slug"],
            "title":            article["title"],
            "meta_description": article["meta_description"],
            "excerpt":          article.get("excerpt", article["meta_description"]),
            "category":         category,
            "tags":             article.get("tags", []),
            "image_url":        image,
            "read_time":        article.get("read_time", "5 min read"),
            "author_name":      author["name"],
            "author_title":     author["title"],
            "author_avatar":    author["avatar"],
            "author_id":        author["id"],
            "date_iso":         now.isoformat(),
            "date_human":       now.strftime("%B %d, %Y"),
        })
        published.add(article["slug"])
        new_count += 1
        time.sleep(2)

    print("Generated " + str(new_count) + " new articles")
    rebuild_homepage(posts_index)
    rebuild_categories(posts_index)
    rebuild_author_pages(posts_index)
    rebuild_sitemap(posts_index)
    save_published(published)
    save_posts_index(posts_index)
    print("Done!")

if __name__ == "__main__":
    main()
