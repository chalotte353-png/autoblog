"""
ONE-TIME SCRIPT — Purani saari posts mein internal links inject karo.
Run: python inject_links_old_posts.py
Output folder: output/ (same as site)
"""
import json, re, os
from pathlib import Path
from bs4 import BeautifulSoup

SITE_URL = "https://marketsnewstoday.info"
OUTPUT_DIR = Path("output")
POSTS_DIR = OUTPUT_DIR / "posts"
MAX_LINKS = 3

STOP = {"a","an","the","in","on","at","of","and","for","to","is","are","was",
        "were","it","its","as","by","with","from","that","this","has","have",
        "after","over","into","about","up","out","than","but","be","been",
        "their","his","her","our","us","new","says","will","can","could",
        "would","should","may","might","also","just","more","most","one",
        "two","or","not","all","who","which","what","when","where","how"}

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def inject_links(article_html, current_slug, all_posts):
    soup = BeautifulSoup(article_html, 'html.parser')
    current_cat = next((p.get("category","") for p in all_posts if p["slug"] == current_slug), "")
    candidates = [p for p in all_posts if p["slug"] != current_slug]
    candidates = sorted(candidates, key=lambda p: (0 if p.get("category") == current_cat else 1))

    injected = 0
    used_slugs = set()

    for post in candidates:
        if injected >= MAX_LINKS:
            break
        if post["slug"] in used_slugs:
            continue

        title_words = [w for w in re.sub(r'[^a-zA-Z0-9 ]', '', post["title"]).split()
                      if w.lower() not in STOP and len(w) > 3]
        if len(title_words) < 2:
            continue

        phrases = []
        if len(title_words) >= 3:
            phrases.append(" ".join(title_words[:3]))
        if len(title_words) >= 2:
            phrases.append(" ".join(title_words[:2]))

        link_url = f"{SITE_URL}/posts/{post['slug']}.html"
        linked = False

        for phrase in phrases:
            if linked:
                break
            for tag in soup.find_all(['p', 'h2', 'h3']):
                if tag.find('a'):
                    continue
                tag_text = tag.get_text()
                match = re.search(re.escape(phrase), tag_text, re.IGNORECASE)
                if match:
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
                        linked = True
                        break

    return str(soup), injected

def main():
    # Load posts index
    index_file = OUTPUT_DIR / "posts_index.json"
    if not index_file.exists():
        print("❌ posts_index.json not found!")
        return

    all_posts = json.loads(index_file.read_text())
    print(f"Total posts: {len(all_posts)}")

    total_fixed = 0
    total_links = 0
    skipped = 0

    for post in all_posts:
        slug = post["slug"]
        post_file = POSTS_DIR / f"{slug}.html"

        if not post_file.exists():
            skipped += 1
            continue

        content = post_file.read_text(encoding="utf-8")

        # Find post-body content
        body_match = re.search(
            r'<div class="post-body">(.*?)</div>\s*(?:<div class="post-related"|<div class="post-tags")',
            content, re.DOTALL
        )
        if not body_match:
            skipped += 1
            continue

        # Check if already has internal links in body
        body_html = body_match.group(1)
        existing_links = len(re.findall(r'href="[^"]*posts/[^"]*"', body_html))
        if existing_links >= 2:
            # Already has enough links
            skipped += 1
            continue

        # Inject links
        new_body, links_added = inject_links(body_html, slug, all_posts)

        if links_added > 0:
            # Replace body in full HTML
            new_content = content.replace(
                f'<div class="post-body">{body_html}</div>',
                f'<div class="post-body">{new_body}</div>',
                1
            )
            post_file.write_text(new_content, encoding="utf-8")
            total_fixed += 1
            total_links += links_added
            print(f"  ✅ {slug[:60]} — {links_added} links added")

    print(f"\n{'='*50}")
    print(f"✅ Done!")
    print(f"   Posts updated: {total_fixed}")
    print(f"   Total links injected: {total_links}")
    print(f"   Skipped (no match/already linked): {skipped}")

if __name__ == "__main__":
    main()
