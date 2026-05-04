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
ROOT_POSTS_DIR   = Path("posts")  # Root level — Git mein hamesha saare posts rahenge
AUTHORS_DIR      = OUTPUT_DIR / "authors"
ARTICLES_PER_RUN = int(os.environ.get("ARTICLES_PER_RUN", "20"))
CUSTOM_KEYWORDS  = [k.strip() for k in os.environ.get("CUSTOM_KEYWORDS", "").split(",") if k.strip()]

CATEGORIES = ["Business","Technology","Finance","World","Sports","Health","Travel","Science","Entertainment","Politics","Crypto","Forex","Stocks"]

# ── CATEGORY BALANCE ─────────────────────────────────────────────────
# Target distribution per 15 articles per run (4 runs/day = ~60 articles/day)
# All 13 categories properly covered every day
CATEGORY_TARGETS = {
    "World":         2,
    "Politics":      2,
    "Finance":       2,
    "Crypto":        3,   # core site focus
    "Forex":         2,   # core site focus
    "Stocks":        2,   # core site focus
    "Technology":    2,
    "Sports":        2,
    "Entertainment": 2,
    "Health":        1,
    "Business":      1,
    "Science":       1,
    "Travel":        1,
    # Total targets = 23 for 20 slots → healthy competition, balanced coverage
}

# Wiki topics balanced across underrepresented categories
WIKI_TOPICS_BALANCED = {
    "Business":     ["Global mergers and acquisitions 2026","Small business growth strategies 2026",
                     "Corporate sustainability ESG 2026","Supply chain resilience business",
                     "Remote work business productivity 2026","Private equity market trends 2026"],
    "Technology":   ["Artificial intelligence enterprise 2026","Quantum computing breakthrough 2026",
                     "Semiconductor chip shortage update","Cybersecurity threats 2026",
                     "Electric vehicle technology update","5G network expansion 2026"],
    "Finance":      ["Federal Reserve interest rate 2026","US housing market trends 2026",
                     "Global debt crisis 2026","Hedge fund performance 2026",
                     "Private equity trends 2026","Bond market outlook 2026"],
    "Health":       ["Mental health workplace 2026","Cancer treatment breakthrough 2026",
                     "Healthcare innovation 2026","Obesity drug research update",
                     "Antibiotic resistance global","Longevity science 2026"],
    "Science":      ["SpaceX mission update 2026","Climate change research 2026",
                     "CRISPR gene editing breakthrough","Ocean plastic pollution science",
                     "Dark matter discovery 2026","Renewable energy innovation 2026"],
    "Travel":       ["Best travel destinations 2026","Luxury travel trends 2026",
                     "Sustainable eco-tourism 2026","Budget travel tips 2026",
                     "Digital nomad hotspots 2026","Air travel recovery 2026"],
    "World":        ["India economy growth 2026","China trade policy 2026",
                     "European Union politics 2026","Africa development 2026"],
    "Sports":       ["NBA season highlights 2026","Premier League football 2026",
                     "Olympic sports update 2026","Formula 1 season 2026"],
    "Entertainment":["Hollywood box office 2026","Streaming wars update 2026",
                     "Music industry trends 2026","Video game market 2026"],
    "Politics":     ["US Congress legislation 2026","Global elections 2026",
                     "Climate policy international","Trade policy tariffs 2026"],
    "Crypto":       ["Bitcoin price analysis 2026","Ethereum network upgrade 2026",
                     "Cryptocurrency regulation update 2026","DeFi decentralized finance trends",
                     "Bitcoin ETF market update 2026","Altcoin season predictions 2026",
                     "Crypto market bull run 2026","Solana ecosystem growth 2026",
                     "XRP Ripple court case update","Blockchain technology adoption 2026",
                     "Cryptocurrency tax rules 2026","NFT market recovery 2026"],
    "Forex":        ["US Dollar index outlook 2026","EUR USD analysis 2026",
                     "British Pound GBP forecast 2026","Japanese Yen intervention 2026",
                     "Forex trading strategies 2026","Currency war global 2026",
                     "Pakistani Rupee PKR outlook 2026","Indian Rupee INR forecast 2026",
                     "Emerging market currencies 2026","Federal Reserve dollar impact 2026"],
    "Stocks":       ["S&P 500 outlook 2026","NASDAQ tech stocks 2026",
                     "Dow Jones analysis 2026","Stock market crash risk 2026",
                     "Dividend stocks best 2026","Growth stocks to watch 2026",
                     "Apple stock analysis 2026","Tesla stock forecast 2026",
                     "AI stocks investment 2026","Small cap stocks 2026",
                     "Stock market earnings season 2026","IPO market 2026"],
}

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
    "Crypto":        [{"id":"mark-thompson","name":"Mark Thompson","title":"Crypto Correspondent","bio":"Blockchain technology expert since 2013.","avatar":"https://i.pravatar.cc/150?img=17","twitter":"@markthompson_crypto"},
                      {"id":"lisa-wong","name":"Lisa Wong","title":"Digital Assets Reporter","bio":"Covers DeFi, NFTs and cryptocurrency markets.","avatar":"https://i.pravatar.cc/150?img=49","twitter":"@lisawong_inv"},
                      {"id":"alex-rivera","name":"Alex Rivera","title":"Blockchain Editor","bio":"Silicon Valley insider covering Web3 and crypto.","avatar":"https://i.pravatar.cc/150?img=12","twitter":"@alexrivera_tech"}],
    "Forex":         [{"id":"david-park","name":"David Park","title":"Forex Markets Editor","bio":"CFA charterholder with global forex expertise.","avatar":"https://i.pravatar.cc/150?img=13","twitter":"@davidpark_mkt"},
                      {"id":"sarah-chen","name":"Sarah Chen","title":"Currency Strategist","bio":"Former FX trader at Goldman Sachs.","avatar":"https://i.pravatar.cc/150?img=47","twitter":"@sarahchen_fin"},
                      {"id":"robert-hayes","name":"Robert Hayes","title":"FX Correspondent","bio":"Oxford economics graduate, expert in currency markets.","avatar":"https://i.pravatar.cc/150?img=15","twitter":"@roberthayes_econ"}],
    "Stocks":        [{"id":"james-mitchell","name":"James Mitchell","title":"Stocks Editor","bio":"15 years covering Wall Street and equity markets.","avatar":"https://i.pravatar.cc/150?img=11","twitter":"@jmitchell_biz"},
                      {"id":"david-park","name":"David Park","title":"Equities Analyst","bio":"CFA charterholder, S&P 500 and NASDAQ specialist.","avatar":"https://i.pravatar.cc/150?img=13","twitter":"@davidpark_mkt"},
                      {"id":"lisa-wong","name":"Lisa Wong","title":"Investment Reporter","bio":"Covers hedge funds, ETFs and equity markets.","avatar":"https://i.pravatar.cc/150?img=49","twitter":"@lisawong_inv"}],
}

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
                url = r.json()["urls"]["regular"]
                # Convert to WebP — smaller file, faster load, better Core Web Vitals
                url = re.sub(r'fm=jpg', 'fm=webp', url)
                if 'fm=' not in url:
                    url += '&fm=webp'
                return url
        except Exception:
            pass
    seed = abs(hash(slug)) % 1000
    return f"https://picsum.photos/seed/{seed}/1200/630"

def get_thumbnail_url(image_url):
    """Return smaller version of image for sidebars/thumbnails — saves ~70% bandwidth."""
    if 'unsplash.com' in image_url:
        url = re.sub(r'w=\d+', 'w=400', image_url)
        if 'w=' not in url:
            url += '&w=400'
        return url
    return image_url

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


# ── MANUAL RUN ROTATION STATE ────────────────────────────────────────
# Tracks which category comes next in manual runs, so each manual run
# cycles through all categories in order — no repeats until full cycle.
ROTATION_FILE = OUTPUT_DIR / "rotation_state.json"
ROTATION_ORDER = [
    "Crypto", "Forex", "Stocks", "Finance", "World", "Politics",
    "Technology", "Sports", "Business", "Health", "Entertainment",
    "Science", "Travel"
]

def load_rotation_state():
    if ROTATION_FILE.exists():
        try:
            return json.loads(ROTATION_FILE.read_text())
        except Exception:
            pass
    return {"index": 0, "used_this_cycle": []}

def save_rotation_state(state):
    ROTATION_FILE.write_text(json.dumps(state, indent=2))

def get_next_rotation_categories(count):
    """
    Returns a list of `count` categories in rotation order.
    - Single run (count=1): returns next category in cycle
    - Bulk run (count>1): distributes evenly across all categories
    - After full cycle completes, resets and starts again
    """
    state = load_rotation_state()
    idx = state.get("index", 0)
    used = state.get("used_this_cycle", [])
    n = len(ROTATION_ORDER)

    if count == 1:
        # Single article: just pick next in rotation
        cat = ROTATION_ORDER[idx % n]
        new_idx = (idx + 1) % n
        new_used = used + [cat]
        # Reset cycle when complete
        if new_idx == 0:
            new_used = []
        save_rotation_state({"index": new_idx, "used_this_cycle": new_used})
        return [cat]
    else:
        # Bulk run: distribute count articles evenly across all categories
        # e.g. count=13 → 1 each; count=15 → some get 2, rest get 1
        result = []
        per_cat = count // n
        extras = count % n
        for i, cat in enumerate(ROTATION_ORDER):
            times = per_cat + (1 if i < extras else 0)
            result.extend([cat] * times)
        # Reset rotation to beginning after bulk run
        save_rotation_state({"index": 0, "used_this_cycle": []})
        return result

