#!/usr/bin/env python3
"""
Fix script: Add real Wikipedia images to all net worth profile pages.
Run from repo root: python fix_networth_images.py
"""
import json, os, requests, time, re, sys
from pathlib import Path
from urllib.parse import quote

NETWORTH_JSON = Path("output/networth_index.json")
NETWORTH_DIR  = Path("output/networth")
SITE_URL      = os.environ.get("SITE_URL", "https://marketsnewstoday.info")
SITE_NAME     = os.environ.get("SITE_NAME", "Markets News Today")


def fetch_wiki_image(name: str, real_name: str = "") -> str:
    """Try to get a real Wikipedia photo for the person."""
    search_names = []
    if real_name and real_name.lower() != name.lower():
        search_names.append(real_name)
    search_names.append(name)

    for search_name in search_names:
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{search_name.replace(' ', '_')}"
            r = requests.get(url, timeout=10, headers={"User-Agent": "AutoBlogBot/1.0"})
            if r.status_code == 200:
                data = r.json()
                img_url = data.get("thumbnail", {}).get("source", "")
                if img_url:
                    img_url = re.sub(r"/(\d+)px-", "/400px-", img_url)
                    return img_url
        except Exception:
            pass
        try:
            params = {"action": "query", "titles": search_name,
                      "prop": "pageimages", "pithumbsize": 400,
                      "format": "json", "redirects": 1}
            r = requests.get("https://en.wikipedia.org/w/api.php", params=params,
                             timeout=10, headers={"User-Agent": "AutoBlogBot/1.0"})
            if r.status_code == 200:
                pages = r.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    src = page.get("thumbnail", {}).get("source", "")
                    if src:
                        return src
        except Exception:
            pass
        time.sleep(0.5)
    return ""


def avatar_url(name: str) -> str:
    return f"https://ui-avatars.com/api/?name={quote(name)}&size=400&background=1a1a2e&color=fff&bold=true&font-size=0.4"


def get_real_name_map():
    import ast
    try:
        content = Path("generate_networth.py").read_text()
        start = content.index('CELEBRITIES = [')
        i = start + len('CELEBRITIES = ')
        depth = 0
        for j, c in enumerate(content[i:], i):
            if c == '[': depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    end = j+1
                    break
        celebs = ast.literal_eval(content[i:end])
        def slugify(s):
            s = s.lower().strip()
            s = re.sub(r'[^\w\s-]', '', s)
            s = re.sub(r'[-\s]+', '-', s)
            return s.strip('-')
        return {slugify(c['name']): c.get('real_name', c['name']) for c in celebs}
    except Exception:
        return {}


def patch_profile_html(html_path: Path, image_url: str, name: str) -> bool:
    """Add image to profile HTML if it's using old hero template (no image)."""
    content = html_path.read_text()

    # Check if already has the new template with image
    if 'nw-profile-hero-bg' in content:
        # Already new template - just update the image URL if it's picsum
        if 'picsum.photos' in content and image_url and 'picsum.photos' not in image_url:
            content = re.sub(
                r"https://picsum\.photos/seed/\d+/\d+/\d+",
                image_url, content
            )
            html_path.write_text(content)
            return True
        return False

    # Old template: has <div class="nw-hero"> without image
    # Inject image into the hero background + add profile img
    old_hero_pattern = r'<div class="nw-hero">\s*<div class="container">\s*<div>'
    new_hero = f'''<div class="nw-hero" style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);position:relative;overflow:hidden">
  <div style="position:absolute;inset:0;background-image:url('{image_url}');background-size:cover;background-position:center;opacity:0.18;filter:blur(4px)"></div>
  <div class="container" style="position:relative;z-index:2;display:flex;align-items:center;gap:28px;padding:32px 20px">
    <img src="{image_url}" alt="{name}" 
         style="width:160px;height:160px;border-radius:50%;object-fit:cover;border:4px solid rgba(255,255,255,0.3);flex-shrink:0;box-shadow:0 8px 32px rgba(0,0,0,0.4)"
         onerror="this.src='https://ui-avatars.com/api/?name={quote(name)}&size=200&background=1a1a1a&color=fff&bold=true'">
    <div>'''

    if re.search(old_hero_pattern, content):
        content = re.sub(old_hero_pattern, new_hero, content, count=1)
        # Also add OG image meta if missing
        if '<meta property="og:image"' not in content and image_url:
            content = content.replace(
                '<meta name="robots"',
                f'<meta property="og:image" content="{image_url}">\n<meta name="robots"',
                1
            )
        html_path.write_text(content)
        return True
    return False


