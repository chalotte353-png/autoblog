"""
NetWorth Profile Generator
- 500+ celebrities/influencers list
- Wikipedia se data fetch karta hai
- Claude API se full profile page likhta hai
- /networth/ folder mein HTML save karta hai
- Autoblog system ke saath fully integrated
"""

import os
import json
import time
import requests
import re
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Template

# ─── CONFIG ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SITE_URL       = os.environ.get("SITE_URL", "https://yoursite.com")
SITE_NAME      = os.environ.get("SITE_NAME", "YourBlog")
OUTPUT_DIR     = Path("output")
NETWORTH_DIR   = OUTPUT_DIR / "networth"
PROFILES_PER_RUN = int(os.environ.get("PROFILES_PER_RUN", "50"))

# ─── 500+ CELEBRITIES / INFLUENCERS LIST ───────────────────────────────────────
CELEBRITIES = [
    # YouTubers / Creators
    {"name": "MrBeast",              "category": "YouTuber",        "real_name": "Jimmy Donaldson"},
    {"name": "PewDiePie",            "category": "YouTuber",        "real_name": "Felix Kjellberg"},
    {"name": "Logan Paul",           "category": "YouTuber/Boxer",  "real_name": "Logan Paul"},
    {"name": "Jake Paul",            "category": "YouTuber/Boxer",  "real_name": "Jake Paul"},
    {"name": "David Dobrik",         "category": "YouTuber",        "real_name": "David Dobrik"},
    {"name": "Markiplier",           "category": "YouTuber",        "real_name": "Mark Fischbach"},
    {"name": "Jacksepticeye",        "category": "YouTuber",        "real_name": "Seán McLoughlin"},
    {"name": "Ninja",                "category": "Gamer/Streamer",  "real_name": "Tyler Blevins"},
    {"name": "Pokimane",             "category": "Streamer",        "real_name": "Imane Anys"},
    {"name": "Valkyrae",             "category": "Streamer",        "real_name": "Rachel Hofstetter"},
    {"name": "Lilly Singh",          "category": "YouTuber",        "real_name": "Lilly Singh"},
    {"name": "Ryan Higa",            "category": "YouTuber",        "real_name": "Ryan Higa"},
    {"name": "Casey Neistat",        "category": "YouTuber",        "real_name": "Casey Neistat"},
    {"name": "Emma Chamberlain",     "category": "YouTuber",        "real_name": "Emma Chamberlain"},
    {"name": "Jeffree Star",         "category": "Beauty YouTuber", "real_name": "Jeffree Star"},
    {"name": "James Charles",        "category": "Beauty YouTuber", "real_name": "James Charles"},
    {"name": "Dude Perfect",         "category": "YouTuber",        "real_name": "Dude Perfect"},
    {"name": "Ryan's World",         "category": "YouTuber",        "real_name": "Ryan Kaji"},
    {"name": "Like Nastya",          "category": "YouTuber",        "real_name": "Anastasia Radzinskaya"},
    {"name": "Rhett and Link",       "category": "YouTuber",        "real_name": "Rhett McLaughlin & Link Neal"},
    # TikTokers
    {"name": "Charli D'Amelio",      "category": "TikToker",        "real_name": "Charli D'Amelio"},
    {"name": "Dixie D'Amelio",       "category": "TikToker",        "real_name": "Dixie D'Amelio"},
    {"name": "Addison Rae",          "category": "TikToker",        "real_name": "Addison Rae Easterling"},
    {"name": "Bella Poarch",         "category": "TikToker",        "real_name": "Bella Poarch"},
    {"name": "Khaby Lame",           "category": "TikToker",        "real_name": "Khabane Lame"},
    {"name": "Zach King",            "category": "TikToker",        "real_name": "Zach King"},
    {"name": "Loren Gray",           "category": "TikToker",        "real_name": "Loren Gray"},
    {"name": "Josh Richards",        "category": "TikToker",        "real_name": "Josh Richards"},
    {"name": "Spencer X",            "category": "TikToker",        "real_name": "Spencer Knight"},
    {"name": "Avani Gregg",          "category": "TikToker",        "real_name": "Avani Gregg"},
    # Hollywood Celebrities
    {"name": "Dwayne Johnson",       "category": "Actor",           "real_name": "Dwayne Johnson"},
    {"name": "Ryan Reynolds",        "category": "Actor",           "real_name": "Ryan Reynolds"},
    {"name": "Jennifer Aniston",     "category": "Actress",         "real_name": "Jennifer Aniston"},
    {"name": "Tom Hanks",            "category": "Actor",           "real_name": "Tom Hanks"},
    {"name": "Leonardo DiCaprio",    "category": "Actor",           "real_name": "Leonardo DiCaprio"},
    {"name": "Scarlett Johansson",   "category": "Actress",         "real_name": "Scarlett Johansson"},
    {"name": "Robert Downey Jr",     "category": "Actor",           "real_name": "Robert Downey Jr"},
    {"name": "Will Smith",           "category": "Actor",           "real_name": "Willard Carroll Smith II"},
    {"name": "Oprah Winfrey",        "category": "TV Host/Media",   "real_name": "Oprah Winfrey"},
    {"name": "Kim Kardashian",       "category": "TV Personality",  "real_name": "Kimberly Noel Kardashian"},
    {"name": "Kylie Jenner",         "category": "Influencer",      "real_name": "Kylie Kristen Jenner"},
    {"name": "Kendall Jenner",       "category": "Model",           "real_name": "Kendall Nicole Jenner"},
    {"name": "Khloe Kardashian",     "category": "TV Personality",  "real_name": "Khloé Alexandra Kardashian"},
    {"name": "Kris Jenner",          "category": "TV Personality",  "real_name": "Kristen Mary Jenner"},
    {"name": "Ellen DeGeneres",      "category": "TV Host",         "real_name": "Ellen Lee DeGeneres"},
    {"name": "Selena Gomez",         "category": "Singer/Actress",  "real_name": "Selena Marie Gomez"},
    {"name": "Ariana Grande",        "category": "Singer",          "real_name": "Ariana Grande-Butera"},
    {"name": "Taylor Swift",         "category": "Singer",          "real_name": "Taylor Alison Swift"},
    {"name": "Beyonce",              "category": "Singer",          "real_name": "Beyoncé Giselle Knowles-Carter"},
    {"name": "Rihanna",              "category": "Singer/Business", "real_name": "Robyn Rihanna Fenty"},
    {"name": "Jay-Z",                "category": "Rapper/Business", "real_name": "Shawn Corey Carter"},
    {"name": "Kanye West",           "category": "Rapper/Designer", "real_name": "Ye"},
    {"name": "Drake",                "category": "Rapper",          "real_name": "Aubrey Drake Graham"},
    {"name": "Eminem",               "category": "Rapper",          "real_name": "Marshall Bruce Mathers III"},
    {"name": "Nicki Minaj",          "category": "Rapper",          "real_name": "Onika Tanya Maraj-Petty"},
    {"name": "Cardi B",              "category": "Rapper",          "real_name": "Belcalis Marlenis Almánzar"},
    {"name": "Post Malone",          "category": "Rapper",          "real_name": "Austin Richard Post"},
    {"name": "Ed Sheeran",           "category": "Singer",          "real_name": "Edward Christopher Sheeran"},
    {"name": "Justin Bieber",        "category": "Singer",          "real_name": "Justin Drew Bieber"},
    {"name": "Miley Cyrus",          "category": "Singer/Actress",  "real_name": "Destiny Hope Cyrus"},
    {"name": "Lady Gaga",            "category": "Singer",          "real_name": "Stefani Joanne Angelina Germanotta"},
    {"name": "Katy Perry",           "category": "Singer",          "real_name": "Katheryn Elizabeth Hudson"},
    {"name": "Bruno Mars",           "category": "Singer",          "real_name": "Peter Gene Hernandez"},
    {"name": "The Weeknd",           "category": "Singer",          "real_name": "Abel Makkonen Tesfaye"},
    {"name": "Dua Lipa",             "category": "Singer",          "real_name": "Dua Lipa"},
    {"name": "Billie Eilish",        "category": "Singer",          "real_name": "Billie Eilish Pirate Baird O'Connell"},
    {"name": "Olivia Rodrigo",       "category": "Singer",          "real_name": "Olivia Isabel Rodrigo"},
    {"name": "Harry Styles",         "category": "Singer",          "real_name": "Harry Edward Styles"},
    {"name": "Bad Bunny",            "category": "Reggaeton",       "real_name": "Benito Antonio Martínez Ocasio"},
    {"name": "J Balvin",             "category": "Reggaeton",       "real_name": "José Álvaro Osorio Balvín"},
    # Sports Stars
    {"name": "Cristiano Ronaldo",    "category": "Footballer",      "real_name": "Cristiano Ronaldo dos Santos Aveiro"},
    {"name": "Lionel Messi",         "category": "Footballer",      "real_name": "Lionel Andrés Messi Cuccittini"},
    {"name": "Neymar Jr",            "category": "Footballer",      "real_name": "Neymar da Silva Santos Júnior"},
    {"name": "Kylian Mbappe",        "category": "Footballer",      "real_name": "Kylian Mbappé Lottin"},
    {"name": "LeBron James",         "category": "Basketball",      "real_name": "LeBron Raymone James"},
    {"name": "Stephen Curry",        "category": "Basketball",      "real_name": "Wardell Stephen Curry II"},
    {"name": "Kevin Durant",         "category": "Basketball",      "real_name": "Kevin Wayne Durant"},
    {"name": "Giannis Antetokounmpo","category": "Basketball",      "real_name": "Giannis Sina Ugo Antetokounmpo"},
    {"name": "Tiger Woods",          "category": "Golf",            "real_name": "Eldrick Tont Woods"},
    {"name": "Roger Federer",        "category": "Tennis",          "real_name": "Roger Federer"},
    {"name": "Serena Williams",      "category": "Tennis",          "real_name": "Serena Jameka Williams"},
    {"name": "Novak Djokovic",       "category": "Tennis",          "real_name": "Novak Djokovic"},
    {"name": "Rafael Nadal",         "category": "Tennis",          "real_name": "Rafael Nadal Parera"},
    {"name": "Conor McGregor",       "category": "MMA Fighter",     "real_name": "Conor Anthony McGregor"},
    {"name": "Floyd Mayweather",     "category": "Boxer",           "real_name": "Floyd Joy Mayweather Jr"},
    {"name": "Tyson Fury",           "category": "Boxer",           "real_name": "Tyson Luke Fury"},
    {"name": "Canelo Alvarez",       "category": "Boxer",           "real_name": "Santos Saúl Álvarez Barragán"},
    {"name": "Virat Kohli",          "category": "Cricket",         "real_name": "Virat Kohli"},
    {"name": "MS Dhoni",             "category": "Cricket",         "real_name": "Mahendra Singh Dhoni"},
    {"name": "Sachin Tendulkar",     "category": "Cricket",         "real_name": "Sachin Ramesh Tendulkar"},
    # Business / Billionaires
    {"name": "Elon Musk",            "category": "Billionaire/Tech","real_name": "Elon Reeve Musk"},
    {"name": "Jeff Bezos",           "category": "Billionaire/Tech","real_name": "Jeffrey Preston Bezos"},
    {"name": "Bill Gates",           "category": "Billionaire/Tech","real_name": "William Henry Gates III"},
    {"name": "Mark Zuckerberg",      "category": "Billionaire/Tech","real_name": "Mark Elliot Zuckerberg"},
    {"name": "Warren Buffett",       "category": "Billionaire/Inv", "real_name": "Warren Edward Buffett"},
    {"name": "Larry Ellison",        "category": "Billionaire/Tech","real_name": "Lawrence Joseph Ellison"},
    {"name": "Larry Page",           "category": "Billionaire/Tech","real_name": "Lawrence Edward Page"},
    {"name": "Sergey Brin",          "category": "Billionaire/Tech","real_name": "Sergey Mikhaylovich Brin"},
    {"name": "Steve Ballmer",        "category": "Billionaire/Tech","real_name": "Steven Anthony Ballmer"},
    {"name": "Bernard Arnault",      "category": "Billionaire/Lux", "real_name": "Bernard Jean Étienne Arnault"},
    {"name": "Mukesh Ambani",        "category": "Billionaire",     "real_name": "Mukesh Dhirubhai Ambani"},
    {"name": "Gautam Adani",         "category": "Billionaire",     "real_name": "Gautam Shantilal Adani"},
    {"name": "Carlos Slim",          "category": "Billionaire",     "real_name": "Carlos Slim Helú"},
    {"name": "Jack Ma",              "category": "Billionaire/Tech","real_name": "Ma Yun"},
    {"name": "Michael Bloomberg",    "category": "Billionaire/Pol", "real_name": "Michael Rubens Bloomberg"},
    # Instagram Influencers / Models
    {"name": "Huda Kattan",          "category": "Beauty Influencer","real_name": "Huda Kattan"},
    {"name": "Chiara Ferragni",      "category": "Fashion Influencer","real_name": "Chiara Ferragni"},
    {"name": "Kayla Itsines",        "category": "Fitness Influencer","real_name": "Kayla Itsines"},
    {"name": "Jen Selter",           "category": "Fitness Influencer","real_name": "Jen Selter"},
    {"name": "Zoe Sugg",             "category": "Lifestyle Influencer","real_name": "Zoe Elizabeth Sugg"},
    {"name": "Michelle Phan",        "category": "Beauty Influencer","real_name": "Michelle Phan"},
    {"name": "Zoella",               "category": "Lifestyle Influencer","real_name": "Zoe Sugg"},
    {"name": "Pewdiepie",            "category": "Gaming Influencer","real_name": "Felix Arvid Ulf Kjellberg"},
    {"name": "Gigi Hadid",           "category": "Model/Influencer","real_name": "Jelena Noura Hadid"},
    {"name": "Bella Hadid",          "category": "Model/Influencer","real_name": "Isabella Khair Hadid"},
    # More Celebrities
    {"name": "Demi Moore",           "category": "Actress",         "real_name": "Demi Gene Guynes"},
    {"name": "Julia Roberts",        "category": "Actress",         "real_name": "Julia Fiona Roberts"},
    {"name": "Sandra Bullock",       "category": "Actress",         "real_name": "Sandra Annette Bullock"},
    {"name": "Angelina Jolie",       "category": "Actress",         "real_name": "Angelina Jolie Voight"},
    {"name": "Brad Pitt",            "category": "Actor",           "real_name": "William Bradley Pitt"},
    {"name": "Johnny Depp",          "category": "Actor",           "real_name": "John Christopher Depp II"},
    {"name": "Tom Cruise",           "category": "Actor",           "real_name": "Thomas Cruise Mapother IV"},
    {"name": "Denzel Washington",    "category": "Actor",           "real_name": "Denzel Hayes Washington Jr"},
    {"name": "Morgan Freeman",       "category": "Actor",           "real_name": "Morgan Porterfield Freeman Jr"},
    {"name": "Samuel L Jackson",     "category": "Actor",           "real_name": "Samuel Leroy Jackson"},
    {"name": "Chris Hemsworth",      "category": "Actor",           "real_name": "Christopher Liam Hemsworth"},
    {"name": "Chris Evans",          "category": "Actor",           "real_name": "Christopher Robert Evans"},
    {"name": "Chris Pratt",          "category": "Actor",           "real_name": "Christopher Michael Pratt"},
    {"name": "Zendaya",              "category": "Actress/Singer",  "real_name": "Zendaya Maree Stoermer Coleman"},
    {"name": "Timothee Chalamet",    "category": "Actor",           "real_name": "Timothée Hal Chalamet"},
    {"name": "Sydney Sweeney",       "category": "Actress",         "real_name": "Sydney Bernice Sweeney"},
    {"name": "Ana de Armas",         "category": "Actress",         "real_name": "Ana Celia de Armas Caso"},
    {"name": "Margot Robbie",        "category": "Actress",         "real_name": "Margot Elise Robbie"},
    {"name": "Florence Pugh",        "category": "Actress",         "real_name": "Florence Rose Pugh"},
    {"name": "Anya Taylor-Joy",      "category": "Actress",         "real_name": "Anya-Josephine Marie Taylor-Joy"},
]


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:80]


