import os, json, requests
from datetime import datetime, timezone
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────
SITE_URL  = os.environ.get("SITE_URL", "https://marketsnewstoday.info")
SITE_NAME = "Markets News Today"
OUTPUT_DIR = Path("output")

GROQ_API_KEY = (os.environ.get("GROQ_API_KEY_1","") or
                os.environ.get("GROQ_API_KEY_2","") or
                os.environ.get("GROQ_API_KEY_3","") or
                os.environ.get("GROQ_API_KEY_4",""))

COINS = [
    {"slug":"bitcoin",   "sym":"BTC",  "name":"Bitcoin",   "tag":"bitcoin",   "color":"#F7931A","desc":"The world's first and largest cryptocurrency by market cap."},
    {"slug":"ethereum",  "sym":"ETH",  "name":"Ethereum",  "tag":"ethereum",  "color":"#627EEA","desc":"The leading smart contract platform powering DeFi and Web3."},
    {"slug":"solana",    "sym":"SOL",  "name":"Solana",    "tag":"solana",    "color":"#9945FF","desc":"High-performance blockchain known for speed and low fees."},
    {"slug":"xrp",       "sym":"XRP",  "name":"XRP",       "tag":"xrp",       "color":"#00AAE4","desc":"Digital payment protocol focused on fast cross-border transactions."},
    {"slug":"bnb",       "sym":"BNB",  "name":"BNB",       "tag":"bnb",       "color":"#F3BA2F","desc":"Native token of the Binance ecosystem and BNB Chain."},
    {"slug":"dogecoin",  "sym":"DOGE", "name":"Dogecoin",  "tag":"dogecoin",  "color":"#C2A633","desc":"The original meme coin with a strong community and wide adoption."},
    {"slug":"cardano",   "sym":"ADA",  "name":"Cardano",   "tag":"cardano",   "color":"#0033AD","desc":"Proof-of-stake blockchain focused on security and scalability."},
    {"slug":"avalanche", "sym":"AVAX", "name":"Avalanche", "tag":"avalanche", "color":"#E84142","desc":"Fast, low-cost smart contract platform with subnet architecture."},
    {"slug":"chainlink", "sym":"LINK", "name":"Chainlink", "tag":"chainlink", "color":"#2A5ADA","desc":"Decentralized oracle network connecting blockchains to real-world data."},
    {"slug":"polkadot",  "sym":"DOT",  "name":"Polkadot",  "tag":"polkadot",  "color":"#E6007A","desc":"Multi-chain protocol enabling blockchain interoperability."},
]

# ── HELPERS ─────────────────────────────────────────────────────────
def fmt_price(p):
    if p >= 1000: return "$" + f"{p:,.2f}"
    if p >= 1:    return "$" + f"{p:.4f}"
    return "$" + f"{p:.6f}"

def fmt_large(n):
    if n >= 1e12: return "$" + f"{n/1e12:.2f}T"
    if n >= 1e9:  return "$" + f"{n/1e9:.2f}B"
    if n >= 1e6:  return "$" + f"{n/1e6:.2f}M"
    return "$" + f"{n:,.0f}"

def fmt_chg(c):
    return ("+" if c >= 0 else "") + f"{c:.2f}%"

def chg_cls(c):
    return "coin-up" if c >= 0 else "coin-dn"

# ── GROQ ─────────────────────────────────────────────────────────────
def groq_ask(prompt, max_tokens=300, temp=0.6):
    if not GROQ_API_KEY:
        return ""
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": "Bearer " + GROQ_API_KEY, "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "max_tokens": max_tokens,
                  "temperature": temp, "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        resp = r.json()
        if "choices" in resp:
            return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("  Groq error:", e)
    return ""

def get_sentiment(name, sym, price, chg24, chg7, vol):
    prompt = (
        "You are a crypto sentiment analyst. Based on this data for " + name + " (" + sym + "):\n"
        "Price=$" + f"{price:,.2f}" + ", 24h=" + fmt_chg(chg24) + ", 7d=" + fmt_chg(chg7) + ", Vol=" + fmt_large(vol) + "\n\n"
        'Respond ONLY in this exact JSON format:\n{"score":<0-100>,"label":"<Extreme Fear|Fear|Neutral|Greed|Extreme Greed>","reason":"<max 12 words>"}'
    )
    raw = groq_ask(prompt, max_tokens=80, temp=0.3)
    try:
        raw = raw.strip().strip("`").replace("json","").strip()
        d = json.loads(raw)
        return int(d.get("score",50)), str(d.get("label","Neutral")), str(d.get("reason",""))
    except:
        if chg24 > 5:   return 75, "Greed", "Strong upward momentum"
        elif chg24 > 2: return 62, "Greed", "Positive price action"
        elif chg24 > 0: return 55, "Neutral", "Slight bullish bias"
        elif chg24 > -2:return 45, "Neutral", "Slight bearish pressure"
        elif chg24 > -5:return 35, "Fear", "Negative price action"
        else:           return 20, "Extreme Fear", "Heavy selling pressure"

def get_verdict(name, sym, price, chg24, chg7, high, low):
    prompt = (
        "You are a crypto trading advisor. Give a daily verdict for " + name + " (" + sym + ").\n"
        "Price=$" + f"{price:,.2f}" + ", 24h=" + fmt_chg(chg24) + ", 7d=" + fmt_chg(chg7) +
        ", High=$" + f"{high:,.2f}" + ", Low=$" + f"{low:,.2f}" + "\n\n"
        'Respond ONLY in this exact JSON format:\n{"action":"<BUY|HOLD|WAIT|SELL>","confidence":"<High|Medium|Low>","risk":"<Low|Medium|High|Very High>","reason":"<2 sentences plain text>","target":"<price>","stop":"<price>"}'
    )
    raw = groq_ask(prompt, max_tokens=150, temp=0.4)
    try:
        raw = raw.strip().strip("`").replace("json","").strip()
        return json.loads(raw)
    except:
        act = "HOLD"
        if chg24 > 3: act = "BUY"
        elif chg24 < -3: act = "WAIT"
        return {"action":act,"confidence":"Medium","risk":"Medium",
                "reason":name+" is showing " + ("positive" if chg24>=0 else "negative") + " momentum. Monitor key levels carefully.",
                "target":fmt_price(price*1.05),"stop":fmt_price(price*0.95)}