# ── CONVERT EXISTING IMAGES TO WEBP ─────────────────────────────────
def convert_existing_to_webp():
    """Convert all fm=jpg Unsplash URLs to fm=webp in existing HTML files."""
    converted = 0
    for html_file in OUTPUT_DIR.rglob("*.html"):
        try:
            content = html_file.read_text(encoding="utf-8")
            if "fm=jpg" in content:
                updated = re.sub(
                    r'(https://images\.unsplash\.com[^\s"\']*?)fm=jpg',
                    r'\1fm=webp',
                    content
                )
                html_file.write_text(updated, encoding="utf-8")
                converted += content.count("fm=jpg")
        except Exception:
            pass
    if converted:
        print(f"  Converted {converted} images to WebP")
def build_robots():
    """Generate robots.txt with correct SITE_URL — never use placeholder."""
    content = f"""User-agent: *
Allow: /
Disallow: /cgi-bin/
Disallow: /*.json$

Sitemap: {SITE_URL}/sitemap.xml
"""
    (OUTPUT_DIR / "robots.txt").write_text(content)

# ── BUILD RSS FEED ───────────────────────────────────────────────────
def xml_esc(s):
    """Full XML escape — required for RSS feed. Handles &, <, >, ', " all."""
    return (str(s)
        .replace("&", "&amp;")   # must be first!
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;"))

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
    <title>{xml_esc(p["title"])}</title>
    <link>{SITE_URL}/posts/{p["slug"]}.html</link>
    <description>{xml_esc(p.get("excerpt", p.get("meta_description", "")))}</description>
    <pubDate>{pub}</pubDate>
    <guid isPermaLink="true">{SITE_URL}/posts/{p["slug"]}.html</guid>
    <category>{xml_esc(p.get("category","World"))}</category>
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
    Threshold raised to 70% to block slight headline variations on same story.
    """
    # Exact match
    if title_slug in published:
        return True
    # Stopwords to ignore when comparing
    STOP = {"a","an","the","in","on","at","of","and","for","to","is","are","was","were",
            "it","its","as","by","with","from","that","this","has","have","after","over",
            "into","about","up","out","than","but","be","been","their","his","her","our",
            "us","new","says","say","after","amid","over","set","get","gets","make"}
    words = set(title_slug.split("-")) - STOP
    if not words:
        return False
    for p in published:
        p_words = set(p.split("-")) - STOP
        if not p_words:
            continue
        overlap = len(words & p_words) / max(len(words), len(p_words))
        if overlap >= 0.70:   # 70%+ same keywords = duplicate story
            return True
    return False

def pick_needed_category(posts_index, run_used_cats):
    """Pick which category needs an article most, based on current imbalance vs targets."""
    from collections import Counter
    existing_counts = Counter(p.get("category","World") for p in posts_index)
    total = max(sum(existing_counts.values()), 1)
    # Calculate how far each category is from its target ratio
    scores = {}
    for cat, target in CATEGORY_TARGETS.items():
        target_ratio = target / 10.0
        actual_ratio = existing_counts.get(cat, 0) / total
        # Penalize categories already used this run
        run_penalty = 0.5 * run_used_cats.get(cat, 0)
        scores[cat] = target_ratio - actual_ratio - run_penalty
    return max(scores, key=scores.get)

def build_topics(count, published, posts_index=None):
    """Build topic list with category balance enforcement.

    - Scheduled (auto) runs: use pick_needed_category (ratio-based balancing)
    - Manual runs: use get_next_rotation_categories (round-robin rotation)
      so every single manual trigger cycles through all 13 categories in order.
    """
    from collections import defaultdict, Counter
    if posts_index is None:
        posts_index = []

    # Detect if this is a manual/forced rotation run
    IS_MANUAL = os.environ.get("MANUAL_ROTATION", "false").lower() == "true"

    news = fetch_news(count * 3)

    # Group news topics by likely category (robust keyword match)
    CAT_KEYWORDS = {
        "Politics":      ["trump","congress","senate","republican","democrat","election","vote","law","bill","white house","president","governor","policy","legislation","government","minister","parliament","political","administration","federal","supreme court","doj","fbi","cia","pentagon","white house","comey","biden","harris","maga"],
        "World":         ["iran","china","russia","ukraine","europe","africa","india","pakistan","israel","war","ceasefire","nato","united nations","global","international","foreign","diplomatic","embassy","sanctions","middle east","asia","latin america","pope","vatican","eu ","g7","g20"],
        "Sports":        ["nba","nfl","mlb","nhl","soccer","football","basketball","baseball","playoffs","draft picks","head coach","quarterback","touchdown","championship","super bowl","world cup","olympic","athlete","stadium","league","tournament","match","fixture","transfer","roster"],
        "Entertainment": ["movie","film","actor","actress","singer","album","tv show","tv series","celebrity","oscar","grammy","netflix","hulu","disney","concert","music video","box office","hollywood","broadway","streaming","season 2","season 3","episode","finale","premiere","colbert","kimmel","fallon","reality tv","showrunner","decker","recap","cast"],
        "Technology":    ["ai","artificial intelligence","tech","software","apple","google","microsoft","startup","robot","chip","semiconductor","cyber","data","app","openai","spacex","elon musk","silicon valley","gadget","smartphone","computer","algorithm","cloud","quantum","programming","developer","digital"],
        "Finance":       ["economy","bank","gdp","inflation","interest rate","monetary","fiscal","hedge fund","private equity","bond","treasury","federal reserve","fed ","imf","world bank","debt","deficit","recession","economic","financial","credit","loan","mortgage","pension","investment fund"],
        "Business":      ["company","ceo","merger","acquisition","corporate","revenue","profit","layoff","worker","job cuts","industry","deal","startup","entrepreneur","brand","retail","supply chain","manufacturing","earnings report","quarterly","shareholders","board of directors","ipo ","valuation"],
        "Health":        ["cancer","vaccine","drug","hospital","mental health","disease","fda","medical","patient","virus","treatment","therapy","surgery","doctor","nurse","medicine","pharmaceutical","outbreak","epidemic","pandemic","obesity","diabetes","heart","lung","brain","clinical trial","cdc","who ","health care"],
        "Science":       ["climate","space","nasa","research","study","planet","ocean","fossil","physics","gene","species","earth","asteroid","comet","galaxy","universe","telescope","experiment","discovery","scientist","laboratory","biology","chemistry","geology","evolution","crispr","dna","rna"],
        "Travel":        ["travel","tourism","flight","hotel","destination","tourist","visa","airport","cruise","resort","vacation","holiday","airline","passport","booking","itinerary","backpacking","expedition","adventure travel"],
        "Crypto":        ["bitcoin","btc price","ethereum","eth price","crypto","cryptocurrency","blockchain","defi","nft","altcoin","binance","coinbase","solana","ripple","xrp","web3","dogecoin","stablecoin","crypto wallet","mining","token","decentralized","satoshi","crypto bull","halving","crypto market"],
        "Forex":         ["forex","currency","dollar index","euro","british pound","japanese yen","usd","eur","gbp","jpy","exchange rate","fx market","rupee","pkr","inr","currency pair","pip","spread","central bank","dxy","currency war","devaluation"],
        "Stocks":        ["stock market","stock price","shares","equity","s&p 500","nasdaq","dow jones","wall street","earnings report","ipo ","dividend","nyse","bull market","bear market","market cap","index fund","etf ","short sell","options trading","analyst rating","upgrade","downgrade","target price"],
    }

    def guess_category(title):
        import re as _re
        tl = title.lower()
        def kw_match(kw, text):
            # Short keywords (<=3 chars) — whole word match
            if len(kw) <= 3:
                return bool(_re.search(r"\b" + _re.escape(kw) + r"\b", text))
            return kw in text
        scores = {cat: sum(1 for kw in kws if kw_match(kw, tl)) for cat, kws in CAT_KEYWORDS.items()}
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return "World"
        return best

    # Bucket news by category
    news_by_cat = defaultdict(list)
    for t in news:
        cat = guess_category(t["title"])
        slug = slugify(t["title"])
        if not is_duplicate(slug, published):
            news_by_cat[cat].append(t)

    # Build wiki pool by category
    wiki_by_cat = {}
    for cat, topics in WIKI_TOPICS_BALANCED.items():
        random.shuffle(topics)
        wiki_by_cat[cat] = [{"title": t, "hint": ""} for t in topics
                            if not is_duplicate(slugify(t), published)]

    # Select topics with category balance
    selected = []
    run_used_cats = Counter()
    attempts = 0

    # For manual runs: get a pre-set rotation list of categories
    # For auto runs: pick_needed_category dynamically as before
    if IS_MANUAL:
        rotation_cats = get_next_rotation_categories(count)
        rotation_queue = list(rotation_cats)  # consume in order
        print(f"  Manual rotation mode: {rotation_queue}")
    else:
        rotation_queue = None

    while len(selected) < count and attempts < count * 5:
        attempts += 1

        if rotation_queue:
            # Manual mode: take next category from rotation queue
            cat = rotation_queue.pop(0) if rotation_queue else pick_needed_category(posts_index, run_used_cats)
        else:
            # Auto mode: ratio-based balancing
            cat = pick_needed_category(posts_index, run_used_cats)

        # Try news first, then wiki
        topic = None
        if news_by_cat.get(cat):
            topic = news_by_cat[cat].pop(0)
        elif wiki_by_cat.get(cat):
            topic = wiki_by_cat[cat].pop(0)
        else:
            # fallback: any available news
            for c in random.sample(list(CAT_KEYWORDS.keys()), len(CAT_KEYWORDS)):
                if news_by_cat.get(c):
                    topic = news_by_cat[c].pop(0)
                    cat = c
                    break
            if not topic:
                break

        slug = slugify(topic["title"])
        # Final duplicate check including already selected this run
        selected_slugs = {slugify(s["title"]) for s in selected}
        if not is_duplicate(slug, published | selected_slugs):
            topic["_target_category"] = cat
            selected.append(topic)
            run_used_cats[cat] += 1

    print(f"  Category distribution this run: {dict(run_used_cats)}")
    return selected

# ── WRITE ARTICLE ────────────────────────────────────────────────────
def write_article(topic, hint, related_posts=None, target_category=None):
    now = datetime.now()

    cat_hint = (f"IMPORTANT: This article MUST be categorized as '{target_category}'. "
                if target_category else "")

    # Keyword SEO instructions
    kw_hint = ""
    if CUSTOM_KEYWORDS and topic in CUSTOM_KEYWORDS:
        kw_hint = (
            f"CRITICAL SEO INSTRUCTIONS:\n"
            f"1. EXACT keyword '{topic}' MUST appear in the title\n"
            f"2. EXACT keyword '{topic}' MUST appear in meta description\n"
            f"3. EXACT keyword '{topic}' MUST appear in first paragraph\n"
            f"4. EXACT keyword '{topic}' MUST appear 3-5 times in article\n"
            f"5. Use keyword in at least one H2 heading\n"
        )

    prompt = (
        f"Write a professional news article dated {now.strftime('%B %d, %Y')} about: {topic}\n"
        f"Background: {hint}\n"
        f"{cat_hint}"
        f"{kw_hint}"
        "Respond with ONLY this XML format — no extra text:\n"
        "<article>\n"
        "<title>Compelling headline 55-70 chars</title>\n"
        "<slug>url-slug-from-title</slug>\n"
        "<meta_description>SEO description 150-158 chars</meta_description>\n"
        "<focus_keyword>primary keyword phrase</focus_keyword>\n"
        "<category>Business or Technology or Finance or World or Sports or Health or Travel or Science or Entertainment or Politics or Crypto or Forex or Stocks</category>\n"
        "<image_keyword>specific 3-4 word Unsplash search term</image_keyword>\n"
        "<read_time>X min read</read_time>\n"
        "<excerpt>2-3 compelling sentences</excerpt>\n"
        "<tags>tag1,tag2,tag3,tag4</tags>\n"
        "<content>\n"
        "Write minimum 900 words. Use h2, h3, p, ul, li, strong, blockquote, a tags only. "
        "No hr tags. No dashes (-- or —). Do NOT mention any news outlet by name. "
        "Write complete professional article with proper paragraphs. "
        "Any external links MUST have rel=\"noopener noreferrer\" and target=\"_blank\" attributes. "
        "Stay strictly on topic — do NOT reference unrelated current events or other news stories.\n"
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
<nav class="navbar"><div class="navbar-wrap">
  <button class="navbar-arrow left" id="navLeft" onclick="scrollNav(-200)" aria-label="Scroll left">&#8249;</button>
  <div class="navbar-inner" id="navInner">
  <a href="{prefix}">Home</a>
  <a href="{prefix}category-business.html">Business</a>
  <a href="{prefix}category-technology.html">Technology</a>
  <a href="{prefix}category-finance.html">Finance</a>
  <a href="{prefix}category-world.html">World</a>
  <a href="{prefix}category-politics.html">Politics</a>
  <a href="{prefix}category-sports.html">Sports</a>
  <a href="{prefix}category-health.html">Health</a>
  <a href="{prefix}category-science.html">Science</a>
  <a href="{prefix}category-travel.html">Travel</a>
  <a href="{prefix}category-entertainment.html">Entertainment</a>
  <a href="{prefix}networth/index.html">Net Worth</a>
  <a href="{prefix}markets.html">Markets</a>
  <a href="{prefix}category-crypto.html">Crypto</a>
  <a href="{prefix}category-forex.html">Forex</a>
  <a href="{prefix}category-stocks.html">Stocks</a>
  </div>
  <button class="navbar-arrow right" id="navRight" onclick="scrollNav(200)" aria-label="Scroll right">&#8250;</button>
</div></nav>
<script>
(function(){{
  var nav=document.getElementById('navInner');
  var btnL=document.getElementById('navLeft');
  var btnR=document.getElementById('navRight');
  if(!nav)return;
  function upd(){{
    if(nav.scrollLeft>10)btnL.classList.add('visible');else btnL.classList.remove('visible');
    if(nav.scrollLeft<nav.scrollWidth-nav.clientWidth-10)btnR.classList.add('visible');else btnR.classList.remove('visible');
  }}
  nav.addEventListener('scroll',upd);
  window.addEventListener('resize',upd);
  upd();
  window.scrollNav=function(d){{nav.scrollBy({{left:d,behavior:'smooth'}});}};
}})();
</script>"""

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
  <div class="footer-col"><h4>Markets</h4>
    <a href="{prefix}markets.html">Live Markets</a>
    <a href="{prefix}category-crypto.html">Crypto</a>
    <a href="{prefix}category-forex.html">Forex</a>
    <a href="{prefix}category-stocks.html">Stocks</a></div>
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
  <div class="footer-col"><h4>Company</h4>
    <a href="{prefix}about.html">About Us</a>
    <a href="{prefix}contact.html">Contact</a>
    <a href="{prefix}privacy-policy.html">Privacy Policy</a></div>
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
<meta name="google-site-verification" content="GHgnc6jifq43ccFgYjjD8spGle2qoCw5MW_e_cNahoY">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{SITE_URL}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{prefix}style.css?v={datetime.now().strftime('%Y%m%d')}">
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap"></noscript>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-YC4REN62D0"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-YC4REN62D0');
</script>
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

# ── INTERNAL LINK INJECTION ──────────────────────────────────────────
def inject_internal_links(article_html, current_slug, all_posts):
    """
    Inject internal links into article body WITHOUT changing any sentences.
    Finds keyword phrases from SAME CATEGORY posts inside existing text.
    - Same category ONLY — no cross-category links (no Finance links in Entertainment)
    - Max 2 links per article
    - Never links same post twice
    - Never links to itself
    - Content/sentences never modified — only existing words wrapped
    """
    from bs4 import BeautifulSoup

    MAX_LINKS = 2
    STOP = {"a","an","the","in","on","at","of","and","for","to","is","are","was",
            "were","it","its","as","by","with","from","that","this","has","have",
            "after","over","into","about","up","out","than","but","be","been",
            "their","his","her","our","us","new","says","will","can","could",
            "would","should","may","might","also","just","more","most","one",
            "two","or","not","all","who","which","what","when","where","how","said"}

    soup = BeautifulSoup(article_html, 'html.parser')
    body_text = soup.get_text().lower()

    # Get current post category
    current_cat = next((p.get("category","") for p in all_posts if p["slug"] == current_slug), "")

    # STRICT: same category ONLY — no cross-category linking
    if not current_cat:
        return str(soup)

    candidates = [p for p in all_posts
                  if p["slug"] != current_slug
                  and p.get("category","") == current_cat]

    # Pre-screen: only keep posts whose title has at least one phrase in body
    viable = []
    for post in candidates:
        title_words = [w for w in re.sub(r'[^a-zA-Z0-9 ]', '', post["title"]).split()
                      if w.lower() not in STOP and len(w) > 4]
        best_phrase = None
        for i in range(len(title_words) - 1):
            phrase = title_words[i] + " " + title_words[i+1]
            if phrase.lower() in body_text:
                best_phrase = phrase
                break
        if best_phrase:
            viable.append((post, best_phrase))
        if len(viable) >= MAX_LINKS * 2:
            break

    injected = 0
    used_slugs = set()

    for post, phrase in viable:
        if injected >= MAX_LINKS:
            break
        if post["slug"] in used_slugs:
            continue

        link_url = f"{SITE_URL}/posts/{post['slug']}.html"

        for tag in soup.find_all(['p', 'h2', 'h3']):
            # Skip tags that already have a link
            if tag.find('a'):
                continue
            tag_text = tag.get_text()
            if re.search(re.escape(phrase), tag_text, re.IGNORECASE):
                tag_html = str(tag)
                new_html = re.sub(
                    re.escape(phrase),
                    f'<a href="{link_url}" title="{esc(post["title"])}">{phrase}</a>',
                    tag_html, count=1, flags=re.IGNORECASE
                )
                if new_html != tag_html:
                    tag.replace_with(BeautifulSoup(new_html, 'html.parser'))
                    injected += 1
                    used_slugs.add(post["slug"])
                    break

    return str(soup)

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
    
    tags_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in data.get("tags", []))
    
    # Sidebar trending
    sidebar_items = "".join(
        f'''<a href="{SITE_URL}/posts/{p["slug"]}.html" class="sw-item">
          <div class="sw-item-img"><img src="{get_thumbnail_url(p["image_url"])}" alt="{esc(p["title"])}" loading="lazy"></div>
          <div><h4>{esc(p["title"][:80])}{"..." if len(p["title"])>80 else ""}</h4>
          <div class="sw-item-date">{p.get("date_human","")}</div></div></a>'''
        for p in [x for x in all_posts if x["slug"] != slug and x.get("image_url") and x["slug"] != "index"][:6]
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
    
    # Inject internal links — before f-string
    linked_html = inject_internal_links(data["article_html"], slug, all_posts)

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
  <div class="post-hero"><img src="{data["image_url"]}" alt="{esc(data["title"])}" loading="eager" fetchpriority="high"></div>
  <div class="post-body">{linked_html}</div>
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

# ── BUILD MARKETS TICKER (homepage strip) ────────────────────────────
def build_markets_ticker():
    return """<div class="markets-strip">
  <div class="markets-strip-inner container">
    <a href="markets.html" class="markets-strip-label">📈 LIVE</a>
    <div class="mk-scroll-track" id="mkTrack">
      <div class="mk-ticker-inner" id="mkInner">
      <span class="mk-tick" id="tk-btc">BTC/USD <span>—</span></span>
      <span class="mk-tick" id="tk-eth">ETH/USD <span>—</span></span>
      <span class="mk-tick" id="tk-sol">SOL <span>—</span></span>
      <span class="mk-tick" id="tk-xrp">XRP <span>—</span></span>
      <span class="mk-tick mk-sep-v">|</span>
      <span class="mk-tick" id="tk-eurusd">EUR/USD <span>—</span></span>
      <span class="mk-tick" id="tk-gbpusd">GBP/USD <span>—</span></span>
      <span class="mk-tick" id="tk-usdjpy">USD/JPY <span>—</span></span>

      <span class="mk-tick mk-sep-v">|</span>
      <span class="mk-tick" id="tk-fg">Fear &amp; Greed: <span>—</span></span>
      <span class="mk-tick mk-sep-v">|</span>
      <span class="mk-tick mk-lnk"><a href="markets.html">Full Markets ›</a></span>
      <span class="mk-tick mk-lnk"><a href="category-crypto.html">Crypto</a></span>
      <span class="mk-tick mk-lnk"><a href="category-forex.html">Forex</a></span>
      <span class="mk-tick mk-lnk"><a href="category-stocks.html">Stocks</a></span>
      <span class="mk-tick mk-sep-v">&nbsp;&nbsp;&nbsp;</span>
      <!-- Duplicate for seamless loop -->
      <span class="mk-tick">BTC/USD <span id="tk-btc2">—</span></span>
      <span class="mk-tick">ETH/USD <span id="tk-eth2">—</span></span>
      <span class="mk-tick">SOL <span id="tk-sol2">—</span></span>
      <span class="mk-tick">XRP <span id="tk-xrp2">—</span></span>
      <span class="mk-tick mk-sep-v">|</span>
      <span class="mk-tick">EUR/USD <span id="tk-eurusd2">—</span></span>
      <span class="mk-tick">GBP/USD <span id="tk-gbpusd2">—</span></span>
      <span class="mk-tick">USD/JPY <span id="tk-usdjpy2">—</span></span>

      <span class="mk-tick mk-sep-v">|</span>
      <span class="mk-tick">Fear &amp; Greed: <span id="tk-fg2">—</span></span>
      <span class="mk-tick mk-sep-v">|</span>
      <span class="mk-tick mk-lnk"><a href="markets.html">Full Markets ›</a></span>
      <span class="mk-tick mk-lnk"><a href="category-crypto.html">Crypto</a></span>
      <span class="mk-tick mk-lnk"><a href="category-forex.html">Forex</a></span>
      <span class="mk-tick mk-lnk"><a href="category-stocks.html">Stocks</a></span>
      </div>
    </div>
  </div>
</div>
<script>
(function(){
  function pc(v,d){return '$'+Number(v).toLocaleString('en-US',{maximumFractionDigits:d||2});}
  function ch(c){var u=c>=0;return '<em class="'+(u?'up':'dn')+'">'+(u?'▲':'▼')+Math.abs(c).toFixed(2)+'%</em>';}
  function set(id,t,c){var e=document.getElementById(id);if(!e)return;var s=e.querySelector('span');if(s){s.innerHTML=t+(c!==undefined?ch(c):'');}}
  function setTick(id,html){
    var e=document.getElementById(id);if(e){var sp=e.querySelector('span');if(sp)sp.innerHTML=html;}
    var e2=document.getElementById(id+'2');if(e2){var sp2=e2.querySelector ? e2 : e2;if(e2)e2.innerHTML=html;}
  }
  async function tick(){
    try{
      var r=await fetch('https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,ETH,SOL,XRP&tsyms=USD');
      var d=(await r.json()).RAW;
      if(!d)throw new Error();
      var map={BTC:'tk-btc',ETH:'tk-eth',SOL:'tk-sol',XRP:'tk-xrp'};
      for(var sym in map){
        if(!d[sym]||!d[sym].USD)continue;
        var price=d[sym].USD.PRICE;
        var chg=d[sym].USD.CHANGEPCT24HOUR;
        var u=chg>=0;
        var html='$'+price.toLocaleString('en-US',{maximumFractionDigits:price<1?4:2})+'<em class="'+(u?'up':'dn')+'">'+(u?'▲':'▼')+Math.abs(chg).toFixed(2)+'%</em>';
        var s=document.getElementById(map[sym]);if(s){var sp=s.querySelector('span');if(sp)sp.innerHTML=html;}
        var s2=document.getElementById(map[sym]+'2');if(s2)s2.innerHTML=html;
      }
    }catch(e){}

    try{
      var r=await fetch('https://open.er-api.com/v6/latest/USD');
      var f=await r.json();
      var fx=f.rates||{};
      if(fx.EUR){
        var pairs=[
          ['tk-eurusd',(1/fx.EUR).toFixed(4)],
          ['tk-gbpusd',(1/fx.GBP).toFixed(4)],
          ['tk-usdjpy',fx.JPY.toFixed(2)]
        ];
        pairs.forEach(function(p){
          var s=document.getElementById(p[0]);if(s){var sp=s.querySelector('span');if(sp)sp.textContent=p[1];}
          var s2=document.getElementById(p[0]+'2');if(s2)s2.textContent=p[1];
        });
      }
    }catch(e){}

    try{
      var r=await fetch('https://api.alternative.me/fng/');
      var g=await r.json();
      if(g.data){
        var val=g.data[0].value+' ('+g.data[0].value_classification+')';
        var s=document.getElementById('tk-fg');if(s){s.querySelector('span').textContent=val;}
        var s2=document.getElementById('tk-fg2');if(s2)s2.textContent=val;
      }
    }catch(e){}
  }
  tick();setInterval(tick,60000);
})();
</script>"""

# ── BUILD MARKETS PAGE (CNBC-style full data) ─────────────────────────
def build_markets_page():
    html = f"""{head_html(
        "Live Markets — Crypto, Forex, Stocks & Commodities | " + SITE_NAME,
        "Real-time cryptocurrency prices, forex rates, market indices, Fear & Greed Index. Bitcoin, Ethereum, EUR/USD, USD/PKR and 50+ markets.",
        SITE_URL + "/markets.html", "", "", "website")}
{nav_html("/")}
<div class="mkp-wrap" style="overflow-x:hidden">
<div class="mkp-hero">
  <div class="container">
    <div class="mkp-hero-top">
      <div>
        <h1 id="mkp-hdr-title">Crypto Markets</h1>
        <p class="mkp-sub">Live data &mdash; updates every 30s &mdash; <span id="mkp-time">Loading...</span></p>
      </div>
      <div class="mkp-tabs">
        <button class="mkp-tab active" onclick="showTab('crypto')">Crypto</button>
        <button class="mkp-tab" onclick="showTab('forex')">Forex</button>
        <button class="mkp-tab" onclick="showTab('indices')">Indices</button>
      </div>
    </div>

    <!-- CRYPTO OVERVIEW CARDS -->
    <div class="mkp-overview" id="ov-crypto">
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">Bitcoin (BTC)</div>
        <div class="mkp-ov-price" id="ov-btc-p">—</div>
        <div class="mkp-ov-chg" id="ov-btc-c">—</div>
      </div>
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">Ethereum (ETH)</div>
        <div class="mkp-ov-price" id="ov-eth-p">—</div>
        <div class="mkp-ov-chg" id="ov-eth-c">—</div>
      </div>
      <div class="mkp-ov-card mkp-ov-interactive">
        <select id="ov-coin-sel" onchange="updatePickedCoin()" class="mkp-coin-select">
          <option value="SOL">Solana (SOL)</option>
          <option value="BNB">BNB</option>
          <option value="XRP">XRP</option>
          <option value="ADA">Cardano</option>
          <option value="DOGE">Dogecoin</option>
          <option value="AVAX">Avalanche</option>
          <option value="DOT">Polkadot</option>
          <option value="MATIC">Polygon</option>
          <option value="LINK">Chainlink</option>
          <option value="LTC">Litecoin</option>
          <option value="TRX">TRON</option>
          <option value="NEAR">NEAR</option>
        </select>
        <div class="mkp-ov-price" id="ov-picked-p">—</div>
        <div class="mkp-ov-chg" id="ov-picked-c">—</div>
      </div>
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">BTC Dominance</div>
        <div class="mkp-ov-price" id="ov-btc-dom2">—</div>
        <div class="mkp-ov-chg mkp-ov-sub">Of total market</div>
      </div>
      <div class="mkp-ov-card mkp-ov-fear" id="ov-fg-card">
        <div class="mkp-ov-label">Fear &amp; Greed</div>
        <div class="mkp-ov-price" id="ov-fg-val">—</div>
        <div class="mkp-ov-chg" id="ov-fg-label">—</div>
      </div>
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">Market Cap</div>
        <div class="mkp-ov-price" id="ov-mcap">—</div>
        <div class="mkp-ov-chg" id="ov-mcap-c">—</div>
      </div>
    </div>

    <!-- FOREX OVERVIEW CARDS -->
    <div class="mkp-overview" id="ov-forex" style="display:none">
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">EUR / USD</div>
        <div class="mkp-ov-price" id="ov-eur-p">—</div>
        <div class="mkp-ov-chg mkp-ov-sub">Euro</div>
      </div>
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">GBP / USD</div>
        <div class="mkp-ov-price" id="ov-gbp-p">—</div>
        <div class="mkp-ov-chg mkp-ov-sub">British Pound</div>
      </div>
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">USD / JPY</div>
        <div class="mkp-ov-price" id="ov-jpy-p">—</div>
        <div class="mkp-ov-chg mkp-ov-sub">Japanese Yen</div>
      </div>
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">USD / CHF</div>
        <div class="mkp-ov-price" id="ov-chf-p">—</div>
        <div class="mkp-ov-chg mkp-ov-sub">Swiss Franc</div>
      </div>

      <div class="mkp-ov-card">
        <div class="mkp-ov-label">USD Index (DXY)</div>
        <div class="mkp-ov-price" id="ov-dxy-p">—</div>
        <div class="mkp-ov-chg mkp-ov-sub">Est. from rates</div>
      </div>
    </div>

    <!-- INDICES OVERVIEW CARDS -->
    <div class="mkp-overview" id="ov-indices" style="display:none">
      <div class="mkp-ov-card mkp-ov-fear" id="ov-fg-card2">
        <div class="mkp-ov-label">Fear &amp; Greed</div>
        <div class="mkp-ov-price" id="ov-fg-val2">—</div>
        <div class="mkp-ov-chg" id="ov-fg-label2">—</div>
      </div>
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">BTC Dominance</div>
        <div class="mkp-ov-price" id="ov-btc-dom3">—</div>
        <div class="mkp-ov-chg mkp-ov-sub">Bitcoin market share</div>
      </div>
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">Total Market Cap</div>
        <div class="mkp-ov-price" id="ov-mcap2">—</div>
        <div class="mkp-ov-chg mkp-ov-sub">All crypto</div>
      </div>
      <div class="mkp-ov-card">
        <div class="mkp-ov-label">24h Volume</div>
        <div class="mkp-ov-price" id="ov-vol2">—</div>
        <div class="mkp-ov-chg mkp-ov-sub">Total crypto</div>
      </div>

      <div class="mkp-ov-card">
        <div class="mkp-ov-label">Active Cryptos</div>
        <div class="mkp-ov-price">20,000+</div>
        <div class="mkp-ov-chg mkp-ov-sub">Tracked globally</div>
      </div>
    </div>
  </div>
</div>

<div class="container mkp-body">
  <div class="mkp-main">

    <!-- CRYPTO TAB -->
    <div id="tab-crypto" class="mkp-tab-content active">
      <div class="mkp-section-hdr">
        <h2>🪙 Cryptocurrency Prices</h2>
        <span class="mkp-live-dot"></span><span class="mkp-live-txt">Live</span>
      </div>
      <div class="mkp-table-wrap">
        <table class="mkp-table" id="crypto-table">
          <thead>
            <tr><th>#</th><th>Name</th><th>Price</th><th>24h %</th><th>7d %</th><th>Market Cap</th><th>Volume 24h</th></tr>
          </thead>
          <tbody id="crypto-tbody">
            <tr><td colspan="7" class="mkp-loading">Loading crypto data...</td></tr>
          </tbody>
        </table>
      </div>
      <div class="mkp-section-hdr" style="margin-top:40px">
        <h2>📊 Top Gainers &amp; Losers (24h)</h2>
      </div>
      <div class="mkp-gl-grid">
        <div>
          <div class="mkp-gl-title up">🚀 Top Gainers</div>
          <div id="gainers-list"></div>
        </div>
        <div>
          <div class="mkp-gl-title dn">📉 Top Losers</div>
          <div id="losers-list"></div>
        </div>
      </div>
    </div>

    <!-- FOREX TAB -->
    <div id="tab-forex" class="mkp-tab-content">
      <div class="mkp-section-hdr">
        <h2>💱 Forex Exchange Rates</h2>
        <span class="mkp-live-dot"></span><span class="mkp-live-txt">Live</span>
      </div>
      <div class="mkp-fx-grid">
        <div class="mkp-table-wrap">
          <table class="mkp-table">
            <thead><tr><th>Pair</th><th>Rate</th><th>Inverse</th><th>Currency</th></tr></thead>
            <tbody id="forex-major"></tbody>
          </table>
        </div>
        <div class="mkp-table-wrap">
          <table class="mkp-table">
            <thead><tr><th>Pair</th><th>Rate</th><th>Inverse</th><th>Currency</th></tr></thead>
            <tbody id="forex-emerging"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- INDICES TAB -->
    <div id="tab-indices" class="mkp-tab-content">
      <div class="mkp-section-hdr">
        <h2>📊 Market Sentiment &amp; Global Indices</h2>
      </div>

      <!-- Fear & Greed — big featured card -->
      <div class="mkp-fg-featured">
        <div class="mkp-fg-featured-left">
          <div class="mkp-fg-featured-title">Crypto Fear &amp; Greed Index</div>
          <div class="mkp-fg-num" id="idx-fg-num">—</div>
          <div class="mkp-fg-class" id="idx-fg-class">—</div>
          <div class="mkp-fg-bar-wrap" style="margin:12px 0 6px"><div class="mkp-fg-bar" id="idx-fg-bar"></div></div>
          <div class="mkp-fg-labels"><span>Extreme Fear</span><span>Fear</span><span>Neutral</span><span>Greed</span><span>Extreme Greed</span></div>
          <div class="mkp-fg-history">
            <span>Yesterday: <strong id="idx-fg-yest">—</strong></span>
            <span>Last Week: <strong id="idx-fg-week">—</strong></span>
          </div>
        </div>
        <div class="mkp-fg-featured-right">
          <div class="mkp-fg-mini-card">
            <div class="mkp-fg-mini-label">BTC Dominance</div>
            <div class="mkp-fg-mini-val" id="idx-btc-dom">—</div>
          </div>
          <div class="mkp-fg-mini-card">
            <div class="mkp-fg-mini-label">Market Cap</div>
            <div class="mkp-fg-mini-val" id="idx-total-mcap">—</div>
          </div>
          <div class="mkp-fg-mini-card">
            <div class="mkp-fg-mini-label">24h Volume</div>
            <div class="mkp-fg-mini-val" id="idx-volume">—</div>
          </div>

          <div class="mkp-fg-mini-card">
            <div class="mkp-fg-mini-label">Active Cryptos</div>
            <div class="mkp-fg-mini-val" id="idx-active">20,000+</div>
          </div>
          <div class="mkp-fg-mini-card">
            <div class="mkp-fg-mini-label">USD Index (DXY)</div>
            <div class="mkp-fg-mini-val">~<span id="idx-dxy">—</span></div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- SIDEBAR -->
  <aside class="mkp-sidebar">
    <div class="mkp-sw">
      <div class="mkp-sw-title">🔥 Trending Crypto</div>
      <div id="trending-list"></div>
    </div>
    <div class="mkp-sw">
      <div class="mkp-sw-title">📰 Markets News</div>
      <a href="category-crypto.html" class="mkp-sw-link">Latest Crypto News →</a>
      <a href="category-forex.html" class="mkp-sw-link">Latest Forex News →</a>
      <a href="category-stocks.html" class="mkp-sw-link">Latest Stocks News →</a>
      <a href="category-finance.html" class="mkp-sw-link">Finance Analysis →</a>
    </div>
    <div class="mkp-sw">
      <div class="mkp-sw-title">💡 Quick Converter</div>
      <div class="mkp-conv">
        <input type="number" id="conv-amt" value="1" class="mkp-conv-input" oninput="convert()">
        <select id="conv-from" class="mkp-conv-sel" onchange="convert()">
          <option value="usd">USD</option><option value="eur">EUR</option>
          <option value="gbp">GBP</option><option value="pkr">PKR</option>
          <option value="inr">INR</option><option value="jpy">JPY</option>
        </select>
        <div class="mkp-conv-arrow">→</div>
        <select id="conv-to" class="mkp-conv-sel" onchange="convert()">
          <option value="pkr">PKR</option><option value="usd">USD</option>
          <option value="eur">EUR</option><option value="gbp">GBP</option>
          <option value="inr">INR</option><option value="jpy">JPY</option>
        </select>
        <div class="mkp-conv-result" id="conv-result">—</div>
      </div>
    </div>
  </aside>
</div>
</div>
<p class="mkp-disclaimer container">Data sourced from CryptoCompare &amp; ExchangeRate-API. Prices are indicative and may be delayed. Not financial advice.</p>

<script>
(function(){{
  var fxRates={{}}, cryptoData={{}}, globalData={{}};

  /* ── UTILS ── */
  function fmt(v,d){{
    if(v===undefined||v===null)return'—';
    d=d||2;
    if(v>=1e12)return'$'+(v/1e12).toFixed(2)+'T';
    if(v>=1e9)return'$'+(v/1e9).toFixed(2)+'B';
    if(v>=1e6)return'$'+(v/1e6).toFixed(2)+'M';
    return'$'+Number(v).toLocaleString('en-US',{{minimumFractionDigits:d,maximumFractionDigits:d}});
  }}
  function fmtFx(v,d){{return Number(v).toFixed(d||4);}}
  function badge(c){{
    if(c===undefined||c===null)return'—';
    var u=c>=0;
    return'<span class="mkp-badge '+(u?'up':'dn')+'">'+(u?'▲':'▼')+Math.abs(c).toFixed(2)+'%</span>';
  }}
  function set(id,html){{var e=document.getElementById(id);if(e)e.innerHTML=html;}}
  function setText(id,t){{var e=document.getElementById(id);if(e)e.textContent=t;}}

  /* ── TABS ── */
  var TAB_TITLES={{'crypto':'Crypto Markets','forex':'Forex Exchange Rates','indices':'Market Indices & Sentiment'}};
  window.showTab=function(t){{
    document.querySelectorAll('.mkp-tab-content').forEach(function(e){{e.classList.remove('active');}});
    document.querySelectorAll('.mkp-tab').forEach(function(e){{e.classList.remove('active');}});
    document.getElementById('tab-'+t).classList.add('active');
    event.target.classList.add('active');
    // Switch header title
    var hdr=document.getElementById('mkp-hdr-title');
    if(hdr)hdr.textContent=TAB_TITLES[t]||'Global Markets';
    // Switch overview cards
    ['crypto','forex','indices'].forEach(function(s){{
      var el=document.getElementById('ov-'+s);
      if(el)el.style.display=(s===t?'grid':'none');
    }});
  }};

  /* ── CRYPTO — CryptoCompare API (CORS friendly, works everywhere) ── */
  var COINS = [
    {{sym:'BTC',name:'Bitcoin'}},{{sym:'ETH',name:'Ethereum'}},
    {{sym:'BNB',name:'BNB'}},{{sym:'SOL',name:'Solana'}},
    {{sym:'XRP',name:'XRP'}},{{sym:'ADA',name:'Cardano'}},
    {{sym:'DOGE',name:'Dogecoin'}},{{sym:'AVAX',name:'Avalanche'}},
    {{sym:'DOT',name:'Polkadot'}},{{sym:'MATIC',name:'Polygon'}},
    {{sym:'LINK',name:'Chainlink'}},{{sym:'UNI',name:'Uniswap'}},
    {{sym:'LTC',name:'Litecoin'}},{{sym:'ATOM',name:'Cosmos'}},
    {{sym:'ETC',name:'Ethereum Classic'}},{{sym:'XLM',name:'Stellar'}},
    {{sym:'TRX',name:'TRON'}},{{sym:'NEAR',name:'NEAR Protocol'}},
    {{sym:'ALGO',name:'Algorand'}},{{sym:'FTM',name:'Fantom'}},
  ];
  var cryptoPrices = {{}};

  async function fetchCrypto(){{
    try{{
      // Fetch in 2 batches to avoid rate limits
      var batch1=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','AVAX','DOT','MATIC'];
      var batch2=['LINK','UNI','LTC','ATOM','ETC','XLM','TRX','NEAR','ALGO','FTM'];

      var r1=await fetch('https://min-api.cryptocompare.com/data/pricemultifull?fsyms='+batch1.join(',')+'&tsyms=USD');
      var res1=await r1.json();
      var raw1=res1.RAW||{{}};

      var r2=await fetch('https://min-api.cryptocompare.com/data/pricemultifull?fsyms='+batch2.join(',')+'&tsyms=USD');
      var res2=await r2.json();
      var raw2=res2.RAW||{{}};

      var raw=Object.assign({{}},raw1,raw2);
      if(!Object.keys(raw).length)throw new Error('no data');

      var tbody='';
      var coins_data=[];
      COINS.forEach(function(c,i){{
        var d=raw[c.sym]&&raw[c.sym].USD;
        if(!d)return;
        var price=d.PRICE||0;
        var chg=d.CHANGEPCT24HOUR||0;
        var vol=d.TOTALVOLUME24HTO||0;
        var mcap=d.MKTCAP||0;
        cryptoPrices[c.sym]={{price:price,chg:chg}};
        coins_data.push({{name:c.name,short:c.sym,price:price,chg:chg,vol:vol,mcap:mcap}});
        tbody+='<tr>'
          +'<td class="mkp-rank">'+(i+1)+'</td>'
          +'<td class="mkp-name"><strong>'+c.name+'</strong> <span class="mkp-sym">'+c.sym+'</span></td>'
          +'<td class="mkp-price">'+fmt(price,price<1?4:2)+'</td>'
          +'<td>'+badge(chg)+'</td>'
          +'<td>—</td>'
          +'<td class="mkp-mcap">'+fmt(mcap)+'</td>'
          +'<td class="mkp-vol">'+fmt(vol)+'</td>'
          +'</tr>';
      }});
      set('crypto-tbody',tbody||'<tr><td colspan="7" style="text-align:center;padding:20px;color:#999">Loading...</td></tr>');

      // Coin switcher
      window.updatePickedCoin=function(){{
        var sym=document.getElementById('ov-coin-sel').value;
        var d=cryptoPrices[sym];
        if(!d)return;
        document.getElementById('ov-picked-p').textContent=fmt(d.price,d.price<1?4:2);
        document.getElementById('ov-picked-c').innerHTML=badge(d.chg);
      }};
      updatePickedCoin();

      // Overview cards
      var btc=cryptoPrices['BTC'],eth=cryptoPrices['ETH'];
      if(btc){{set('ov-btc-p',fmt(btc.price));set('ov-btc-c',badge(btc.chg));}}
      if(eth){{set('ov-eth-p',fmt(eth.price));set('ov-eth-c',badge(eth.chg));}}

      // Global stats
      var totalMcap=coins_data.reduce(function(s,c){{return s+(c.mcap||0);}},0)*1.3;
      var totalVol=coins_data.reduce(function(s,c){{return s+(c.vol||0);}},0);
      var btcMcap=btc?btc.price*19800000:0;
      var btcDom=totalMcap?(btcMcap/totalMcap*100).toFixed(1)+'%':'—';
      set('ov-mcap',fmt(totalMcap));set('ov-mcap2',fmt(totalMcap));
      set('ov-vol',fmt(totalVol));set('ov-vol2',fmt(totalVol));
      set('ov-btc-dom2',btcDom);set('ov-btc-dom3',btcDom);
      set('idx-total-mcap',fmt(totalMcap));set('idx-btc-dom',btcDom);set('idx-volume',fmt(totalVol));
      setText('idx-active','20,000+');

      // Gainers & Losers
      var sorted=[...coins_data].sort(function(a,b){{return b.chg-a.chg;}});
      var gHtml='',lHtml='';
      sorted.slice(0,5).forEach(function(c){{
        gHtml+='<div class="mkp-gl-item"><span>'+c.short+' <small>'+c.name+'</small></span>'+badge(c.chg)+'</div>';
      }});
      sorted.slice(-5).reverse().forEach(function(c){{
        lHtml+='<div class="mkp-gl-item"><span>'+c.short+' <small>'+c.name+'</small></span>'+badge(c.chg)+'</div>';
      }});
      set('gainers-list',gHtml);set('losers-list',lHtml);

      // Trending
      var trending=[...coins_data].sort(function(a,b){{return Math.abs(b.chg)-Math.abs(a.chg);}}).slice(0,7);
      var tHtml='';
      trending.forEach(function(c,i){{
        tHtml+='<div class="mkp-trend-item"><span class="mkp-trend-rank">'+(i+1)+'</span><span>'+c.name+' <small>'+c.short+'</small></span><span class="mkp-trend-score">'+(c.chg>=0?'🔥':'❄️')+'</span></div>';
      }});
      set('trending-list',tHtml);

    }}catch(e){{set('crypto-tbody','<tr><td colspan="7" style="text-align:center;padding:20px;color:#999">Refreshing data...</td></tr>');}}
  }}

  async function fetchGlobal(){{}}

  /* ── FOREX ── */
  async function fetchForex(){{
    try{{
      var r=await fetch('https://open.er-api.com/v6/latest/USD');
      var f=await r.json();
      fxRates=f.rates||{{}};

      // Overview — Forex cards
      if(fxRates.EUR){{
        set('ov-eur-p',(1/fxRates.EUR).toFixed(4));
        set('ov-gbp-p',(1/fxRates.GBP).toFixed(4));
        set('ov-jpy-p',fxRates.JPY.toFixed(2));
        set('ov-chf-p',fxRates.CHF.toFixed(4));
        // DXY estimate (weighted basket)
        var dxy=(100/(0.576*(1/fxRates.EUR)+0.136*(1/fxRates.JPY/100)+0.119*(1/fxRates.GBP)+0.091*fxRates.CAD+0.042*fxRates.SEK+0.036*fxRates.CHF)).toFixed(2);
        set('ov-dxy-p','~'+dxy);
      }}

      // Major pairs
      var major=[
        ['EUR/USD',(1/fxRates.EUR).toFixed(4),(fxRates.EUR).toFixed(4),'Euro'],
        ['GBP/USD',(1/fxRates.GBP).toFixed(4),(fxRates.GBP).toFixed(4),'British Pound'],
        ['USD/JPY',fxRates.JPY.toFixed(2),(1/fxRates.JPY).toFixed(6),'Japanese Yen'],
        ['USD/CAD',fxRates.CAD.toFixed(4),(1/fxRates.CAD).toFixed(4),'Canadian Dollar'],
        ['AUD/USD',(1/fxRates.AUD).toFixed(4),(fxRates.AUD).toFixed(4),'Australian Dollar'],
        ['USD/CHF',fxRates.CHF.toFixed(4),(1/fxRates.CHF).toFixed(4),'Swiss Franc'],
        ['NZD/USD',(1/fxRates.NZD).toFixed(4),(fxRates.NZD).toFixed(4),'New Zealand Dollar'],
        ['USD/SGD',fxRates.SGD.toFixed(4),(1/fxRates.SGD).toFixed(4),'Singapore Dollar'],
      ];
      var emerging=[
        ['USD/PKR',fxRates.PKR.toFixed(2),(1/fxRates.PKR).toFixed(6),'Pakistani Rupee'],
        ['USD/INR',fxRates.INR.toFixed(2),(1/fxRates.INR).toFixed(6),'Indian Rupee'],
        ['USD/CNY',fxRates.CNY.toFixed(4),(1/fxRates.CNY).toFixed(4),'Chinese Yuan'],
        ['USD/AED',fxRates.AED.toFixed(4),(1/fxRates.AED).toFixed(4),'UAE Dirham'],
        ['USD/SAR',fxRates.SAR.toFixed(4),(1/fxRates.SAR).toFixed(4),'Saudi Riyal'],
        ['USD/TRY',fxRates.TRY.toFixed(2),(1/fxRates.TRY).toFixed(6),'Turkish Lira'],
        ['USD/BRL',fxRates.BRL.toFixed(4),(1/fxRates.BRL).toFixed(4),'Brazilian Real'],
        ['USD/MXN',fxRates.MXN.toFixed(4),(1/fxRates.MXN).toFixed(4),'Mexican Peso'],
      ];
      function fxRows(arr){{return arr.map(function(p){{return'<tr><td><strong>'+p[0]+'</strong></td><td class="mkp-price">'+p[1]+'</td><td class="mkp-muted">'+p[2]+'</td><td>'+p[3]+'</td></tr>';}}).join('');}}
      set('forex-major',fxRows(major));
      set('forex-emerging',fxRows(emerging));

      // Currency converter
      convert();
    }}catch(e){{}}
  }}

  /* ── FEAR & GREED ── */
  async function fetchFG(){{
    try{{
      var r=await fetch('https://api.alternative.me/fng/?limit=7');
      var g=await r.json();
      if(!g.data)return;
      var today=g.data[0], yest=g.data[1], week=g.data[6]||g.data[g.data.length-1];
      var val=parseInt(today.value);
      var cls=val<=25?'extreme-fear':val<=45?'fear':val<=55?'neutral':val<=75?'greed':'extreme-greed';
      var clr=val<=25?'#ef4444':val<=45?'#f97316':val<=55?'#eab308':val<=75?'#22c55e':'#16a34a';

      set('ov-fg-val',today.value);set('ov-fg-val2',today.value);
      set('ov-fg-label',today.value_classification);set('ov-fg-label2',today.value_classification);
      var card=document.getElementById('ov-fg-card');
      if(card)card.style.borderTop='3px solid '+clr;

      // Indices gauge
      set('idx-fg-num',today.value);
      set('idx-fg-class',today.value_classification);
      var bar=document.getElementById('idx-fg-bar');
      if(bar){{bar.style.width=today.value+'%';bar.style.background=clr;}}
      setText('idx-fg-yest',yest?yest.value+' ('+yest.value_classification+')':'—');
      setText('idx-fg-week',week?week.value+' ('+week.value_classification+')':'—');

      // Ticker
      var tk=document.getElementById('tk-fg');
      if(tk){{var s=tk.querySelector('span');if(s)s.textContent=today.value+' ('+today.value_classification+')';}}
    }}catch(e){{}}
  }}

  /* ── CONVERTER ── */
  window.convert=function(){{
    var amt=parseFloat(document.getElementById('conv-amt').value)||1;
    var from=document.getElementById('conv-from').value;
    var to=document.getElementById('conv-to').value;
    if(!fxRates.PKR){{set('conv-result','Loading...');return;}}
    var rates=Object.assign({{}},fxRates,{{usd:1}});
    var fromRate=from==='usd'?1:from==='eur'?(1/fxRates.EUR):from==='gbp'?(1/fxRates.GBP):from==='jpy'?(1/fxRates.JPY):(1/(fxRates[from.toUpperCase()]||1));
    var toRate=to==='usd'?1:fxRates[to.toUpperCase()]||1;
    if(to==='eur')toRate=1/fxRates.EUR;
    if(to==='gbp')toRate=1/fxRates.GBP;
    var result=amt*fromRate*toRate;
    var label=to.toUpperCase();
    set('conv-result','<strong>'+(result>=1?result.toFixed(2):result.toFixed(4))+' '+label+'</strong>');
  }};

  /* ── TIMESTAMP & INIT ── */
  function updateTime(){{
    var e=document.getElementById('mkp-time');
    if(e)e.textContent='Last updated: '+new Date().toLocaleTimeString();
  }}

  async function fetchAll(){{
    await Promise.allSettled([fetchCrypto(),fetchGlobal(),fetchForex(),fetchFG()]);
    updateTime();
  }}

  fetchAll();
  setInterval(fetchAll,30000);
}})();
</script>
{foot_html()}
</body></html>"""
    (OUTPUT_DIR / "markets.html").write_text(html)

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
    <div class="hero-main-img"><img src="{h["image_url"]}" alt="{esc(h["title"])}" loading="eager" fetchpriority="high"></div>
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
          <div class="sw-item-img"><img src="{get_thumbnail_url(p["image_url"])}" alt="{esc(p["title"])}" loading="lazy"></div>
          <div><h4>{esc(p["title"][:80])}{"..." if len(p["title"])>80 else ""}</h4>
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
{nav_html("/")}
{hero_html}
{build_markets_ticker()}
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
{nav_html("/")}
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
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             f'  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>']
    for cat in CATEGORIES:
        lines.append(f'  <url><loc>{SITE_URL}/category-{cat.lower()}.html</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>')
    # Static pages
    lines.append(f'  <url><loc>{SITE_URL}/markets.html</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>')
    lines.append(f'  <url><loc>{SITE_URL}/about.html</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.5</priority></url>')
    lines.append(f'  <url><loc>{SITE_URL}/contact.html</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.5</priority></url>')
    lines.append(f'  <url><loc>{SITE_URL}/privacy-policy.html</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.3</priority></url>')
    # Networth section
    lines.append(f'  <url><loc>{SITE_URL}/networth/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    nw_index = OUTPUT_DIR / "networth_index.json"
    if nw_index.exists():
        try:
            for profile in json.loads(nw_index.read_text()):
                nw_slug = profile.get("slug", "")
                if nw_slug and nw_slug not in seen_slugs:
                    seen_slugs.add(nw_slug)
                    lines.append(f'  <url><loc>{SITE_URL}/networth/{nw_slug}.html</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>')
        except Exception:
            pass
    seen_slugs.clear()
    # Posts — deduplicated, with lastmod + changefreq
    for p in posts:
        if p["slug"] in seen_slugs:
            print(f"  Sitemap: skipping duplicate slug {p['slug']}")
            continue
        seen_slugs.add(p["slug"])
        post_date = p["date_iso"][:10]
        lines.append(f'  <url><loc>{SITE_URL}/posts/{p["slug"]}.html</loc><lastmod>{post_date}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>')
    lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines))

