import os, json, requests, re
from datetime import datetime, timezone
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────
SITE_URL   = os.environ.get("SITE_URL", "https://marketsnewstoday.info")
SITE_NAME  = "Markets News Today"
OUTPUT_DIR = Path("output")

# ── TOP 10 COINS ────────────────────────────────────────────────────
COINS = [
    {"slug": "bitcoin",   "sym": "BTC", "name": "Bitcoin",   "tag": "bitcoin",   "color": "#F7931A", "desc": "The world's first and largest cryptocurrency by market cap."},
    {"slug": "ethereum",  "sym": "ETH", "name": "Ethereum",  "tag": "ethereum",  "color": "#627EEA", "desc": "The leading smart contract platform powering DeFi and Web3."},
    {"slug": "solana",    "sym": "SOL", "name": "Solana",    "tag": "solana",    "color": "#9945FF", "desc": "High-performance blockchain known for speed and low fees."},
    {"slug": "xrp",       "sym": "XRP", "name": "XRP",       "tag": "xrp",       "color": "#00AAE4", "desc": "Digital payment protocol focused on fast cross-border transactions."},
    {"slug": "bnb",       "sym": "BNB", "name": "BNB",       "tag": "bnb",       "color": "#F3BA2F", "desc": "Native token of the Binance ecosystem and BNB Chain."},
    {"slug": "dogecoin",  "sym": "DOGE","name": "Dogecoin",  "tag": "dogecoin",  "color": "#C2A633", "desc": "The original meme coin with a strong community and wide adoption."},
    {"slug": "cardano",   "sym": "ADA", "name": "Cardano",   "tag": "cardano",   "color": "#0033AD", "desc": "Proof-of-stake blockchain focused on security and scalability."},
    {"slug": "avalanche", "sym": "AVAX","name": "Avalanche", "tag": "avalanche", "color": "#E84142", "desc": "Fast, low-cost smart contract platform with subnet architecture."},
    {"slug": "chainlink", "sym": "LINK","name": "Chainlink", "tag": "chainlink", "color": "#2A5ADA", "desc": "Decentralized oracle network connecting blockchains to real-world data."},
    {"slug": "polkadot",  "sym": "DOT", "name": "Polkadot",  "tag": "polkadot",  "color": "#E6007A", "desc": "Multi-chain protocol enabling blockchain interoperability."},
]

# ── HELPERS ─────────────────────────────────────────────────────────
def fmt_price(p):
    if p >= 1000: return f"${p:,.2f}"
    if p >= 1:    return f"${p:,.4f}"
    return f"${p:.6f}"

def fmt_large(n):
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.2f}B"
    if n >= 1e6:  return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"

def fmt_change(c):
    sign = "+" if c >= 0 else ""
    return f"{sign}{c:.2f}%"

def change_class(c):
    return "coin-up" if c >= 0 else "coin-dn"

def fetch_coin_data():
    """Fetch live data for all 10 coins from CryptoCompare."""
    syms = ",".join(c["sym"] for c in COINS)
    try:
        r = requests.get(
            "https://min-api.cryptocompare.com/data/pricemultifull",
            params={"fsyms": syms, "tsyms": "USD"},
            timeout=10
        )
        raw = r.json().get("RAW", {})
        result = {}
        for sym, info in raw.items():
            usd = info.get("USD", {})
            result[sym] = {
                "price":     usd.get("PRICE", 0),
                "change24h": usd.get("CHANGEPCT24HOUR", 0),
                "change7d":  usd.get("CHANGEPCT7D", 0),
                "marketcap": usd.get("MKTCAP", 0),
                "volume24h": usd.get("VOLUME24HOURTO", 0),
                "high24h":   usd.get("HIGH24HOUR", 0),
                "low24h":    usd.get("LOW24HOUR", 0),
                "supply":    usd.get("SUPPLY", 0),
                "rank":      usd.get("IMAGEURL", ""),
            }
        return result
    except Exception as e:
        print(f"  Coin data fetch error: {e}")
        return {}

def get_coin_articles(coin_tag, posts_index):
    """Get all articles tagged with this coin."""
    articles = [p for p in posts_index if p.get("coin_tag","") == coin_tag]
    articles.sort(key=lambda x: x.get("date_iso",""), reverse=True)
    return articles[:20]