def get_analysis(name, sym, price, chg24, chg7, mcap, high, low, vol):
    prompt = (
        "You are a professional crypto analyst. Write 120-150 word technical analysis for " + name + " (" + sym + ").\n"
        "Price=$" + f"{price:,.2f}" + ", 24h=" + fmt_chg(chg24) + ", 7d=" + fmt_chg(chg7) +
        ", MCap=" + fmt_large(mcap) + ", High=$" + f"{high:,.2f}" + ", Low=$" + f"{low:,.2f}" + "\n\n"
        "Include: momentum, key support/resistance, short-term outlook.\n"
        "Plain text only. No markdown. No bullets. Direct analyst voice."
    )
    return groq_ask(prompt, max_tokens=250, temp=0.6)

def get_weekly_digest(coins_data, all_coins):
    performers = []
    for coin in all_coins:
        d = coins_data.get(coin["sym"], {})
        performers.append((coin["name"], coin["sym"], d.get("change7d",0), d.get("price",0)))
    performers.sort(key=lambda x: x[2], reverse=True)
    best  = ", ".join(n+"("+s+"): "+fmt_chg(c) for n,s,c,p in performers[:3])
    worst = ", ".join(n+"("+s+"): "+fmt_chg(c) for n,s,c,p in performers[-3:])
    prompt = (
        "Write a 150-word weekly crypto digest for " + datetime.now(timezone.utc).strftime("%B %d, %Y") + ".\n"
        "Top performers: " + best + "\nWorst: " + worst + "\n\n"
        "3 short paragraphs: market mood, key movers, what to watch. Plain text only."
    )
    return groq_ask(prompt, max_tokens=300, temp=0.7)

# ── DATA FETCH ───────────────────────────────────────────────────────
def fetch_coins():
    syms = ",".join(c["sym"] for c in COINS)
    try:
        r = requests.get("https://min-api.cryptocompare.com/data/pricemultifull",
                         params={"fsyms":syms,"tsyms":"USD"}, timeout=10)
        raw = r.json().get("RAW",{})
        out = {}
        for sym, info in raw.items():
            u = info.get("USD",{})
            out[sym] = {
                "price":    u.get("PRICE",0),
                "change24h":u.get("CHANGEPCT24HOUR",0),
                "change7d": u.get("CHANGEPCT7D",0),
                "marketcap":u.get("MKTCAP",0),
                "volume24h":u.get("VOLUME24HOURTO",0),
                "high24h":  u.get("HIGH24HOUR",0),
                "low24h":   u.get("LOW24HOUR",0),
                "supply":   u.get("SUPPLY",0),
            }
        return out
    except Exception as e:
        print("  Fetch error:", e)
        return {}

def get_articles(tag, posts_index):
    arts = [p for p in posts_index if p.get("coin_tag","") == tag]
    arts.sort(key=lambda x: x.get("date_iso",""), reverse=True)
    return arts[:20]

# ── NAV / FOOT ───────────────────────────────────────────────────────
def nav_html():
    d = datetime.now().strftime("%A, %B %d, %Y")
    lines = []
    lines.append('<div class="topbar"><div class="topbar-inner">')
    lines.append('  <span class="topbar-left">' + d + '</span>')
    lines.append('  <a href="../" class="topbar-logo">Markets <span class="accent">News</span> Today</a>')
    lines.append('  <span class="topbar-right">Crypto &middot; AI &middot; Stocks</span>')
    lines.append('</div></div>')
    lines.append('<nav class="navbar"><div class="navbar-wrap"><div class="navbar-inner">')
    lines.append('  <a href="../" class="nav-link">Home</a>')
    lines.append('  <div class="nav-dropdown">')
    lines.append('    <a href="../crypto.html" class="nav-link nav-dropdown-trigger">Crypto &#9662;</a>')
    lines.append('    <div class="nav-dropdown-menu">')
    lines.append('      <div class="nav-dropdown-col"><span class="nav-dropdown-head">Top Coins</span>')
    for c in COINS:
        lines.append('        <a href="../' + c["slug"] + '.html">' + c["name"] + ' (' + c["sym"] + ')</a>')
    lines.append('      </div>')
    lines.append('      <div class="nav-dropdown-col"><span class="nav-dropdown-head">Topics</span>')
    lines.append('        <a href="../crypto.html">All Crypto</a>')
    lines.append('        <a href="../defi.html">DeFi</a>')
    lines.append('        <a href="../blockchain.html">Blockchain</a>')
    lines.append('        <a href="../web3.html">Web3</a>')
    lines.append('      </div>')
    lines.append('    </div>')
    lines.append('  </div>')
    lines.append('  <div class="nav-dropdown">')
    lines.append('    <a href="../ai.html" class="nav-link nav-dropdown-trigger">AI &#9662;</a>')
    lines.append('    <div class="nav-dropdown-menu"><div class="nav-dropdown-col"><span class="nav-dropdown-head">AI Coverage</span>')
    lines.append('      <a href="../ai.html">All AI News</a>')
    lines.append('      <a href="../technology.html">Technology</a>')
    lines.append('    </div></div>')
    lines.append('  </div>')
    lines.append('  <div class="nav-dropdown">')
    lines.append('    <a href="../stocks.html" class="nav-link nav-dropdown-trigger">Stocks &#9662;</a>')
    lines.append('    <div class="nav-dropdown-menu"><div class="nav-dropdown-col"><span class="nav-dropdown-head">Markets</span>')
    lines.append('      <a href="../stocks.html">Stocks</a>')
    lines.append('      <a href="../markets-news.html">Markets</a>')
    lines.append('      <a href="../forex.html">Forex</a>')
    lines.append('      <a href="../investing.html">Investing</a>')
    lines.append('      <a href="../economy.html">Economy</a>')
    lines.append('      <a href="../finance.html">Finance</a>')
    lines.append('    </div></div>')
    lines.append('  </div>')
    lines.append('  <a href="../markets.html" class="nav-link">Live Markets</a>')
    lines.append('</div></div></nav>')
    lines.append('<script>(function(){var dd=document.querySelectorAll(".nav-dropdown");dd.forEach(function(d){var t=d.querySelector(".nav-dropdown-trigger");if(!t)return;t.addEventListener("click",function(e){var m=window.innerWidth<=768;if(!m)return;e.preventDefault();e.stopPropagation();var a=d.classList.contains("active");dd.forEach(function(x){x.classList.remove("active")});if(!a)d.classList.add("active")})});document.addEventListener("click",function(){dd.forEach(function(d){d.classList.remove("active")})})})();</script>')
    return "\n".join(lines)