# ── BUILD STATIC PAGES (About, Contact, Privacy) ──────────────────────
def build_static_pages():
    """Rebuild About, Contact, Privacy pages with latest nav/footer every run."""
    now = datetime.now()
    
    def static_head(title, desc, canonical):
        return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="favicon.ico" type="image/x-icon">
<link rel="apple-touch-icon" href="favicon.png">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{SITE_URL}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="style.css">
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap"></noscript>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-YC4REN62D0"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-YC4REN62D0');</script>
</head><body>"""

    about_body = """<div class="container" style="max-width:800px;margin:48px auto;padding:0 20px">
  <div class="label" style="margin-bottom:12px">About</div>
  <h1 style="font-size:clamp(28px,4vw,42px);font-weight:800;line-height:1.15;margin-bottom:20px">About Markets News Today</h1>
  <div style="width:60px;height:4px;background:var(--red);margin-bottom:32px"></div>
  <div style="font-size:17px;line-height:1.8;color:var(--dark)">
    <p style="margin-bottom:20px">Markets News Today is an independent digital news publication dedicated to delivering fast, accurate, and insightful reporting on the stories that shape the global economy and society.</p>
    <h2 style="font-size:22px;font-weight:700;margin:32px 0 14px">Our Mission</h2>
    <p style="margin-bottom:20px">Our mission is simple: to keep you informed. We focus on clarity, accuracy, and depth. Every article is written to give you the context you need to understand not just what happened — but why it matters.</p>
    <h2 style="font-size:22px;font-weight:700;margin:32px 0 14px">What We Cover</h2>
    <ul style="margin-bottom:20px;padding-left:24px;line-height:2">
      <li><strong>Business &amp; Finance</strong> — Markets, earnings, economic policy, and corporate strategy</li>
      <li><strong>Technology</strong> — AI, cybersecurity, startups, and the companies shaping our digital future</li>
      <li><strong>Crypto &amp; Forex</strong> — Live markets, analysis, and trading insights</li>
      <li><strong>World Affairs</strong> — International politics, diplomacy, and global events</li>
      <li><strong>Sports</strong> — Breaking news and results from major leagues worldwide</li>
      <li><strong>Health &amp; Science</strong> — Medical breakthroughs and research</li>
      <li><strong>Entertainment</strong> — Film, music, television, and popular culture</li>
    </ul>
    <h2 style="font-size:22px;font-weight:700;margin:32px 0 14px">Our Team</h2>
    <p style="margin-bottom:20px">Powered by experienced journalists and analysts from across the globe. Read more on our <a href="authors/" style="color:var(--red)">author profile pages</a>.</p>
    <h2 style="font-size:22px;font-weight:700;margin:32px 0 14px">Contact Us</h2>
    <p style="margin-bottom:20px">Have a tip or question? Visit our <a href="contact.html" style="color:var(--red)">Contact page</a>.</p>
    <div style="background:var(--gray);border-left:4px solid var(--red);padding:20px 24px;margin:32px 0;border-radius:4px">
      <p style="margin:0;font-size:15px;color:var(--muted)"><strong style="color:var(--dark)">Markets News Today</strong><br>
      Email: <a href="mailto:contact@marketsnewstoday.info" style="color:var(--red)">contact@marketsnewstoday.info</a></p>
    </div>
  </div>
