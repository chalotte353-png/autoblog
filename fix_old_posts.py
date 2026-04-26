"""
Fix old posts:
1. Remove cross-category links
2. Replace with same-category links where possible
3. Rewrite forced/twisted paragraphs via Claude

Place in autoblog-main/ root and run via GitHub Actions.
"""
import os, re, json, time, requests
from pathlib import Path
from bs4 import BeautifulSoup

SITE_URL = os.environ.get("SITE_URL", "https://marketsnewstoday.info")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
OUTPUT_DIR = Path("output")
POSTS_DIR = OUTPUT_DIR / "posts"

# Phrases that signal a paragraph was twisted to force a link
FORCED_SIGNALS = [
    'as seen when', 'much like how', 'similar to how', 'just as',
    'parallels to broader', 'even amid the noise', 'from the',
    'rattled by geopolit', 'rocked by supply', 'financial markets have been',
    'global uncertainty has created', 'broader patterns of volatility',
    'energy markets have been', 'supply disruptions', 'drawn parallels to'
]

STOP = {"a","an","the","in","on","at","of","and","for","to","is","are","was",
        "were","it","its","as","by","with","from","that","this","has","have",
        "after","over","into","about","up","out","than","but","be","been",
        "their","his","her","our","us","new","says","will","can","could",
        "would","should","may","might","also","just","more","most","one",
        "two","or","not","all","who","which","what","when","where","how","said"}

def load_index():
    return json.loads((OUTPUT_DIR / "posts_index.json").read_text())

def get_cat_map(posts_index):
    return {p['slug']: p.get('category', '') for p in posts_index}

def find_same_category_link(phrase, current_slug, current_cat, cat_map, all_slugs):
    """Find a same-category post that matches this phrase."""
    for slug in all_slugs:
        if slug == current_slug:
            continue
        if cat_map.get(slug, '') != current_cat:
            continue
        slug_words = set(re.sub(r'[^a-zA-Z0-9 ]', '', slug.replace('-', ' ')).lower().split())
        phrase_words = set(phrase.lower().split()) - STOP
        if phrase_words and phrase_words.issubset(slug_words):
            return slug
    return None