def foot_html():
    y = datetime.now().year
    lines = []
    lines.append('<footer class="footer"><div class="footer-top"><div class="container"><div class="footer-grid">')
    lines.append('  <div class="footer-brand"><div class="footer-logo">Markets <span class="accent">News</span> Today</div>')
    lines.append('  <p>Your trusted source for crypto, AI, stocks and financial market analysis.</p></div>')
    lines.append('  <div class="footer-col"><h4>Crypto</h4>')
    lines.append('    <a href="../crypto.html">All Crypto</a>')
    for c in COINS[:5]:
        lines.append('    <a href="../' + c["slug"] + '.html">' + c["name"] + '</a>')
    lines.append('  </div>')
    lines.append('  <div class="footer-col"><h4>Coins</h4>')
    for c in COINS[5:]:
        lines.append('    <a href="../' + c["slug"] + '.html">' + c["name"] + '</a>')
    lines.append('  </div>')
    lines.append('  <div class="footer-col"><h4>Markets</h4>')
    lines.append('    <a href="../markets.html">Live Markets</a>')
    lines.append('    <a href="../stocks.html">Stocks</a>')
    lines.append('    <a href="../forex.html">Forex</a>')
    lines.append('    <a href="../finance.html">Finance</a>')
    lines.append('    <a href="../investing.html">Investing</a>')
    lines.append('  </div>')
    lines.append('  <div class="footer-col"><h4>Technology</h4>')
    lines.append('    <a href="../ai.html">AI</a>')
    lines.append('    <a href="../technology.html">Technology</a>')
    lines.append('    <a href="../blockchain.html">Blockchain</a>')
    lines.append('    <a href="../defi.html">DeFi</a>')
    lines.append('    <a href="../web3.html">Web3</a>')
    lines.append('  </div>')
    lines.append('  <div class="footer-col"><h4>Company</h4>')
    lines.append('    <a href="../about.html">About Us</a>')
    lines.append('    <a href="../contact.html">Contact</a>')
    lines.append('    <a href="../privacy-policy.html">Privacy Policy</a>')
    lines.append('    <a href="../sitemap.xml">Sitemap</a>')
    lines.append('  </div>')
    lines.append('</div></div></div>')
    lines.append('<div class="footer-btm"><div class="container">&copy; ' + str(y) + ' Markets News Today. All rights reserved.</div></div>')
    lines.append('</footer>')
    return "\n".join(lines)