def nav_html():
    d = datetime.now().strftime("%A, %B %d, %Y")
    return f"""<div class="topbar"><div class="topbar-inner">
  <span class="topbar-left">{d}</span>
  <a href="../" class="topbar-logo">Markets <span class="accent">News</span> Today</a>
  <span class="topbar-right">Crypto &middot; AI &middot; Stocks</span>
</div></div>
<nav class="navbar">
<div class="navbar-wrap">
  <div class="navbar-inner">
    <a href="../" class="nav-link">Home</a>
    <div class="nav-dropdown">
      <a href="../category-crypto.html" class="nav-link nav-dropdown-trigger">Crypto &#9662;</a>
      <div class="nav-dropdown-menu">
        <div class="nav-dropdown-col">
          <span class="nav-dropdown-head">Top Coins</span>
          <a href="../bitcoin.html">Bitcoin (BTC)</a>
          <a href="../ethereum.html">Ethereum (ETH)</a>
          <a href="../solana.html">Solana (SOL)</a>
          <a href="../xrp.html">XRP</a>
          <a href="../bnb.html">BNB</a>
          <a href="../dogecoin.html">Dogecoin</a>
          <a href="../cardano.html">Cardano</a>
          <a href="../avalanche.html">Avalanche</a>
          <a href="../chainlink.html">Chainlink</a>
          <a href="../polkadot.html">Polkadot</a>
        </div>
        <div class="nav-dropdown-col">
          <span class="nav-dropdown-head">Topics</span>
          <a href="../category-crypto.html">All Crypto News</a>
          <a href="../category-defi.html">DeFi</a>
          <a href="../category-blockchain.html">Blockchain</a>
          <a href="../category-web3.html">Web3</a>
        </div>
      </div>
    </div>
    <div class="nav-dropdown">
      <a href="../category-ai.html" class="nav-link nav-dropdown-trigger">AI &#9662;</a>
      <div class="nav-dropdown-menu">
        <div class="nav-dropdown-col">
          <span class="nav-dropdown-head">AI Coverage</span>
          <a href="../category-ai.html">All AI News</a>
          <a href="../category-technology.html">Technology</a>
        </div>
      </div>
    </div>
    <div class="nav-dropdown">
      <a href="../category-stocks.html" class="nav-link nav-dropdown-trigger">Stocks &#9662;</a>
      <div class="nav-dropdown-menu">
        <div class="nav-dropdown-col">
          <span class="nav-dropdown-head">Markets</span>
          <a href="../category-stocks.html">All Stocks</a>
          <a href="../category-markets.html">Markets</a>
          <a href="../category-forex.html">Forex</a>
          <a href="../category-investing.html">Investing</a>
          <a href="../category-economy.html">Economy</a>
          <a href="../category-finance.html">Finance</a>
        </div>
      </div>
    </div>
    <a href="../markets.html" class="nav-link">Live Markets</a>
  </div>
</div>
</nav>"""

def foot_html():
    y = datetime.now().year
    return f"""<footer class="footer"><div class="footer-top"><div class="container"><div class="footer-grid">
  <div class="footer-brand">
    <div class="footer-logo">Markets <span class="accent">News</span> Today</div>
    <p>Your trusted source for crypto, AI, stocks and financial market analysis.</p>
  </div>
  <div class="footer-col"><h4>Crypto</h4>
    <a href="../category-crypto.html">All Crypto</a>
    <a href="../bitcoin.html">Bitcoin</a>
    <a href="../ethereum.html">Ethereum</a>
    <a href="../solana.html">Solana</a>
    <a href="../xrp.html">XRP</a></div>
  <div class="footer-col"><h4>Coins</h4>
    <a href="../bnb.html">BNB</a>
    <a href="../dogecoin.html">Dogecoin</a>
    <a href="../cardano.html">Cardano</a>
    <a href="../avalanche.html">Avalanche</a>
    <a href="../polkadot.html">Polkadot</a></div>
  <div class="footer-col"><h4>Markets</h4>
    <a href="../markets.html">Live Markets</a>
    <a href="../category-stocks.html">Stocks</a>
    <a href="../category-forex.html">Forex</a>
    <a href="../category-finance.html">Finance</a>
    <a href="../category-investing.html">Investing</a></div>
  <div class="footer-col"><h4>Technology</h4>
    <a href="../category-ai.html">AI</a>
    <a href="../category-technology.html">Technology</a>
    <a href="../category-blockchain.html">Blockchain</a>
    <a href="../category-defi.html">DeFi</a>
    <a href="../category-web3.html">Web3</a></div>
  <div class="footer-col"><h4>Company</h4>
    <a href="../about.html">About Us</a>
    <a href="../contact.html">Contact</a>
    <a href="../privacy-policy.html">Privacy Policy</a>
    <a href="../sitemap.xml">Sitemap</a></div>
</div></div></div>
<div class="footer-btm"><div class="container">&copy; {y} Markets News Today. All rights reserved.</div></div>
</footer>"""