</div>"""

    contact_body = """<div class="container" style="max-width:800px;margin:48px auto;padding:0 20px">
  <div class="label" style="margin-bottom:12px">Contact</div>
  <h1 style="font-size:clamp(28px,4vw,42px);font-weight:800;line-height:1.15;margin-bottom:20px">Contact Us</h1>
  <div style="width:60px;height:4px;background:var(--red);margin-bottom:32px"></div>
  <div style="font-size:17px;line-height:1.8;color:var(--dark)">
    <p style="margin-bottom:28px">We welcome tips, corrections, feedback, and press inquiries.</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin-bottom:36px">
      <div style="background:var(--gray);padding:24px;border-top:3px solid var(--red)">
        <h3 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">News Tips</h3>
        <a href="mailto:tips@marketsnewstoday.info" style="color:var(--red);font-weight:600;font-size:14px">tips@marketsnewstoday.info</a>
      </div>
      <div style="background:var(--gray);padding:24px;border-top:3px solid var(--red)">
        <h3 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">Corrections</h3>
        <a href="mailto:corrections@marketsnewstoday.info" style="color:var(--red);font-weight:600;font-size:14px">corrections@marketsnewstoday.info</a>
      </div>
      <div style="background:var(--gray);padding:24px;border-top:3px solid var(--red)">
        <h3 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">General</h3>
        <a href="mailto:contact@marketsnewstoday.info" style="color:var(--red);font-weight:600;font-size:14px">contact@marketsnewstoday.info</a>
      </div>
    </div>
    <div style="background:var(--gray);border-left:4px solid var(--red);padding:20px 24px;margin:32px 0;border-radius:4px">
      <p style="margin:0;font-size:15px">We aim to respond within 1-2 business days.</p>
    </div>
  </div>