# ── BUILD COIN PAGE ──────────────────────────────────────────────────
def build_coin_page(coin, coin_data, articles):
    sym   = coin["sym"]
    name  = coin["name"]
    slug  = coin["slug"]
    color = coin["color"]
    desc  = coin["desc"]

    d         = coin_data.get(sym, {})
    price     = d.get("price", 0)
    chg24     = d.get("change24h", 0)
    chg7      = d.get("change7d", 0)
    mcap      = d.get("marketcap", 0)
    vol       = d.get("volume24h", 0)
    high      = d.get("high24h", 0)
    low       = d.get("low24h", 0)
    supply    = d.get("supply", 0)

    price_s   = fmt_price(price)
    chg24_s   = fmt_chg(chg24)
    chg7_s    = fmt_chg(chg7)
    mcap_s    = fmt_large(mcap)
    vol_s     = fmt_large(vol)
    high_s    = fmt_price(high)
    low_s     = fmt_price(low)
    supply_s  = fmt_large(supply) if supply > 0 else "N/A"
    chg24_cls = chg_cls(chg24)
    chg7_cls  = chg_cls(chg7)
    now_s     = datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC")
    now_iso   = datetime.now(timezone.utc).isoformat()
    today     = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── AI FEATURES ─────────────────────────────────────────────────
    print("    Generating AI features for " + name + "...")
    s_score, s_label, s_reason = get_sentiment(name, sym, price, chg24, chg7, vol)
    verdict   = get_verdict(name, sym, price, chg24, chg7, high, low)
    analysis  = get_analysis(name, sym, price, chg24, chg7, mcap, high, low, vol)

    if   s_score >= 75: s_color = "#16a34a"
    elif s_score >= 55: s_color = "#65a30d"
    elif s_score >= 45: s_color = "#ca8a04"
    elif s_score >= 25: s_color = "#ea580c"
    else:               s_color = "#dc2626"

    v_act  = verdict.get("action","HOLD")
    v_conf = verdict.get("confidence","Medium")
    v_risk = verdict.get("risk","Medium")
    v_why  = verdict.get("reason","")
    v_tgt  = str(verdict.get("target","N/A"))
    v_stp  = str(verdict.get("stop","N/A"))
    v_clrs = {"BUY":"#16a34a","HOLD":"#2563eb","WAIT":"#ca8a04","SELL":"#dc2626"}
    v_color = v_clrs.get(v_act, "#2563eb")

    # ── SCHEMA ──────────────────────────────────────────────────────
    schema = json.dumps({
        "@context":"https://schema.org",
        "@type":["WebPage","FinancialProduct"],
        "name": name + " (" + sym + ") Price Today — " + price_s,
        "description": "Live " + name + " price " + price_s + " (" + chg24_s + " 24h). Market cap " + mcap_s + ". Latest news, AI analysis and daily verdict.",
        "url": SITE_URL + "/" + slug + ".html",
        "dateModified": now_iso,
        "inLanguage":"en-US",
        "isAccessibleForFree":True,
        "mainEntityOfPage":{"@type":"WebPage","@id": SITE_URL + "/" + slug + ".html"},
        "publisher":{"@type":"NewsMediaOrganization","name":SITE_NAME,"url":SITE_URL,
                     "logo":{"@type":"ImageObject","url":SITE_URL+"/favicon.png","width":512,"height":512}}
    })

    breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":SITE_URL},
            {"@type":"ListItem","position":2,"name":"Crypto","item":SITE_URL+"/crypto.html"},
            {"@type":"ListItem","position":3,"name":name+" Price","item":SITE_URL+"/"+slug+".html"}
        ]
    })

    faq_schema = json.dumps({
        "@context":"https://schema.org","@type":"FAQPage",
        "mainEntity":[
            {"@type":"Question","name":"What is the "+name+" price today?",
             "acceptedAnswer":{"@type":"Answer","text":name+" ("+sym+") is trading at "+price_s+" today, "+chg24_s+" in the last 24 hours. Market cap is "+mcap_s+"."}},
            {"@type":"Question","name":"Should I buy "+name+" today?",
             "acceptedAnswer":{"@type":"Answer","text":"Our AI verdict for "+name+" is: "+v_act+" (Confidence: "+v_conf+", Risk: "+v_risk+"). "+v_why+" Not financial advice."}},
            {"@type":"Question","name":"What is the "+name+" market sentiment?",
             "acceptedAnswer":{"@type":"Answer","text":name+" sentiment score is "+str(s_score)+"/100 — "+s_label+". "+s_reason}}
        ]
    })

    # ── ARTICLES HTML ────────────────────────────────────────────────
    if articles:
        cards = []
        for a in articles:
            img = a.get("image_url","") or "https://picsum.photos/seed/"+a["slug"]+"/400/240"
            cards.append(
                '<div class="coin-article-card">'
                '<a href="../posts/'+a["slug"]+'.html"><img src="'+img+'" alt="'+a["title"]+'" loading="lazy" width="400" height="240"></a>'
                '<div class="coin-article-info">'
                '<span class="coin-article-date">'+a.get("date_human","")+'</span>'
                '<h3><a href="../posts/'+a["slug"]+'.html">'+a["title"]+'</a></h3>'
                '<p>'+a.get("excerpt","")[:120]+'...</p>'
                '<a href="../posts/'+a["slug"]+'.html" class="coin-article-read">Read More &rarr;</a>'
                '</div></div>'
            )
        art_html = (
            '<section class="coin-articles"><div class="container">'
            '<div class="coin-articles-hdr"><h2>Latest '+name+' News &amp; Analysis</h2></div>'
            '<div class="coin-articles-grid">' + "\n".join(cards) + '</div>'
            '</div></section>'
        )
    else:
        art_html = (
            '<section class="coin-articles"><div class="container">'
            '<div class="coin-articles-hdr"><h2>Latest '+name+' News &amp; Analysis</h2></div>'
            '<p style="color:#888;padding:24px 0">No articles yet. Check back soon.</p>'
            '</div></section>'
        )

    # ── AI ANALYSIS BOX ──────────────────────────────────────────────
    if analysis:
        ai_box = (
            '<div style="max-width:1200px;margin:0 auto 32px;padding:0 20px">'
            '<div style="background:linear-gradient(135deg,#fff8f8,#fff);border:1px solid #f0d0d0;border-left:5px solid '+color+';border-radius:10px;padding:24px 28px">'
            '<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">'
            '<span style="font-size:20px">🤖</span>'
            '<div><div style="font-size:13px;font-weight:700;color:'+color+';text-transform:uppercase;letter-spacing:0.5px">AI Market Analysis</div>'
            '<div style="font-size:11px;color:#aaa">Updated '+now_s+' &middot; Markets News Today AI</div></div></div>'
            '<p style="font-size:15px;line-height:1.8;color:#333;margin:0">'+analysis+'</p>'
            '<p style="font-size:11px;color:#bbb;margin:12px 0 0;font-style:italic">AI-generated for informational purposes only. Not financial advice.</p>'
            '</div></div>'
        )
    else:
        ai_box = ""

    # ── ASSEMBLE PAGE ────────────────────────────────────────────────
    parts = []
    parts.append('<!DOCTYPE html>')
    parts.append('<html lang="en">')
    parts.append('<head>')
    parts.append('<meta charset="UTF-8">')
    parts.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    parts.append('<title>'+name+' ('+sym+') Price Today, News &amp; Analysis | '+SITE_NAME+'</title>')
    parts.append('<meta name="description" content="Live '+name+' price '+price_s+', '+chg24_s+' (24h). Market cap '+mcap_s+'. Latest '+name+' news, AI analysis and daily verdict.">')
    parts.append('<meta property="og:title" content="'+name+' Price Today — '+price_s+' '+chg24_s+'">')
    parts.append('<meta property="og:url" content="'+SITE_URL+'/'+slug+'.html">')
    parts.append('<meta property="og:type" content="website">')
    parts.append('<meta name="twitter:card" content="summary_large_image">')
    parts.append('<meta name="robots" content="index,follow">')
    parts.append('<link rel="canonical" href="'+SITE_URL+'/'+slug+'.html">')
    parts.append('<link rel="stylesheet" href="../style.css">')
    parts.append('<script type="application/ld+json">'+schema+'</script>')
    parts.append('<script type="application/ld+json">'+breadcrumb+'</script>')
    parts.append('<script type="application/ld+json">'+faq_schema+'</script>')
    parts.append('<style>')
    parts.append('.coin-hero{background:linear-gradient(135deg,'+color+'15 0%,#fff 60%);border-bottom:1px solid #eee;padding:40px 0 32px}')
    parts.append('.coin-hero-inner{max-width:1200px;margin:0 auto;padding:0 20px}')
    parts.append('.coin-hero-top{display:flex;align-items:center;gap:16px;margin-bottom:24px}')
    parts.append('.coin-icon{width:56px;height:56px;border-radius:50%;background:'+color+'20;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:700;color:'+color+';border:2px solid '+color+'40}')
    parts.append('.coin-name{font-size:28px;font-weight:800;color:var(--dark)}.coin-sym{font-size:14px;color:#888;margin-left:8px;font-weight:500}')
    parts.append('.coin-price{font-size:42px;font-weight:800;color:var(--dark);margin-bottom:8px}')
    parts.append('.coin-up{color:#16a34a}.coin-dn{color:#dc2626}')
    parts.append('.coin-change{font-size:18px;font-weight:600}.coin-updated{font-size:11px;color:#aaa;margin-top:6px}')
    parts.append('.coin-stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-top:28px}')
    parts.append('.coin-stat{background:#fff;border:1px solid #eee;border-radius:10px;padding:14px 16px}')
    parts.append('.coin-stat-label{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px}')
    parts.append('.coin-stat-value{font-size:18px;font-weight:700;color:var(--dark)}')
    parts.append('.coin-about{max-width:1200px;margin:32px auto;padding:0 20px}')
    parts.append('.coin-about h2{font-size:22px;font-weight:700;margin-bottom:12px;color:var(--dark);border-left:4px solid '+color+';padding-left:12px}')
    parts.append('.coin-about p{font-size:16px;line-height:1.8;color:#444}')
    parts.append('.coin-articles{padding:40px 0;background:#fafafa}')
    parts.append('.coin-articles-hdr h2{font-size:24px;font-weight:800;margin-bottom:24px;color:var(--dark)}')
    parts.append('.coin-articles-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px}')
    parts.append('.coin-article-card{background:#fff;border-radius:10px;overflow:hidden;border:1px solid #eee;transition:box-shadow 0.2s}')
    parts.append('.coin-article-card:hover{box-shadow:0 4px 20px rgba(0,0,0,0.08)}')
    parts.append('.coin-article-card img{width:100%;height:180px;object-fit:cover}')
    parts.append('.coin-article-info{padding:16px}.coin-article-date{font-size:11px;color:#aaa}')
    parts.append('.coin-article-info h3{font-size:16px;font-weight:700;margin:6px 0 8px;line-height:1.4}')
    parts.append('.coin-article-info h3 a{color:var(--dark);text-decoration:none}.coin-article-info h3 a:hover{color:var(--red)}')
    parts.append('.coin-article-info p{font-size:13px;color:#666;line-height:1.6;margin-bottom:12px}')
    parts.append('.coin-article-read{font-size:12px;font-weight:600;color:var(--red);text-decoration:none}')
    parts.append('@media(max-width:600px){.coin-price{font-size:30px}.coin-name{font-size:22px}.coin-stats-grid{grid-template-columns:repeat(2,1fr)}}')
    parts.append('</style>')
    parts.append('</head>')
    parts.append('<body>')
    parts.append(nav_html())

    # Hero
    parts.append('<div class="coin-hero"><div class="coin-hero-inner">')
    parts.append('<div class="coin-hero-top">')
    parts.append('<div class="coin-icon">'+sym[0]+'</div>')
    parts.append('<div><div><span class="coin-name">'+name+'</span><span class="coin-sym">'+sym+'</span></div>')
    parts.append('<div style="font-size:13px;color:#888">'+desc+'</div></div>')
    parts.append('</div>')
    parts.append('<div class="coin-price" id="cp-price">'+price_s+'</div>')
    parts.append('<div>')
    parts.append('<span class="coin-change '+chg24_cls+'" id="cp-24h">'+chg24_s+' (24h)</span>&nbsp;&nbsp;')
    parts.append('<span class="coin-change '+chg7_cls+'" id="cp-7d" style="font-size:15px">'+chg7_s+' (7d)</span>')
    parts.append('</div>')
    parts.append('<div class="coin-updated" id="cp-updated">Last updated: '+now_s+'</div>')
    parts.append('<div class="coin-stats-grid">')
    parts.append('<div class="coin-stat"><div class="coin-stat-label">Market Cap</div><div class="coin-stat-value" id="cp-mcap">'+mcap_s+'</div></div>')
    parts.append('<div class="coin-stat"><div class="coin-stat-label">24h Volume</div><div class="coin-stat-value" id="cp-vol">'+vol_s+'</div></div>')
    parts.append('<div class="coin-stat"><div class="coin-stat-label">24h High</div><div class="coin-stat-value">'+high_s+'</div></div>')
    parts.append('<div class="coin-stat"><div class="coin-stat-label">24h Low</div><div class="coin-stat-value">'+low_s+'</div></div>')
    parts.append('<div class="coin-stat"><div class="coin-stat-label">Circulating Supply</div><div class="coin-stat-value">'+supply_s+'</div></div>')
    parts.append('</div>')
    parts.append('</div></div>')

    # Sentiment + Verdict row
    parts.append('<div style="max-width:1200px;margin:24px auto 0;padding:0 20px;display:grid;grid-template-columns:1fr 1fr;gap:16px">')
    # Sentiment
    parts.append('<div style="background:#fff;border:1px solid #eee;border-radius:12px;padding:20px 24px">')
    parts.append('<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:#888;margin-bottom:12px">'+name+' Sentiment Index</div>')
    parts.append('<div style="display:flex;align-items:center;gap:16px">')
    parts.append('<div style="width:64px;height:64px;border-radius:50%;background:'+s_color+'20;border:3px solid '+s_color+';display:flex;align-items:center;justify-content:center;flex-shrink:0">')
    parts.append('<span style="font-size:20px;font-weight:800;color:'+s_color+'">'+str(s_score)+'</span></div>')
    parts.append('<div><div style="font-size:18px;font-weight:700;color:'+s_color+'">'+s_label+'</div>')
    parts.append('<div style="font-size:13px;color:#666;margin-top:3px">'+s_reason+'</div></div>')
    parts.append('</div>')
    parts.append('<div style="margin-top:12px;height:6px;background:#f0f0f0;border-radius:3px;overflow:hidden">')
    parts.append('<div style="width:'+str(s_score)+'%;height:100%;background:'+s_color+';border-radius:3px"></div></div>')
    parts.append('<div style="display:flex;justify-content:space-between;font-size:10px;color:#bbb;margin-top:4px"><span>Extreme Fear</span><span>Neutral</span><span>Extreme Greed</span></div>')
    parts.append('</div>')
    # Verdict
    parts.append('<div style="background:#fff;border:2px solid '+v_color+';border-radius:12px;padding:20px 24px">')
    parts.append('<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:#888;margin-bottom:12px">Should I Buy '+name+' Today?</div>')
    parts.append('<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">')
    parts.append('<div style="background:'+v_color+';color:#fff;font-size:22px;font-weight:800;padding:8px 20px;border-radius:8px;letter-spacing:1px">'+v_act+'</div>')
    parts.append('<div><div style="font-size:13px;color:#333">Confidence: <strong>'+v_conf+'</strong></div>')
    parts.append('<div style="font-size:13px;color:#333">Risk: <strong style="color:'+v_color+'">'+v_risk+'</strong></div></div>')
    parts.append('</div>')
    parts.append('<p style="font-size:13px;color:#555;line-height:1.6;margin:0 0 10px">'+v_why+'</p>')
    parts.append('<div style="display:flex;gap:16px;font-size:12px">')
    parts.append('<span style="color:#16a34a">🎯 Target: <strong>'+v_tgt+'</strong></span>')
    parts.append('<span style="color:#dc2626">🛡 Stop: <strong>'+v_stp+'</strong></span>')
    parts.append('</div>')
    parts.append('<p style="font-size:10px;color:#bbb;margin:10px 0 0;font-style:italic">Not financial advice. For informational purposes only.</p>')
    parts.append('</div>')
    parts.append('</div>')

    # TradingView Chart
    parts.append('<div style="max-width:1200px;margin:32px auto;padding:0 20px">')
    parts.append('<div style="border:1px solid #eee;border-radius:10px;overflow:hidden">')
    parts.append('<div id="tv_'+sym.lower()+'"></div>')
    parts.append('<script src="https://s3.tradingview.com/tv.js"></script>')
    parts.append('<script>new TradingView.widget({"width":"100%","height":400,"symbol":"BINANCE:'+sym+'USDT","interval":"D","timezone":"Etc/UTC","theme":"light","style":"1","locale":"en","toolbar_bg":"#f1f3f6","enable_publishing":false,"container_id":"tv_'+sym.lower()+'"});</script>')
    parts.append('</div></div>')

    # About
    parts.append('<div class="coin-about"><h2>About '+name+'</h2>')
    parts.append('<p>'+desc+' '+name+' ('+sym+') is one of the most actively traded cryptocurrencies, with a 24-hour trading volume of '+vol_s+' and a market cap of '+mcap_s+'. Follow the latest '+name+' news and expert analysis below.</p>')
    parts.append('</div>')

    # AI Analysis
    if ai_box:
        parts.append(ai_box)

    # Articles
    parts.append(art_html)

    # Live refresh JS
    parts.append('<script>')
    # Live price refresh using CryptoCompare
    parts.append('<script>')
    parts.append('<script>')
    parts.append('async function refreshPrice(){')
    parts.append('  try{')
    parts.append('    var r=await fetch("https://min-api.cryptocompare.com/data/pricemultifull?fsyms='+sym+'&tsyms=USD");')
    parts.append('    var j=await r.json();')
    parts.append('    var d=j.RAW&&j.RAW.'+sym+'&&j.RAW.'+sym+'.USD;')
    parts.append('    if(!d||!d.PRICE)throw new Error("no data");')
    parts.append('    var p=d.PRICE;')
    parts.append('    var f=p>=1000?"$"+p.toLocaleString("en",{minimumFractionDigits:2,maximumFractionDigits:2}):"$"+p.toFixed(p>=1?4:6);')
    parts.append('    document.getElementById("cp-price").textContent=f;')
    parts.append('    var c=d.CHANGEPCT24HOUR||0;')
    parts.append('    var s=(c>=0?"+":"")+c.toFixed(2)+"% (24h)";')
    parts.append('    var e24=document.getElementById("cp-24h");if(e24){e24.textContent=s;e24.className="coin-change "+(c>=0?"coin-up":"coin-dn");}')
    parts.append('    var c7=d.CHANGEPCT7D||0;var s7=(c7>=0?"+":"")+c7.toFixed(2)+"% (7d)";')
    parts.append('    var e7=document.getElementById("cp-7d");if(e7){e7.textContent=s7;e7.className="coin-change "+(c7>=0?"coin-up":"coin-dn");}')
    parts.append('    var mc=d.MKTCAP>=1e12?"$"+(d.MKTCAP/1e12).toFixed(2)+"T":d.MKTCAP>=1e9?"$"+(d.MKTCAP/1e9).toFixed(2)+"B":"$"+(d.MKTCAP/1e6).toFixed(2)+"M";')
    parts.append('    var vo=d.TOTALVOLUME24HTO>=1e9?"$"+(d.TOTALVOLUME24HTO/1e9).toFixed(2)+"B":"$"+(d.TOTALVOLUME24HTO/1e6).toFixed(2)+"M";')
    parts.append('    var hi=p>=1000?"$"+d.HIGH24HOUR.toLocaleString("en",{minimumFractionDigits:2,maximumFractionDigits:2}):"$"+d.HIGH24HOUR.toFixed(4);')
    parts.append('    var lo=p>=1000?"$"+d.LOW24HOUR.toLocaleString("en",{minimumFractionDigits:2,maximumFractionDigits:2}):"$"+d.LOW24HOUR.toFixed(4);')
    parts.append('    var em=document.getElementById("cp-mcap");if(em)em.textContent=mc;')
    parts.append('    var ev=document.getElementById("cp-vol");if(ev)ev.textContent=vo;')
    parts.append('    var eh=document.getElementById("cp-high");if(eh)eh.textContent=hi;')
    parts.append('    var el2=document.getElementById("cp-low");if(el2)el2.textContent=lo;')
    parts.append('    document.getElementById("cp-updated").textContent="Last updated: "+new Date().toUTCString();')
    parts.append('  }catch(e){')
    parts.append('    try{')
    parts.append('      var r2=await fetch("https://api.binance.com/api/v3/ticker/24hr?symbol='+sym+'USDT");')
    parts.append('      var d2=await r2.json();')
    parts.append('      if(!d2.lastPrice)return;')
    parts.append('      var p2=parseFloat(d2.lastPrice);')
    parts.append('      var f2=p2>=1000?"$"+p2.toLocaleString("en",{minimumFractionDigits:2,maximumFractionDigits:2}):"$"+p2.toFixed(p2>=1?4:6);')
    parts.append('      document.getElementById("cp-price").textContent=f2;')
    parts.append('      var c2=parseFloat(d2.priceChangePercent)||0;')
    parts.append('      var s2=(c2>=0?"+":"")+c2.toFixed(2)+"% (24h)";')
    parts.append('      var e2=document.getElementById("cp-24h");if(e2){e2.textContent=s2;e2.className="coin-change "+(c2>=0?"coin-up":"coin-dn");}')
    parts.append('      var v2=parseFloat(d2.quoteVolume);var vs2=v2>=1e9?"$"+(v2/1e9).toFixed(2)+"B":"$"+(v2/1e6).toFixed(2)+"M";')
    parts.append('      var ev2=document.getElementById("cp-vol");if(ev2)ev2.textContent=vs2;')
    parts.append('      var h2=parseFloat(d2.highPrice);var l2=parseFloat(d2.lowPrice);')
    parts.append('      var eh2=document.getElementById("cp-high");if(eh2)eh2.textContent=h2>=1000?"$"+h2.toLocaleString("en",{minimumFractionDigits:2,maximumFractionDigits:2}):"$"+h2.toFixed(4);')
    parts.append('      var el3=document.getElementById("cp-low");if(el3)el3.textContent=l2>=1000?"$"+l2.toLocaleString("en",{minimumFractionDigits:2,maximumFractionDigits:2}):"$"+l2.toFixed(4);')
    parts.append('      document.getElementById("cp-updated").textContent="Last updated: "+new Date().toUTCString();')
    parts.append('    }catch(e2){}')
    parts.append('  }')
    parts.append('}')
    parts.append('refreshPrice();setInterval(refreshPrice,30000);')
    parts.append('</script>')
    parts.append('try{')
    parts.append('var r=await fetch("https://min-api.cryptocompare.com/data/pricemultifull?fsyms='+sym+'&tsyms=USD");')
    parts.append('var j=await r.json();')
    parts.append('var d=j.RAW&&j.RAW.'+sym+'&&j.RAW.'+sym+'.USD;')
    parts.append('if(!d)return;')
    parts.append('var p=d.PRICE;')
    parts.append('var f=p>=1000?"$"+p.toLocaleString("en",{minimumFractionDigits:2,maximumFractionDigits:2}):"$"+p.toFixed(p>=1?4:6);')
    parts.append('document.getElementById("cp-price").textContent=f;')
    parts.append('var c=d.CHANGEPCT24HOUR;')
    parts.append('var s=(c>=0?"+":"")+c.toFixed(2)+"% (24h)";')
    parts.append('var e=document.getElementById("cp-24h");e.textContent=s;e.className="coin-change "+(c>=0?"coin-up":"coin-dn");')
    parts.append('var c7=d.CHANGEPCT7D||0;')
    parts.append('var s7=(c7>=0?"+":"")+c7.toFixed(2)+"% (7d)";')
    parts.append('var e7=document.getElementById("cp-7d");if(e7){e7.textContent=s7;e7.className="coin-change "+(c7>=0?"coin-up":"coin-dn");}')
    parts.append('var mc=d.MKTCAP>=1e12?"$"+(d.MKTCAP/1e12).toFixed(2)+"T":"$"+(d.MKTCAP/1e9).toFixed(2)+"B";')
    parts.append('var vo=d.VOLUME24HOURTO>=1e9?"$"+(d.VOLUME24HOURTO/1e9).toFixed(2)+"B":"$"+(d.VOLUME24HOURTO/1e6).toFixed(2)+"M";')
    parts.append('var hi=p>=1000?"$"+d.HIGH24HOUR.toLocaleString("en",{minimumFractionDigits:2,maximumFractionDigits:2}):"$"+d.HIGH24HOUR.toFixed(4);')
    parts.append('var lo=p>=1000?"$"+d.LOW24HOUR.toLocaleString("en",{minimumFractionDigits:2,maximumFractionDigits:2}):"$"+d.LOW24HOUR.toFixed(4);')
    parts.append('var em=document.getElementById("cp-mcap");if(em)em.textContent=mc;')
    parts.append('var ev=document.getElementById("cp-vol");if(ev)ev.textContent=vo;')
    parts.append('var eh=document.getElementById("cp-high");if(eh)eh.textContent=hi;')
    parts.append('var el=document.getElementById("cp-low");if(el)el.textContent=lo;')
    parts.append('document.getElementById("cp-updated").textContent="Last updated: "+new Date().toUTCString();')
    parts.append('}catch(e){}')
    parts.append('}')
    parts.append('refreshPrice();setInterval(refreshPrice,60000);')
    parts.append('</script>')

    parts.append(foot_html())
    parts.append('</body></html>')

    return "\n".join(parts)