def build_coin_page(coin, data, articles):
    """Build a complete coin page with live data + articles."""
    sym   = coin["sym"]
    name  = coin["name"]
    slug  = coin["slug"]
    color = coin["color"]
    desc  = coin["desc"]

    d = data.get(sym, {})
    price     = d.get("price", 0)
    change24h = d.get("change24h", 0)
    change7d  = d.get("change7d", 0)
    marketcap = d.get("marketcap", 0)
    volume24h = d.get("volume24h", 0)
    high24h   = d.get("high24h", 0)
    low24h    = d.get("low24h", 0)
    supply    = d.get("supply", 0)

    price_str  = fmt_price(price)
    chg24_str  = fmt_change(change24h)
    chg7d_str  = fmt_change(change7d)
    mcap_str   = fmt_large(marketcap)
    vol_str    = fmt_large(volume24h)
    high_str   = fmt_price(high24h)
    low_str    = fmt_price(low24h)
    supply_str = fmt_large(supply) if supply > 0 else "N/A"

    chg24_cls = change_class(change24h)
    chg7d_cls = change_class(change7d)

    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC")

    # Build articles section
    articles_html = ""
    if articles:
        cards = ""
        for a in articles:
            img = a.get("image_url", "") or f"https://picsum.photos/seed/{a['slug']}/400/240"
            cards += f"""
            <div class="coin-article-card">
              <a href="../posts/{a['slug']}.html">
                <img src="{img}" alt="{a['title']}" loading="lazy" width="400" height="240">
              </a>
              <div class="coin-article-info">
                <span class="coin-article-date">{a.get('date_human','')}</span>
                <h3><a href="../posts/{a['slug']}.html">{a['title']}</a></h3>
                <p>{a.get('excerpt','')[:120]}...</p>
                <a href="../posts/{a['slug']}.html" class="coin-article-read">Read More &rarr;</a>
              </div>
            </div>"""
        articles_html = f"""
        <section class="coin-articles">
          <div class="container">
            <div class="coin-articles-hdr">
              <h2>Latest {name} News &amp; Analysis</h2>
            </div>
            <div class="coin-articles-grid">{cards}</div>
          </div>
        </section>"""
    else:
        articles_html = f"""
        <section class="coin-articles">
          <div class="container">
            <div class="coin-articles-hdr">
              <h2>Latest {name} News &amp; Analysis</h2>
            </div>
            <p style="color:#888;padding:24px 0">No articles yet. Check back soon.</p>
          </div>
        </section>"""

    # Schema markup
    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"{name} ({sym}) Price, News & Analysis",
        "description": f"Live {name} price, market cap, 24h change and latest {name} news and analysis.",
        "url": f"{SITE_URL}/{slug}.html",
        "publisher": {
            "@type": "NewsMediaOrganization",
            "name": SITE_NAME,
            "url": SITE_URL
        }
    })

    breadcrumb = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": "Crypto", "item": f"{SITE_URL}/category-crypto.html"},
            {"@type": "ListItem", "position": 3, "name": name, "item": f"{SITE_URL}/{slug}.html"}
        ]
    })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} ({sym}) Price Today, News & Analysis | {SITE_NAME}</title>