def rebuild_index_html(profiles: list):
    """Rebuild networth/index.html with image cards."""
    from datetime import datetime
    year = datetime.now().year
    categories = sorted(set(p["category"] for p in profiles))

    # Card CSS
    card_css = """
<style>
.nw-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:20px;padding:24px 0}
.nw-card{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.08);transition:transform .2s,box-shadow .2s;display:flex;flex-direction:column;text-decoration:none;color:inherit}
.nw-card:hover{transform:translateY(-4px);box-shadow:0 8px 28px rgba(0,0,0,.14)}
.nw-card-img{width:100%;height:200px;object-fit:cover;object-position:top center;background:#f0f0f0}
.nw-card-body{padding:14px;flex:1;display:flex;flex-direction:column}
.nw-card-cat{font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:#888;margin-bottom:4px}
.nw-card-name{font-size:1.05rem;font-weight:700;color:#1a1a2e;margin-bottom:6px;line-height:1.3}
.nw-card:hover .nw-card-name{color:#0052cc}
.nw-card-worth{font-size:1.1rem;font-weight:800;color:#0052cc}
.nw-card-meta{font-size:11px;color:#aaa;margin-top:4px}
.nw-filter{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.nw-filter-btn{padding:6px 14px;border:1px solid #ddd;border-radius:20px;background:#fff;cursor:pointer;font-size:.82rem;transition:.2s}
.nw-filter-btn.active,.nw-filter-btn:hover{background:#0052cc;color:#fff;border-color:#0052cc}
.nw-count{color:#888;font-size:.85rem;margin-bottom:8px}
</style>"""

    # Build cards HTML
    cards_html = ""
    for p in sorted(profiles, key=lambda x: x["name"]):
        img = p.get("image_url") or avatar_url(p["name"])
        name_enc = quote(p["name"])
        cat_slug = p["category"].lower().replace(" ", "-")
        cards_html += f"""
      <a href="{p['slug']}.html" class="nw-card" data-cat="{cat_slug}">
        <img src="{img}" alt="{p['name']}" class="nw-card-img" loading="lazy"
             onerror="this.src='https://ui-avatars.com/api/?name={name_enc}&size=300&background=1a1a2e&color=fff&bold=true'">
        <div class="nw-card-body">
          <div class="nw-card-cat">{p['category']}</div>
          <div class="nw-card-name">{p['name']}</div>
          <div class="nw-card-worth">{p.get('estimated_net_worth','N/A')}</div>
          <div class="nw-card-meta">{p.get('nationality','')}</div>
        </div>
      </a>"""

    filter_btns = '<button class="nw-filter-btn active" onclick="filter(\'all\',this)">All</button>'
    for cat in categories:
        cat_slug = cat.lower().replace(" ", "-")
        filter_btns += f'<button class="nw-filter-btn" onclick="filter(\'{cat_slug}\',this)">{cat}</button>'

    # Read existing index.html to preserve nav/footer structure
    index_path = NETWORTH_DIR / "index.html"
    if index_path.exists():
        existing = index_path.read_text()
        # Extract nav
        nav_match = re.search(r'(<nav.*?</nav>)', existing, re.DOTALL)
        nav_html = nav_match.group(1) if nav_match else ""
        # Extract footer
        foot_match = re.search(r'(<footer.*?</footer>)', existing, re.DOTALL)
        foot_html = foot_match.group(1) if foot_match else ""
        # Extract head (for CSS etc)
        head_match = re.search(r'(<head>.*?</head>)', existing, re.DOTALL)
        head_html = head_match.group(1) if head_match else "<head><meta charset='UTF-8'><title>Net Worth</title><link rel='stylesheet' href='../style.css'></head>"
    else:
        nav_html = ""
        foot_html = ""
        head_html = "<head><meta charset='UTF-8'><title>Net Worth</title><link rel='stylesheet' href='../style.css'></head>"

    # Remove old style blocks from head to avoid conflicts
    head_html = re.sub(r'<style>.*?</style>', '', head_html, flags=re.DOTALL)

    html = f"""<!DOCTYPE html>
<html lang="en">
{head_html}
{card_css}
<body>
{nav_html}

<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:40px 0 30px;text-align:center;margin-bottom:8px">
  <div class="container">
    <h1 style="font-size:clamp(1.6rem,4vw,2.4rem);font-weight:800;margin-bottom:8px">Celebrity Net Worth</h1>
    <p style="color:#aab4c8;margin:0">Estimated net worth of {len(profiles)} celebrities, influencers &amp; creators</p>
  </div>
</div>

<div style="background:#f8f9fa;min-height:60vh">
  <div class="container" style="padding-top:24px">
    <div class="nw-filter" id="filters">
      {filter_btns}
    </div>
    <div class="nw-count" id="count">Showing {len(profiles)} profiles</div>
    <div class="nw-grid" id="grid">
      {cards_html}
    </div>
  </div>
</div>

{foot_html}

<script>
function filter(cat, btn) {{
  document.querySelectorAll('.nw-filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  let count = 0;
  document.querySelectorAll('.nw-card').forEach(card => {{
    const show = cat === 'all' || card.dataset.cat === cat;
    card.style.display = show ? 'flex' : 'none';
    if (show) count++;
  }});
  document.getElementById('count').textContent = 'Showing ' + count + ' profiles';
}}
</script>
</body>
</html>"""

    index_path.write_text(html)
    print(f"✅ Rebuilt {index_path} with image cards")