# ── WEEKLY DIGEST ────────────────────────────────────────────────────
def build_weekly_digest(coin_data, posts_index):
    now_utc = datetime.now(timezone.utc)
    if now_utc.weekday() != 0:
        print("  Weekly digest skipped (not Monday)")
        return

    today_slug = now_utc.strftime("%Y-%m-%d")
    digest_slug = "weekly-crypto-digest-" + today_slug
    digest_path = OUTPUT_DIR / "posts" / (digest_slug + ".html")
    if digest_path.exists():
        print("  Weekly digest already exists for today")
        return

    print("  Generating weekly crypto digest...")
    text = get_weekly_digest(coin_data, COINS)
    if not text:
        return

    date_human = now_utc.strftime("%B %d, %Y")
    date_iso   = now_utc.isoformat()

    parts = []
    parts.append('<!DOCTYPE html><html lang="en"><head>')
    parts.append('<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    parts.append('<title>Weekly Crypto Digest ' + date_human + ' | ' + SITE_NAME + '</title>')
    parts.append('<meta name="description" content="Weekly crypto market digest for ' + date_human + '. Top performers, key movers and what to watch.">')
    parts.append('<link rel="canonical" href="' + SITE_URL + '/posts/' + digest_slug + '.html">')
    parts.append('<link rel="stylesheet" href="../style.css">')
    parts.append('</head><body>')
    parts.append('<article style="max-width:860px;margin:40px auto;padding:0 20px">')
    parts.append('<a href="../crypto.html" style="color:var(--red);font-size:12px;font-weight:700;text-transform:uppercase;text-decoration:none">Crypto</a>')
    parts.append('<h1 style="font-size:32px;font-weight:800;margin:12px 0 8px">Weekly Crypto Digest — ' + date_human + '</h1>')
    parts.append('<p style="color:#888;font-size:13px;margin-bottom:28px">By Markets News Today AI &middot; ' + date_human + ' &middot; 3 min read</p>')
    parts.append('<div style="font-size:17px;line-height:1.9;color:#333">' + text + '</div>')
    parts.append('<p style="font-size:11px;color:#bbb;margin-top:32px;font-style:italic">AI-generated for informational purposes only. Not financial advice.</p>')
    parts.append('</article></body></html>')

    digest_path.write_text("\n".join(parts), encoding="utf-8")

    # Add to posts_index
    pi_path = OUTPUT_DIR / "posts_index.json"
    pi = json.loads(pi_path.read_text()) if pi_path.exists() else []
    if digest_slug not in {p["slug"] for p in pi}:
        pi.insert(0, {
            "slug": digest_slug,
            "title": "Weekly Crypto Digest — " + date_human,
            "meta_description": "Weekly crypto market digest for " + date_human + ".",
            "excerpt": text[:200] + "...",
            "category": "Crypto", "coin_tag": "",
            "tags": ["crypto","weekly","digest"],
            "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&q=80",
            "read_time": "3 min read",
            "author_name": "Markets News Today AI", "author_title": "AI Market Analyst",
            "author_avatar": "https://i.pravatar.cc/150?img=33", "author_id": "dr-james-wu",
            "date_iso": date_iso, "date_human": date_human,
        })
        pi_path.write_text(json.dumps(pi, indent=2))
        print("  Weekly digest saved!")

# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "posts").mkdir(exist_ok=True)

    print("Fetching live coin data...")
    coin_data = fetch_coins()

    print("Loading posts index...")
    posts_index = []
    pi_path = OUTPUT_DIR / "posts_index.json"
    if pi_path.exists():
        try:
            posts_index = json.loads(pi_path.read_text())
        except:
            pass

    print("Generating " + str(len(COINS)) + " coin pages...")
    for coin in COINS:
        arts = get_articles(coin["tag"], posts_index)
        html = build_coin_page(coin, coin_data, arts)
        out  = OUTPUT_DIR / (coin["slug"] + ".html")
        out.write_text(html, encoding="utf-8")
        d = coin_data.get(coin["sym"], {})
        print("  OK " + coin["name"] + " — " + fmt_price(d.get("price",0)) + " " + fmt_chg(d.get("change24h",0)) + " — " + str(len(arts)) + " articles")

    build_weekly_digest(coin_data, posts_index)
    print("Done!")

if __name__ == "__main__":
    main()