def rewrite_forced_paragraph(paragraph_text, category, article_title):
    """Rewrite forced paragraph via Claude — stay on topic."""
    if not CLAUDE_API_KEY:
        return None
    prompt = f"""This paragraph is from a {category} news article titled "{article_title}".
It was artificially modified to mention unrelated news stories (like wars, shootings, financial crashes) just to include links. 

Rewrite this paragraph so it:
- Stays strictly on the {category} topic
- Removes ALL references to unrelated events
- Flows naturally without any forced comparisons
- Keeps same approximate length
- Returns ONLY the rewritten paragraph — no explanation, no HTML tags

Original paragraph:
{paragraph_text}"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        resp = r.json()
        if "content" in resp:
            return resp["content"][0]["text"].strip()
    except Exception as e:
        print(f"    Claude error: {e}")
    return None

def fix_post(content, slug, current_cat, cat_map, all_slugs, article_title):
    body_match = re.search(
        r'(<div class="post-body">)(.*?)(</div>\s*<div class="post-related")',
        content, re.DOTALL
    )
    if not body_match:
        return content, 0, 0, 0

    prefix = body_match.group(1)
    body_html = body_match.group(2)
    suffix = body_match.group(3)

    soup = BeautifulSoup(body_html, 'html.parser')
    links_removed = 0
    links_replaced = 0
    paragraphs_fixed = 0

    for tag in soup.find_all(['p', 'h2', 'h3']):
        tag_text = tag.get_text()
        links_in_tag = tag.find_all('a', href=True)

        # Find cross-category links in this tag
        cross_links = []
        for a in links_in_tag:
            href = a.get('href', '')
            if 'posts/' not in href:
                continue
            linked_slug = href.split('posts/')[-1].replace('.html', '')
            linked_cat = cat_map.get(linked_slug, '')
            if linked_cat and linked_cat != current_cat:
                cross_links.append(a)

        if not cross_links:
            continue

        # Check if paragraph is forced/twisted
        tag_lower = tag_text.lower()
        is_forced = any(signal in tag_lower for signal in FORCED_SIGNALS)

        # Remove cross-category links
        for a in cross_links:
            link_text = a.get_text()
            # Try to find same-category replacement
            title_words = [w for w in re.sub(r'[^a-zA-Z0-9 ]','',link_text).split()
                          if w.lower() not in STOP and len(w) > 4]
            replacement_slug = None
            if len(title_words) >= 2:
                phrase = title_words[0] + " " + title_words[1]
                replacement_slug = find_same_category_link(phrase, slug, current_cat, cat_map, all_slugs)

            if replacement_slug:
                # Replace with same-category link
                new_href = f"{SITE_URL}/posts/{replacement_slug}.html"
                a['href'] = new_href
                # Get a clean title from slug
                new_title = replacement_slug.replace('-', ' ').title()
                a['title'] = new_title
                links_replaced += 1
            else:
                # Just remove the link, keep text
                a.unwrap()
                links_removed += 1

        # Rewrite if paragraph is forced/twisted
        if is_forced and CLAUDE_API_KEY and len(tag_text.strip()) > 60:
            rewritten = rewrite_forced_paragraph(tag_text, current_cat, article_title)
            if rewritten and rewritten.strip() != tag_text.strip():
                new_tag = BeautifulSoup(f'<{tag.name}>{rewritten}</{tag.name}>', 'html.parser').find(tag.name)
                if new_tag:
                    tag.replace_with(new_tag)
                    paragraphs_fixed += 1
                    time.sleep(0.8)

    new_body = str(soup)
    new_content = content[:body_match.start()] + prefix + new_body + suffix + content[body_match.end():]
    return new_content, links_removed, links_replaced, paragraphs_fixed

def main():
    if not CLAUDE_API_KEY:
        print("⚠️  CLAUDE_API_KEY not set — links will be fixed but paragraphs NOT rewritten")
    
    posts_index = load_index()
    cat_map = get_cat_map(posts_index)
    all_slugs = list(cat_map.keys())
    # Build title map for context
    title_map = {p['slug']: p.get('title', '') for p in posts_index}

    print(f"Loaded {len(posts_index)} posts")

    total_files = 0
    total_links_removed = 0
    total_links_replaced = 0
    total_paragraphs = 0

    for fname in sorted(os.listdir(POSTS_DIR)):
        if not fname.endswith('.html'):
            continue

        slug = fname.replace('.html', '')
        current_cat = cat_map.get(slug, '')
        if not current_cat:
            continue

        fpath = POSTS_DIR / fname
        try:
            content = fpath.read_text(encoding='utf-8')
        except Exception:
            continue

        # Quick check for cross-category links
        body_match = re.search(r'class="post-body">(.*?)</div>\s*<div class="post-related"', content, re.DOTALL)
        if not body_match:
            continue
        
        soup_check = BeautifulSoup(body_match.group(1), 'html.parser')
        has_cross = False
        for a in soup_check.find_all('a', href=True):
            linked_slug = a['href'].split('posts/')[-1].replace('.html','')
            linked_cat = cat_map.get(linked_slug, '')
            if linked_cat and linked_cat != current_cat:
                has_cross = True
                break

        if not has_cross:
            continue

        article_title = title_map.get(slug, slug)
        print(f"\nFixing [{current_cat}]: {slug[:55]}")

        new_content, removed, replaced, fixed = fix_post(
            content, slug, current_cat, cat_map, all_slugs, article_title
        )

        if removed + replaced + fixed > 0:
            fpath.write_text(new_content, encoding='utf-8')
            total_files += 1
            total_links_removed += removed
            total_links_replaced += replaced
            total_paragraphs += fixed
            print(f"  ✅ Links removed: {removed} | Replaced with same-cat: {replaced} | Paragraphs rewritten: {fixed}")

    print()
    print("=" * 55)
    print(f"✅ DONE!")
    print(f"   Posts fixed: {total_files}")
    print(f"   Cross-links removed: {total_links_removed}")
    print(f"   Replaced with same-category links: {total_links_replaced}")
    print(f"   Forced paragraphs rewritten: {total_paragraphs}")
    print()
    print("Next: cPanel → Git Version Control → Deploy HEAD Commit")

if __name__ == "__main__":
    main()