def main():
    print("🔍 Loading profiles from networth_index.json...")
    profiles = json.loads(NETWORTH_JSON.read_text())
    real_name_map = get_real_name_map()
    updated_json = 0
    updated_html = 0

    for p in profiles:
        slug = p["slug"]
        name = p["name"]
        real_name = real_name_map.get(slug, name)

        # Check if image is missing or is a random picsum image
        current_img = p.get("image_url", "")
        needs_image = not current_img or "picsum.photos" in current_img

        if needs_image:
            print(f"  🔍 Fetching image for {name}...")
            img = fetch_wiki_image(name, real_name)
            if not img:
                img = avatar_url(name)
                print(f"    ⚠️  No Wikipedia image → using avatar")
            else:
                print(f"    ✅ Got: {img[:70]}...")
            p["image_url"] = img
            updated_json += 1
            time.sleep(1)
        else:
            img = current_img

        # Patch existing profile HTML
        html_path = NETWORTH_DIR / f"{slug}.html"
        if html_path.exists():
            if patch_profile_html(html_path, img, name):
                updated_html += 1
                print(f"    📝 Patched {slug}.html with image")

    # Save updated JSON
    NETWORTH_JSON.write_text(json.dumps(profiles, indent=2, ensure_ascii=False))
    print(f"\n✅ Updated {updated_json} entries in networth_index.json")
    print(f"✅ Patched {updated_html} profile HTML files")

    # Rebuild index.html
    print("\n📋 Rebuilding networth/index.html with image cards...")
    rebuild_index_html(profiles)
    print("\n🎉 Done! Commit and push the output/ folder.")


if __name__ == "__main__":
    main()