</div>"""

    privacy_body = f"""<div class="container" style="max-width:800px;margin:48px auto;padding:0 20px">
  <div class="label" style="margin-bottom:12px">Legal</div>
  <h1 style="font-size:clamp(28px,4vw,42px);font-weight:800;line-height:1.15;margin-bottom:20px">Privacy Policy</h1>
  <div style="width:60px;height:4px;background:var(--red);margin-bottom:12px"></div>
  <p style="font-size:13px;color:var(--muted);margin-bottom:32px">Last updated: {now.strftime("%B %d, %Y")}</p>
  <div style="font-size:16px;line-height:1.85;color:var(--dark)">
    <p style="margin-bottom:20px">This Privacy Policy describes how Markets News Today collects, uses, and shares information when you visit <a href="{SITE_URL}" style="color:var(--red)">{SITE_URL}</a>.</p>
    <h2 style="font-size:20px;font-weight:700;margin:32px 0 12px">1. Information We Collect</h2>
    <ul style="padding-left:24px;margin-bottom:20px;line-height:2">
      <li>Browser type and version</li><li>Operating system</li><li>Pages visited and time on page</li>
      <li>Referring website</li><li>IP address (anonymized)</li><li>Device type</li>
    </ul>
    <h2 style="font-size:20px;font-weight:700;margin:32px 0 12px">2. Google Analytics</h2>
    <p style="margin-bottom:20px">We use Google Analytics to analyze usage. Data is anonymized and aggregated. Opt out via the <a href="https://tools.google.com/dlpage/gaoptout" style="color:var(--red)" target="_blank" rel="noopener">Google Analytics Opt-out Add-on</a>.</p>
    <h2 style="font-size:20px;font-weight:700;margin:32px 0 12px">3. Third-Party Services</h2>
    <ul style="padding-left:24px;margin-bottom:20px;line-height:2">
      <li><strong>Google Analytics</strong> — website analytics</li>
      <li><strong>Unsplash</strong> — stock photography</li>
      <li><strong>CryptoCompare</strong> — live crypto prices</li>
      <li><strong>ExchangeRate-API</strong> — live forex rates</li>
    </ul>
    <h2 style="font-size:20px;font-weight:700;margin:32px 0 12px">4. Contact</h2>
    <p style="margin-bottom:20px">Questions? Email <a href="mailto:contact@marketsnewstoday.info" style="color:var(--red)">contact@marketsnewstoday.info</a>.</p>
  </div>