<meta name="description" content="Live {name} price ${price_str}, {chg24_str} (24h). Market cap {mcap_str}. Latest {name} news, price analysis and expert insights.">
<meta property="og:title" content="{name} Price Today — {price_str} {chg24_str}">
<meta property="og:description" content="Live {name} ({sym}) price, market cap, volume and latest news.">
<meta property="og:url" content="{SITE_URL}/{slug}.html">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE_URL}/{slug}.html">
<link rel="stylesheet" href="../style.css">
<script type="application/ld+json">{schema}</script>
<script type="application/ld+json">{breadcrumb}</script>
<style>
.coin-hero {{ background: linear-gradient(135deg, {color}15 0%, #fff 60%); border-bottom: 1px solid #eee; padding: 40px 0 32px; }}
.coin-hero-inner {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
.coin-hero-top {{ display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }}
.coin-icon {{ width: 56px; height: 56px; border-radius: 50%; background: {color}20; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 700; color: {color}; border: 2px solid {color}40; }}
.coin-name {{ font-size: 28px; font-weight: 800; color: var(--dark); }}
.coin-sym {{ font-size: 14px; color: #888; margin-left: 8px; font-weight: 500; }}
.coin-price {{ font-size: 42px; font-weight: 800; color: var(--dark); margin-bottom: 8px; }}
.coin-up {{ color: #16a34a; }}
.coin-dn {{ color: #dc2626; }}
.coin-change {{ font-size: 18px; font-weight: 600; }}
.coin-updated {{ font-size: 11px; color: #aaa; margin-top: 6px; }}
.coin-stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-top: 28px; }}
.coin-stat {{ background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 14px 16px; }}
.coin-stat-label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
.coin-stat-value {{ font-size: 18px; font-weight: 700; color: var(--dark); }}
.coin-about {{ max-width: 1200px; margin: 32px auto; padding: 0 20px; }}
.coin-about h2 {{ font-size: 22px; font-weight: 700; margin-bottom: 12px; color: var(--dark); border-left: 4px solid {color}; padding-left: 12px; }}
.coin-about p {{ font-size: 16px; line-height: 1.8; color: #444; }}
.coin-articles {{ padding: 40px 0; background: #fafafa; }}
.coin-articles-hdr h2 {{ font-size: 24px; font-weight: 800; margin-bottom: 24px; color: var(--dark); }}
.coin-articles-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 24px; }}
.coin-article-card {{ background: #fff; border-radius: 10px; overflow: hidden; border: 1px solid #eee; transition: box-shadow 0.2s; }}
.coin-article-card:hover {{ box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
.coin-article-card img {{ width: 100%; height: 180px; object-fit: cover; }}
.coin-article-info {{ padding: 16px; }}
.coin-article-date {{ font-size: 11px; color: #aaa; }}
.coin-article-info h3 {{ font-size: 16px; font-weight: 700; margin: 6px 0 8px; line-height: 1.4; }}
.coin-article-info h3 a {{ color: var(--dark); text-decoration: none; }}
.coin-article-info h3 a:hover {{ color: var(--red); }}
.coin-article-info p {{ font-size: 13px; color: #666; line-height: 1.6; margin-bottom: 12px; }}
.coin-article-read {{ font-size: 12px; font-weight: 600; color: var(--red); text-decoration: none; }}
@media(max-width:600px) {{
  .coin-price {{ font-size: 30px; }}
  .coin-name {{ font-size: 22px; }}
  .coin-stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>
</head>
<body>
{nav_html()}

<div class="coin-hero">
  <div class="coin-hero-inner">
    <div class="coin-hero-top">
      <div class="coin-icon">{sym[0]}</div>
      <div>
        <div><span class="coin-name">{name}</span><span class="coin-sym">{sym}</span></div>
        <div style="font-size:13px;color:#888">{desc}</div>
      </div>
    </div>

    <div class="coin-price" id="cp-price">{price_str}</div>
    <div>
      <span class="coin-change {chg24_cls}" id="cp-24h">{chg24_str} (24h)</span>
      &nbsp;&nbsp;
      <span class="coin-change {chg7d_cls}" id="cp-7d" style="font-size:15px">{chg7d_str} (7d)</span>
    </div>
    <div class="coin-updated" id="cp-updated">Last updated: {now_str}</div>

    <div class="coin-stats-grid">
      <div class="coin-stat">
        <div class="coin-stat-label">Market Cap</div>
        <div class="coin-stat-value" id="cp-mcap">{mcap_str}</div>
      </div>
      <div class="coin-stat">
        <div class="coin-stat-label">24h Volume</div>
        <div class="coin-stat-value" id="cp-vol">{vol_str}</div>
      </div>
      <div class="coin-stat">
        <div class="coin-stat-label">24h High</div>
        <div class="coin-stat-value" id="cp-high">{high_str}</div>
      </div>
      <div class="coin-stat">
        <div class="coin-stat-label">24h Low</div>
        <div class="coin-stat-value" id="cp-low">{low_str}</div>
      </div>
      <div class="coin-stat">
        <div class="coin-stat-label">Circulating Supply</div>
        <div class="coin-stat-value">{supply_str}</div>
      </div>
    </div>
  </div>
</div>

<!-- TradingView Chart -->
<div style="max-width:1200px;margin:32px auto;padding:0 20px">
  <div class="tradingview-widget-container" style="border:1px solid #eee;border-radius:10px;overflow:hidden">
    <div id="tradingview_{sym.lower()}"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{
      "width": "100%", "height": 400,
      "symbol": "BINANCE:{sym}USDT",
      "interval": "D", "timezone": "Etc/UTC",
      "theme": "light", "style": "1", "locale": "en",
      "toolbar_bg": "#f1f3f6", "enable_publishing": false,
      "hide_top_toolbar": false, "hide_legend": false,
      "save_image": false, "container_id": "tradingview_{sym.lower()}"
    }});
    </script>
  </div>
</div>

<!-- About section -->
<div class="coin-about">
  <h2>About {name}</h2>
  <p>{desc} {name} ({sym}) is one of the most actively traded cryptocurrencies in the world,
  with a 24-hour trading volume of {vol_str} and a market capitalization of {mcap_str}.
  Stay up to date with the latest {name} news, price analysis and expert commentary below.</p>
</div>

{articles_html}

{foot_html()}

<!-- Live price refresh every 60s -->
<script>
function refreshPrice() {{
  fetch('https://min-api.cryptocompare.com/data/pricemultifull?fsyms={sym}&tsyms=USD')
    .then(r => r.json())
    .then(data => {{
      var d = data.RAW && data.RAW.{sym} && data.RAW.{sym}.USD;
      if (!d) return;
      var p = d.PRICE;
      var c24 = d.CHANGEPCT24HOUR;
      var c7 = d.CHANGEPCT7D || 0;
      var fmt = p >= 1000 ? '$' + p.toLocaleString('en', {{minimumFractionDigits:2, maximumFractionDigits:2}})
                          : '$' + p.toFixed(p >= 1 ? 4 : 6);
      document.getElementById('cp-price').textContent = fmt;
      var s24 = (c24 >= 0 ? '+' : '') + c24.toFixed(2) + '% (24h)';
      var el24 = document.getElementById('cp-24h');
      el24.textContent = s24;
      el24.className = 'coin-change ' + (c24 >= 0 ? 'coin-up' : 'coin-dn');
      var s7 = (c7 >= 0 ? '+' : '') + c7.toFixed(2) + '% (7d)';
      var el7 = document.getElementById('cp-7d');
      el7.textContent = s7;
      el7.className = 'coin-change ' + (c7 >= 0 ? 'coin-up' : 'coin-dn');
      var mcap = d.MKTCAP >= 1e12 ? '$' + (d.MKTCAP/1e12).toFixed(2) + 'T' : '$' + (d.MKTCAP/1e9).toFixed(2) + 'B';
      var vol = d.VOLUME24HOURTO >= 1e9 ? '$' + (d.VOLUME24HOURTO/1e9).toFixed(2) + 'B' : '$' + (d.VOLUME24HOURTO/1e6).toFixed(2) + 'M';
      document.getElementById('cp-mcap').textContent = mcap;
      document.getElementById('cp-vol').textContent = vol;
      document.getElementById('cp-updated').textContent = 'Last updated: ' + new Date().toUTCString();
    }}).catch(function(){{}});
}}
setInterval(refreshPrice, 60000);
</script>

</body>
</html>"""
    return html

def build_coins_sitemap(coins):
    """Add coin pages to sitemap."""
    today = datetime.now().strftime("%Y-%m-%d")
    urls = "\n".join(
        f"  <url><loc>{SITE_URL}/{c['slug']}.html</loc><lastmod>{today}</lastmod><changefreq>hourly</changefreq><priority>0.9</priority></url>"
        for c in coins
    )
    return urls

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Fetching live coin data...")
    coin_data = fetch_coin_data()

    print("Loading posts index...")
    posts_index = []
    pi_path = OUTPUT_DIR / "posts_index.json"
    if pi_path.exists():
        try:
            posts_index = json.loads(pi_path.read_text())
        except Exception:
            pass

    print(f"Generating {len(COINS)} coin pages...")
    for coin in COINS:
        articles = get_coin_articles(coin["tag"], posts_index)
        html = build_coin_page(coin, coin_data, articles)
        out_path = OUTPUT_DIR / f"{coin['slug']}.html"
        out_path.write_text(html, encoding="utf-8")
        sym = coin["sym"]
        d = coin_data.get(sym, {})
        price = fmt_price(d.get("price", 0))
        chg   = fmt_change(d.get("change24h", 0))
        print(f"  ✓ {coin['name']} ({sym}) — {price} {chg} — {len(articles)} articles")

    print("Done! All coin pages generated.")

if __name__ == "__main__":
    main()