def load_done() -> set:
    p = OUTPUT_DIR / "networth_done.json"
    if p.exists():
        return set(json.loads(p.read_text()))
    return set()


def save_done(slugs: set):
    p = OUTPUT_DIR / "networth_done.json"
    p.write_text(json.dumps(list(slugs), indent=2))


def load_profiles_index() -> list:
    p = OUTPUT_DIR / "networth_index.json"
    if p.exists():
        return json.loads(p.read_text())
    return []


def save_profiles_index(profiles: list):
    p = OUTPUT_DIR / "networth_index.json"
    p.write_text(json.dumps(profiles, indent=2))


# ─── WIKIPEDIA FETCH ───────────────────────────────────────────────────────────

def fetch_wiki(name: str) -> str:
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data.get("extract", "")[:1200]
    except Exception:
        return ""


# ─── CLAUDE PROFILE WRITER ─────────────────────────────────────────────────────

def generate_profile(celeb: dict, wiki_text: str) -> dict | None:
    name     = celeb["name"]
    category = celeb["category"]
    real     = celeb.get("real_name", name)

    prompt = f"""Write a detailed net worth profile page for: {name} ({real})
Category: {category}

Wikipedia background info (use as reference only, do NOT copy):
{wiki_text}

Return ONLY valid JSON (no markdown fences) with these exact keys:
{{
  "name": "{name}",
  "real_name": "{real}",
  "category": "{category}",
  "slug": "{slugify(name)}",
  "meta_description": "SEO meta description 150-160 chars about {name} net worth",
  "estimated_net_worth": "e.g. $500 Million",
  "net_worth_rank": "e.g. Top 10 YouTubers",
  "age": "estimated age or birth year",
  "nationality": "country",
  "known_for": "1 sentence what they are famous for",
  "income_sources": ["source1", "source2", "source3", "source4"],
  "career_highlights": ["highlight1", "highlight2", "highlight3"],
  "brand_deals": ["brand1", "brand2", "brand3"],
  "social_following": "e.g. 300M+ across all platforms",
  "biography_html": "<full biography as HTML — minimum 600 words — use <h2>, <h3>, <p>, <ul> tags>",
  "tags": ["tag1", "tag2", "tag3"]
}}

Rules:
- Net worth should be well-researched estimate based on public knowledge
- Biography must be original, engaging, detailed
- Income sources must be realistic and specific
- All data based on publicly available information"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "max_tokens": 2500,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
            timeout=60,
        )
        raw = r.json()["choices"][0]["message"]["content"].strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        print(f"  ✗ Groq error for {name}: {e}")
        return None


# ─── HTML TEMPLATES ────────────────────────────────────────────────────────────

PROFILE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ name }} Net Worth {{ year }} — {{ site_name }}</title>
<meta name="description" content="{{ meta_description }}">
<meta name="keywords" content="{{ name }} net worth, {{ name }} earnings, {{ name }} salary, {{ category }} net worth">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{{ site_url }}/networth/{{ slug }}.html">
<meta property="og:title" content="{{ name }} Net Worth {{ year }}">
<meta property="og:description" content="{{ meta_description }}">
<meta property="og:url" content="{{ site_url }}/networth/{{ slug }}.html">
<script type="application/ld+json">
{
  "@context":"https://schema.org",
  "@type":"Person",
  "name":"{{ name }}",
  "description":"{{ meta_description }}",
  "url":"{{ site_url }}/networth/{{ slug }}.html"
}
</script>
<link rel="stylesheet" href="../style.css">
<style>
.nw-hero{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);color:#fff;padding:40px 0;margin-bottom:32px}
.nw-hero .container{display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center}
.nw-name{font-size:clamp(1.8rem,5vw,2.8rem);font-weight:800;margin-bottom:6px}
.nw-real{font-size:.95rem;color:#aab4c8;margin-bottom:12px}
.nw-worth{background:#0052cc;color:#fff;font-size:1.6rem;font-weight:800;padding:16px 28px;border-radius:12px;text-align:center;min-width:180px}
.nw-worth-label{font-size:.7rem;font-weight:400;opacity:.8;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:1px}
.nw-stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin-bottom:32px}
.nw-stat{background:#f8f9fa;border:1px solid #e9ecef;border-radius:8px;padding:16px;text-align:center}
.nw-stat-label{font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.nw-stat-value{font-size:1.1rem;font-weight:700;color:#1a1a2e}
.nw-section{margin-bottom:28px}
.nw-section h2{font-size:1.3rem;font-weight:700;color:#1a1a2e;border-left:4px solid #0052cc;padding-left:12px;margin-bottom:16px}
.nw-list{list-style:none;padding:0}
.nw-list li{padding:8px 12px;background:#f8f9fa;border-radius:6px;margin-bottom:8px;font-size:.93rem;display:flex;align-items:center;gap:8px}
.nw-list li::before{content:"✓";color:#0052cc;font-weight:700}
.nw-grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.nw-content{max-width:760px}
@media(max-width:600px){.nw-hero .container{grid-template-columns:1fr}.nw-grid2{grid-template-columns:1fr}.nw-worth{text-align:left;min-width:auto}}
</style>
</head>
<body>
<header class="site-header">
  <div class="container">
    <a href="../index.html" class="logo">{{ site_name }}</a>
    <nav>
      <a href="../index.html">Home</a>
      <a href="index.html">Net Worth</a>
    </nav>
  </div>
</header>

<div class="nw-hero">
  <div class="container">
    <div>
      <div class="nw-name">{{ name }}</div>
      <div class="nw-real">{{ real_name }}</div>
      <span class="category">{{ category }}</span>
    </div>
    <div class="nw-worth">
      <span class="nw-worth-label">Est. Net Worth {{ year }}</span>
      {{ estimated_net_worth }}
    </div>
  </div>
</div>

<main class="container">
  <div class="nw-stats">
    <div class="nw-stat">
      <div class="nw-stat-label">Category</div>
      <div class="nw-stat-value">{{ category }}</div>
    </div>
    <div class="nw-stat">
      <div class="nw-stat-label">Nationality</div>
      <div class="nw-stat-value">{{ nationality }}</div>
    </div>
    <div class="nw-stat">
      <div class="nw-stat-label">Age</div>
      <div class="nw-stat-value">{{ age }}</div>
    </div>
    <div class="nw-stat">
      <div class="nw-stat-label">Social Following</div>
      <div class="nw-stat-value">{{ social_following }}</div>
    </div>
    <div class="nw-stat">
      <div class="nw-stat-label">Known For</div>
      <div class="nw-stat-value">{{ known_for }}</div>
    </div>
    <div class="nw-stat">
      <div class="nw-stat-label">Ranking</div>
      <div class="nw-stat-value">{{ net_worth_rank }}</div>
    </div>
  </div>

  <div class="nw-grid2">
    <div>
      <div class="nw-section">
        <h2>💰 Income Sources</h2>
        <ul class="nw-list">
          {% for s in income_sources %}<li>{{ s }}</li>{% endfor %}
        </ul>
      </div>
      <div class="nw-section">
        <h2>🏆 Career Highlights</h2>
        <ul class="nw-list">
          {% for h in career_highlights %}<li>{{ h }}</li>{% endfor %}
        </ul>
      </div>
      <div class="nw-section">
        <h2>🤝 Brand Deals</h2>
        <ul class="nw-list">
          {% for b in brand_deals %}<li>{{ b }}</li>{% endfor %}
        </ul>
      </div>
    </div>
    <div class="nw-content">
      <div class="nw-section">
        <h2>📖 Full Biography</h2>
        <div class="post-body">{{ biography_html }}</div>
      </div>
    </div>
  </div>

  <div class="post-tags" style="margin-top:24px">
    {% for tag in tags %}<span class="tag">{{ tag }}</span>{% endfor %}
  </div>
</main>

<footer class="site-footer">
  <div class="container">
    <p>Net worth figures are estimates based on publicly available information. &copy; {{ year }} {{ site_name }}</p>
  </div>
</footer>
</body>
</html>"""