</div>"""

    pages = [
        ("about.html", "About Us | " + SITE_NAME,
         "Markets News Today is your trusted source for breaking news and expert analysis on business, finance and world affairs.",
         SITE_URL + "/about.html", about_body),
        ("contact.html", "Contact Us | " + SITE_NAME,
         "Get in touch with the Markets News Today editorial team. Send us news tips, corrections, or feedback.",
         SITE_URL + "/contact.html", contact_body),
        ("privacy-policy.html", "Privacy Policy | " + SITE_NAME,
         "Learn how Markets News Today collects, uses, and protects your information.",
         SITE_URL + "/privacy-policy.html", privacy_body),
    ]
    for filename, title, desc, canonical, body in pages:
        html = static_head(title, desc, canonical) + nav_html("/") + body + foot_html("/") + "</body></html>"
        (OUTPUT_DIR / filename).write_text(html)
    print("Built static pages (about, contact, privacy)")


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

    # Keyword mode — agar custom keywords hain toh unhi pe articles banao
    if CUSTOM_KEYWORDS:
        print(f"Keyword mode: {len(CUSTOM_KEYWORDS)} keywords provided")
        topics = []
        for kw in CUSTOM_KEYWORDS:
            topics.append({"title": kw, "hint": "", "_target_category": None})
    else:
        print(f"Getting {ARTICLES_PER_RUN} topics (with category balancing)...")
        topics = build_topics(ARTICLES_PER_RUN, published, posts_index)

    new_count = 0
    for i, t in enumerate(topics):
        title = t["title"]
        slug = slugify(title)
        if slug in published:
            continue
        target_cat = t.get("_target_category")
        print(f"  Writing [{i+1}/{len(topics)}] [{target_cat or '?'}] {title}")
        article = write_article(title, t.get("hint", ""), target_category=target_cat)
        if not article:
            continue
        article["slug"] = slugify(article["title"])
        if is_duplicate(article["slug"], published):
            print(f"  Skipping duplicate: {article['slug']}")
            continue
        # Use target_category as fallback if Claude picked wrong one
        category = article.get("category", "World")
        if target_cat and target_cat in CATEGORIES and category not in CATEGORIES:
            category = target_cat
        author = get_author(category)
        img_kw = article.get("image_keyword") or " ".join(article["title"].split()[:4])
        image = get_image(img_kw, article["slug"])
        article["image_url"] = image
        now = datetime.now(timezone.utc)
        
        html = build_post(article, author, posts_index, now)
        (POSTS_DIR / f"{article['slug']}.html").write_text(html)
        ROOT_POSTS_DIR.mkdir(exist_ok=True)
        (ROOT_POSTS_DIR / f"{article['slug']}.html").write_text(html)
        
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
    build_markets_page()
    build_categories(posts_index)
    build_authors(posts_index)
    build_sitemap(posts_index)
    build_robots()
    build_static_pages()
    build_rss(posts_index)
    convert_existing_to_webp()
    save_published(published)
    save_index(posts_index)
    # posts/index.html → homepage redirect
    (POSTS_DIR / "index.html").write_text(
        f'<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<meta http-equiv="refresh" content="0;url={SITE_URL}/">'
        f'<link rel="canonical" href="{SITE_URL}/">'
        f'</head><body><a href="{SITE_URL}/">Redirecting...</a></body></html>'
    )
    print("Done!")

if __name__ == "__main__":
    main()