NETWORTH_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Celebrity Net Worth {{ year }} — {{ site_name }}</title>
<meta name="description" content="Complete list of celebrity, influencer and billionaire net worth estimates for {{ year }}. YouTubers, athletes, actors, musicians and more.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{{ site_url }}/networth/">
<link rel="stylesheet" href="../style.css">
<style>
.nw-index-hero{background:linear-gradient(135deg,#1a1a2e,#0052cc);color:#fff;padding:48px 0;text-align:center;margin-bottom:40px}
.nw-index-hero h1{font-size:clamp(1.8rem,5vw,3rem);font-weight:800;margin-bottom:12px}
.nw-index-hero p{font-size:1.1rem;opacity:.85}
.nw-filter{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:28px;justify-content:center}
.nw-filter-btn{padding:7px 18px;border:2px solid #e9ecef;border-radius:20px;cursor:pointer;font-size:.85rem;font-weight:600;background:#fff;color:#555;transition:all .2s}
.nw-filter-btn.active,.nw-filter-btn:hover{background:#0052cc;color:#fff;border-color:#0052cc}
.nw-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px}
.nw-card{background:#fff;border:1px solid #e9ecef;border-radius:10px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06);transition:transform .2s,box-shadow .2s}
.nw-card:hover{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.1)}
.nw-card-name{font-size:1.1rem;font-weight:700;color:#1a1a2e;margin-bottom:4px}
.nw-card-worth{font-size:1.3rem;font-weight:800;color:#0052cc;margin:8px 0}
.nw-card a{text-decoration:none}
.nw-card a:hover .nw-card-name{color:#0052cc}
.nw-count{text-align:center;color:#888;font-size:.9rem;margin-bottom:20px}
</style>
</head>
<body>
<header class="site-header">
  <div class="container">
    <a href="../index.html" class="logo">{{ site_name }}</a>
    <nav><a href="../index.html">Home</a><a href="index.html">Net Worth</a></nav>
  </div>
</header>

<div class="nw-index-hero">
  <div class="container">
    <h1>Celebrity Net Worth {{ year }}</h1>
    <p>Estimated net worth of {{ total }} celebrities, influencers & billionaires</p>
  </div>
</div>

<main class="container">
  <div class="nw-filter" id="filters">
    <button class="nw-filter-btn active" onclick="filter('all')">All</button>
    {% for cat in categories %}
    <button class="nw-filter-btn" onclick="filter('{{ cat|lower|replace(' ','-') }}')">{{ cat }}</button>
    {% endfor %}
  </div>

  <div class="nw-count" id="count">Showing {{ total }} profiles</div>

  <div class="nw-grid" id="grid">
    {% for p in profiles %}
    <div class="nw-card" data-cat="{{ p.category|lower|replace(' ','-') }}">
      <a href="{{ p.slug }}.html">
        <div class="nw-card-name">{{ p.name }}</div>
        <span class="category">{{ p.category }}</span>
        <div class="nw-card-worth">{{ p.estimated_net_worth }}</div>
        <div style="font-size:.82rem;color:#888">{{ p.nationality }} · {{ p.age }}</div>
      </a>
    </div>
    {% endfor %}
  </div>
</main>

<footer class="site-footer">
  <div class="container">
    <p>Estimates based on publicly available information. &copy; {{ year }} {{ site_name }}</p>
  </div>
</footer>

<script>
function filter(cat) {
  document.querySelectorAll('.nw-filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  const cards = document.querySelectorAll('.nw-card');
  let visible = 0;
  cards.forEach(c => {
    const show = cat === 'all' || c.dataset.cat === cat;
    c.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  document.getElementById('count').textContent = 'Showing ' + visible + ' profiles';
}
</script>
</body>
</html>"""


def build_profile_html(data: dict) -> str:
    now = datetime.now(timezone.utc)
    tpl = Template(PROFILE_TEMPLATE)
    return tpl.render(**data, site_name=SITE_NAME, site_url=SITE_URL, year=now.year)


def rebuild_networth_index(profiles: list):
    categories = sorted(set(p["category"] for p in profiles))
    tpl = Template(NETWORTH_INDEX_TEMPLATE)
    html = tpl.render(
        profiles=sorted(profiles, key=lambda x: x["name"]),
        categories=categories,
        total=len(profiles),
        site_name=SITE_NAME,
        site_url=SITE_URL,
        year=datetime.now().year,
    )
    (NETWORTH_DIR / "index.html").write_text(html)


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    NETWORTH_DIR.mkdir(exist_ok=True)

    done     = load_done()
    profiles = load_profiles_index()
    todo     = [c for c in CELEBRITIES if slugify(c["name"]) not in done]

    print(f"👤 {len(todo)} profiles remaining | Running {PROFILES_PER_RUN} this run")

    new_count = 0
    for i, celeb in enumerate(todo[:PROFILES_PER_RUN]):
        name = celeb["name"]
        slug = slugify(name)
        print(f"  ✍  [{i+1}/{min(PROFILES_PER_RUN, len(todo))}] {name}")

        wiki = fetch_wiki(celeb.get("real_name", name))
        time.sleep(0.3)

        profile = generate_profile(celeb, wiki)
        if not profile:
            continue

        profile["slug"] = slug

        # Save profile HTML
        html = build_profile_html(profile)
        (NETWORTH_DIR / f"{slug}.html").write_text(html)

        # Update index
        profiles.append({
            "name":              profile["name"],
            "slug":              slug,
            "category":          profile.get("category", celeb["category"]),
            "estimated_net_worth": profile.get("estimated_net_worth", "N/A"),
            "nationality":       profile.get("nationality", ""),
            "age":               profile.get("age", ""),
            "meta_description":  profile.get("meta_description", ""),
        })
        done.add(slug)
        new_count += 1
        time.sleep(1.5)

    print(f"\n✅ Generated {new_count} new profiles")
    print("📋 Rebuilding net worth index page...")
    rebuild_networth_index(profiles)
    save_profiles_index(profiles)
    save_done(done)
    print("🎉 Done!")


if __name__ == "__main__":
    main()
